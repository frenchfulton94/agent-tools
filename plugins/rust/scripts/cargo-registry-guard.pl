#!/usr/bin/perl
#
# cargo-registry-guard.pl -- PreToolUse guard for the cargo commands that change a registry.
#
# Everything else cargo does is local and undoable: a build, a test, an edit to
# Cargo.toml, an update to Cargo.lock. Three subcommands reach out and change what
# other people see, and none of them asks first:
#
#   ask -- `cargo publish` without --dry-run. The Cargo Book: a publish is
#          permanent, the version can never be overwritten, and the code cannot be
#          deleted. Only a yank follows, and a yank hides a version from new
#          resolution without removing it. cargo prints no confirmation, so without
#          this hook the upload happens the moment the Bash call runs.
#       -- `cargo yank`, with or without --undo. Reversible, but it changes what
#          every downstream project without a lockfile entry resolves to.
#       -- `cargo owner --add/--remove`. Changes who can publish the crate.
#   allow -- everything else, silently, including `cargo publish --dry-run`,
#          `cargo package`, and `cargo owner --list`. A guard that fires on safe
#          operations gets switched off, and then it protects nothing.
#
# There is no deny. Each of these is the right command when the user means it, so
# the decision goes to a human rather than to this script.
#
# The subcommand is found the way cargo finds it: after `+toolchain` and global
# options (`--config`, `-Z`, `--color` take a value), and through aliases. An alias
# is read from the `[alias]` table of every `.cargo/config.toml` (or `.cargo/config`)
# from the working directory up to the root, from `$CARGO_HOME/config.toml`, and from
# `CARGO_ALIAS_<NAME>`. cargo ignores an
# alias that shadows a built-in command, and so does this script. An alias passed
# as `--config alias.NAME=...` is not honoured by cargo (measured on 1.97.1: "no
# such command"), so it is not modelled here.
#
# Known, accepted limits:
#   - A publish run by a script file, a Makefile, a `just` recipe, or a third-party
#     release tool (cargo-release, cargo-workspaces, release-plz) is not seen.
#   - Variables and command substitutions are not evaluated; a subcommand hidden in
#     one (`cargo $CMD`) is allowed.
#   - Fails open. A malformed payload, or any internal error, allows the call.
#     RUST_GUARD_DEBUG=1 prints the error to stderr, which the test suite asserts
#     never happens.
#
# Perl, core modules only: present on macOS and on effectively every Linux that has
# git, and it parses JSON without jq.

use strict;
use warnings;
use JSON::PP ();
use Cwd ();

my $TAG       = '[rust]';
my $MAX_DEPTH = 4;    # nesting limit for `bash -c`, `eval`, and alias expansion

# Words that mean "the real command follows".
my %WRAPPER = map { $_ => 1 } qw(sudo env command builtin exec nice nohup time do then else ! { xargs);

# cargo's global options that consume the next word (when not written as --opt=value).
my %GLOBAL_WITH_VALUE = map { $_ => 1 } qw(--color --config -Z -C --explain);

# Built-in subcommands and their built-in aliases. A user alias with one of these
# names is ignored by cargo.
my %BUILTIN = map { $_ => 1 } qw(
    add b bench build c check clean clippy config d doc fetch fix fmt generate-lockfile
    help info init install locate-project login logout metadata miri new owner package
    pkgid publish r read-manifest remove report rm run rustc rustdoc search t test tree
    uninstall update vendor verify-project version yank
);

exit main();

sub main {
    my $out = eval { run() };
    if ($@) {
        print STDERR "$TAG internal error: $@" if $ENV{RUST_GUARD_DEBUG};
        return 0;
    }
    print $out if $out;
    return 0;
}

sub run {
    my $raw = do { local $/; <STDIN> };
    return '' unless defined $raw && length $raw;
    my $payload = eval { JSON::PP->new->decode($raw) };
    return '' unless ref $payload eq 'HASH';
    return '' unless ($payload->{tool_name} // '') eq 'Bash';
    my $command = ref $payload->{tool_input} eq 'HASH' ? ($payload->{tool_input}{command} // '') : '';
    return '' unless $command =~ /\bcargo\b/;

    my $cwd = $payload->{cwd};
    $cwd = Cwd::getcwd() unless defined $cwd && length $cwd;

    my $ctx = { cwd => $cwd, verdicts => [] };
    analyse($ctx, $command, 0);

    my ($pick) = @{ $ctx->{verdicts} };
    return '' unless $pick;
    return JSON::PP->new->canonical->encode({
        hookSpecificOutput => {
            hookEventName            => 'PreToolUse',
            permissionDecision       => 'ask',
            permissionDecisionReason => "$TAG $pick",
        },
    }) . "\n";
}

sub verdict { push @{ $_[0]{verdicts} }, $_[1] }

sub analyse {
    my ($ctx, $command, $depth) = @_;
    return if $depth > $MAX_DEPTH;
    statement($ctx, $_, $depth) for @{ tokenize($command) };
}

sub basename_of { my ($t) = @_; $t =~ s{.*/}{}; $t =~ s/\.exe$//i; return $t }

sub statement {
    my ($ctx, $words, $depth) = @_;
    my @w = @$words;
    my %env;

    while (@w) {
        if ($w[0] =~ /^([A-Za-z_]\w*)=(.*)$/s) { $env{$1} = $2; shift @w; next }
        my $b = basename_of($w[0]);
        last unless $WRAPPER{$b};
        shift @w;
        if ($b eq 'sudo') {
            while (@w && $w[0] =~ /^-/) {
                my $opt = shift @w;
                last if $opt eq '--';
                shift @w if $opt =~ /^-[ugpChDRrT]$/ && @w;
            }
        } elsif ($b eq 'env') {
            while (@w && $w[0] =~ /^-/) {
                my $opt = shift @w;
                shift @w if $opt =~ /^-[uPSC]$/ && @w;
            }
        } elsif ($b eq 'nice') {
            if (@w && $w[0] eq '-n') { splice(@w, 0, 2) }
            elsif (@w && $w[0] =~ /^-\d+$/) { shift @w }
        } elsif ($b eq 'xargs') {
            while (@w && $w[0] =~ /^-/) {
                my $opt = shift @w;
                shift @w if $opt =~ /^-[nLIPsdEa]$/ && @w;
            }
        } elsif ($b eq 'time' || $b eq 'command') {
            shift @w while @w && $w[0] =~ /^-/;
        }
    }
    return unless @w;

    my $cmd  = basename_of($w[0]);
    my @args = @w[1 .. $#w];

    if ($cmd eq 'cd' || $cmd eq 'pushd') {
        my $to = @args ? $args[0] : ($ENV{HOME} // '/');
        $ctx->{cwd} = ($to eq '-' || $to =~ /\$/) ? undef : absolute($to, $ctx->{cwd});
        return;
    }
    if ($cmd =~ /^(?:ba|z|da|k)?sh$/) {
        for my $k (0 .. $#args - 1) {
            if ($args[$k] =~ /^-\w*c\w*$/) { nested($ctx, $args[$k + 1], $depth); return }
        }
        return;
    }
    if ($cmd eq 'eval') { nested($ctx, join(' ', @args), $depth); return }
    if ($cmd =~ /^cargo-(publish|yank|owner)$/) { return subcommand($ctx, $1, \@args) }
    return unless $cmd eq 'cargo';

    cargo($ctx, \@args, \%env, $depth);
}

sub nested {
    my ($ctx, $text, $depth) = @_;
    my $saved = $ctx->{cwd};
    analyse($ctx, $text, $depth + 1);
    $ctx->{cwd} = $saved;
}

# `cargo [+toolchain] [global options] SUBCOMMAND [args]`
sub cargo {
    my ($ctx, $args, $env, $depth) = @_;
    my @a = @$args;
    shift @a if @a && $a[0] =~ /^\+/;
    while (@a && $a[0] =~ /^-/) {
        my $opt = shift @a;
        shift @a if $GLOBAL_WITH_VALUE{$opt} && @a;
    }
    return unless @a;
    my $sub  = shift @a;
    my $seen = 0;
    while (!$BUILTIN{$sub}) {
        return if ++$seen > $MAX_DEPTH;
        my $expansion = env_alias($sub, $env) // config_alias($ctx, $sub);
        return unless $expansion && @$expansion;
        unshift @a, @$expansion[1 .. $#$expansion];
        $sub = $expansion->[0];
        if ($sub =~ /^\+|^-/) {    # an alias may itself carry global options
            return cargo($ctx, [$sub, @a], $env, $depth + 1);
        }
    }
    subcommand($ctx, $sub, \@a);
}

sub subcommand {
    my ($ctx, $sub, $args) = @_;
    my @a = @$args;
    return if grep { $_ eq '--help' || $_ eq '-h' } @a;

    if ($sub eq 'publish') {
        return if grep { $_ eq '--dry-run' || /^-[vq]*n[vqn]*$/ } @a;
        my $where = registry(\@a);
        my $what  = (grep { $_ eq '--workspace' || $_ eq '--all' } @a)
            ? 'every publishable package in the workspace'
            : 'this package';
        return verdict($ctx,
            "This uploads $what to $where. A published version is permanent: it can never be "
          . 'overwritten and its code cannot be deleted. A yank only hides it from new dependency '
          . 'resolution. Run `cargo publish --dry-run` first, check the version and the packaged '
          . 'file list (`cargo package --list`), and confirm the user wants this release now.');
    }
    if ($sub eq 'yank') {
        my $undo = grep { $_ eq '--undo' } @a;
        return verdict($ctx, $undo
            ? 'This un-yanks a version on ' . registry(\@a) . ', making it resolvable again for '
              . 'every project that depends on the crate. Confirm the version was not yanked for a '
              . 'security or soundness reason.'
            : 'This yanks a version on ' . registry(\@a) . '. Projects with it already in '
              . 'Cargo.lock keep building, but no new resolution will select it, for anyone. '
              . '`cargo yank --undo` reverses it. Confirm the crate and version with the user.');
    }
    if ($sub eq 'owner') {
        my $change = grep { /^(?:--add|--remove)(?:=|$)/ || /^-[vql]*[ar]/ } @a;
        return unless $change;
        return verdict($ctx,
            'This changes who can publish and yank the crate on ' . registry(\@a) . '. An added '
          . 'owner can publish any version; a team owner can publish but not change owners. '
          . 'Confirm the login and the crate with the user.');
    }
}

sub registry {
    my ($a) = @_;
    for my $k (0 .. $#$a) {
        return "the `$1` registry"  if $a->[$k] =~ /^--registry=(.+)$/;
        return "the `$a->[$k+1]` registry" if $a->[$k] eq '--registry' && $k < $#$a;
        return 'the registry at --index' if $a->[$k] =~ /^--index(?:=|$)/;
    }
    return 'crates.io (or the default registry configured for this package)';
}

# --------------------------------------------------------------------------
# Aliases

sub env_alias {
    my ($name, $env) = @_;
    (my $key = 'CARGO_ALIAS_' . uc $name) =~ s/-/_/g;
    my $v = $env->{$key} // $ENV{$key};
    return defined $v ? [split ' ', $v] : undef;
}

sub config_alias {
    my ($ctx, $name) = @_;
    $ctx->{aliases} //= load_aliases($ctx->{cwd});
    return $ctx->{aliases}{$name};
}

# Nearest file wins, as in cargo's config merge for a scalar key.
sub load_aliases {
    my ($cwd) = @_;
    my @files;
    if (defined $cwd) {
        my $dir = $cwd;
        while (1) {
            push @files, "$dir/.cargo/config.toml", "$dir/.cargo/config";
            last if $dir eq '/' || $dir eq '';
            $dir =~ s{/[^/]*$}{};
            $dir = '/' if $dir eq '';
        }
    }
    my $home = $ENV{CARGO_HOME} // (defined $ENV{HOME} ? "$ENV{HOME}/.cargo" : undef);
    push @files, "$home/config.toml", "$home/config" if defined $home;

    my %alias;
    for my $f (reverse @files) {    # farthest first, so nearer files overwrite
        next unless -f $f;
        open(my $fh, '<', $f) or next;
        my $section = '';
        while (my $line = <$fh>) {
            $line =~ s/^\s+|\s+$//g;
            next if $line eq '' || $line =~ /^#/;
            if ($line =~ /^\[\s*([^\]]+?)\s*\]$/) { $section = $1; next }
            my ($k, $v);
            if ($section eq 'alias' && $line =~ /^"?([\w-]+)"?\s*=\s*(.+)$/) { ($k, $v) = ($1, $2) }
            elsif ($section eq '' && $line =~ /^alias\.([\w-]+)\s*=\s*(.+)$/) { ($k, $v) = ($1, $2) }
            next unless defined $k;
            my $parsed = parse_alias_value($v);
            $alias{$k} = $parsed if $parsed;
        }
        close $fh;
    }
    return \%alias;
}

# `"publish --registry x"` or `["publish", "--registry", "x"]`
sub parse_alias_value {
    my ($v) = @_;
    $v =~ s/\s+#.*$//;
    if ($v =~ /^\[(.*)\]$/s) {
        my @items = $1 =~ /"((?:[^"\\]|\\.)*)"|'([^']*)'/g;
        return [grep { defined && length } @items];
    }
    return [split ' ', $1] if $v =~ /^"((?:[^"\\]|\\.)*)"$/ || $v =~ /^'([^']*)'$/;
    return undef;
}

sub absolute {
    my ($p, $cwd) = @_;
    $p = ($ENV{HOME} // '') . $1 if $p =~ m{^~(/.*)?$} && defined $ENV{HOME};
    return undef if $p !~ m{^/} && !defined $cwd;
    $p = "$cwd/$p" unless $p =~ m{^/};
    my @out;
    for my $seg (split m{/+}, $p) {
        next if $seg eq '' || $seg eq '.';
        if ($seg eq '..') { pop @out; next }
        push @out, $seg;
    }
    return '/' . join('/', @out);
}

# --------------------------------------------------------------------------
# Tokenizer
#
# Splits a command line into statements of words, removing quotes. `$(...)` and
# backtick substitutions are analysed as statements of their own, since a
# `cargo publish` inside one runs too. Variables other than $HOME are kept
# literally. An unmatched quote ends tokenizing with what was read so far.

sub tokenize {
    my ($s) = @_;
    my (@stmts, @cur, $w);
    my $flush = sub { if (defined $w) { push @cur, $w; undef $w } };
    my $end   = sub { $flush->(); push @stmts, [@cur] if @cur; @cur = () };

    my $n = length $s;
    my $i = 0;
    while ($i < $n) {
        my $c = substr($s, $i, 1);
        if ($c eq "\n" || $c eq ';' || $c eq '(' || $c eq ')') { $end->(); $i++; next }
        if ($c eq '&' || $c eq '|') {
            $end->();
            $i++;
            $i++ if $i < $n && (substr($s, $i, 1) eq $c || ($c eq '|' && substr($s, $i, 1) eq '&'));
            next;
        }
        if ($c =~ /\s/) { $flush->(); $i++; next }
        if ($c eq '#' && !defined $w) {
            my $nl = index($s, "\n", $i);
            $i = $nl < 0 ? $n : $nl;
            next;
        }
        if ($c eq '<' || $c eq '>') {
            if (defined $w && $w =~ /^\d+$/) { undef $w } else { $flush->() }
            $i++ while $i < $n && substr($s, $i, 1) =~ /[<>&0-9]/;
            $i++ while $i < $n && substr($s, $i, 1) =~ /[ \t]/;
            $i++ while $i < $n && substr($s, $i, 1) !~ /[\s;&|()<>]/;
            next;
        }
        if ($c eq '\\') {
            if ($i + 1 < $n && substr($s, $i + 1, 1) ne "\n") { $w .= substr($s, $i + 1, 1) }
            $i += 2;
            next;
        }
        if ($c eq "'") {
            my $close = index($s, "'", $i + 1);
            last if $close < 0;
            $w .= substr($s, $i + 1, $close - $i - 1);
            $i = $close + 1;
            next;
        }
        if ($c eq '"') {
            $w //= '';
            my $j = $i + 1;
            my $closed = 0;
            while ($j < $n) {
                my $d = substr($s, $j, 1);
                if ($d eq '"') { $closed = 1; last }
                if ($d eq '\\' && $j + 1 < $n && substr($s, $j + 1, 1) =~ /["\\\$`\n]/) {
                    $w .= substr($s, $j + 1, 1);
                    $j += 2;
                    next;
                }
                if ($d eq '$' && substr($s, $j, 2) eq '$(') {
                    my $len = substitution($s, $j + 1, \@stmts);
                    $j += 1 + $len;
                    next;
                }
                if ($d eq '`') {
                    my $close = index($s, '`', $j + 1);
                    push @stmts, @{ tokenize(substr($s, $j + 1, ($close < 0 ? $n : $close) - $j - 1)) };
                    $j = $close < 0 ? $n : $close + 1;
                    next;
                }
                $w .= $d;
                $j++;
            }
            last unless $closed;
            $i = $j + 1;
            next;
        }
        if ($c eq '$' && substr($s, $i, 2) eq '$(') {
            $w //= '';
            $i += 1 + substitution($s, $i + 1, \@stmts);
            next;
        }
        if ($c eq '`') {
            $w //= '';
            my $close = index($s, '`', $i + 1);
            push @stmts, @{ tokenize(substr($s, $i + 1, ($close < 0 ? $n : $close) - $i - 1)) };
            $i = $close < 0 ? $n : $close + 1;
            next;
        }
        if ($c eq '$' && substr($s, $i) =~ /^\$(?:\{HOME\}|HOME\b)/) {
            $w .= $ENV{HOME} // '$HOME';
            $i += length($&);
            next;
        }
        $w .= $c;
        $i++;
    }
    $end->();
    return \@stmts;
}

# $s[$i] is the '(' of a $( ... ); tokenize its body into @$into and return the
# length consumed through the matching ')'.
sub substitution {
    my ($s, $i, $into) = @_;
    my $depth = 0;
    my $k = $i;
    my $n = length $s;
    while ($k < $n) {
        my $ch = substr($s, $k, 1);
        $depth++ if $ch eq '(';
        if ($ch eq ')') { $depth--; if ($depth == 0) { last } }
        $k++;
    }
    push @$into, @{ tokenize(substr($s, $i + 1, $k - $i - 1)) };
    return $k - $i + 1;
}
