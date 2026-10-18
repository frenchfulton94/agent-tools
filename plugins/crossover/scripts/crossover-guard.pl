#!/usr/bin/perl
#
# crossover-guard.pl -- PreToolUse guard against irreversible CrossOver bottle loss.
#
# A bottle holds a Windows installation, the applications installed into it,
# their licences and activations, and every save file and setting those
# applications wrote. CodeWeavers' own KB says removing an application means
# deleting its whole bottle, and that the delete cannot be undone. Nothing
# recovers a bottle except an archive (`cxbottle --tar NAME.cxarchive`, or
# Bottle > Export to Archive) or a filesystem backup.
#
#   deny  -- raw filesystem deletion of a bottle, a bottle folder, a bottle's
#            C: drive or one of its top-level folders, or a registry or
#            cxbottle.conf file. Never the right tool: CrossOver ships
#            `cxbottle --delete`, which also accounts for the bottle's menus
#            and associations, so raw `rm -r` is never the only way.
#   ask   -- `cxbottle --delete`, `cxuninstall`, the CrossOver Removal Tool,
#            `rsync --delete` or `find -delete` aimed into a bottle, and any
#            recursive delete whose target this script cannot resolve on a
#            command that mentions CrossOver. Legitimate when the user wants
#            it, so a human decides.
#   allow -- everything else, silently. A guard that fires on safe operations
#            gets switched off, and then it protects nothing.
#
# Why --delete is "ask" even though cxbottle has its own confirmation: that
# confirmation does not survive a non-interactive shell. Measured on CrossOver
# 25.1.1: `cxbottle --bottle X --delete </dev/null` (no --force) printed
# "cxmessage standin was called." and deleted the bottle, exit 0. Claude's Bash
# tool has no terminal, so without this hook the delete is immediate.
#
# Why Perl: CrossOver's command-line tools (cxbottle, cxstart, wine, ...) are
# themselves `#!/usr/bin/perl` scripts, so Perl exists on every Mac where
# CrossOver's CLI works. python3 does not: without the developer tools,
# /usr/bin/python3 is a stub that opens an install dialog. Core modules only.
#
# Where bottles live -- every location is resolved, because the KB documents
# four ways to move them:
#   ~/Library/Application Support/CrossOver/Bottles      the default
#   /Library/Application Support/CrossOver/Bottles       published bottles
#   BottleDir, ManagedBottleDirs                          com.codeweavers.CrossOver
#                                                         (and ...CrossOverGames)
#   CX_BOTTLE_PATH, BottlePath                            CrossOver.conf, in the app
#                                                         bundle or the user's support
#                                                         folder, and the environment
# A directory under one of those roots counts as a bottle when it holds a
# cxbottle.conf. An empty root protects nothing and the guard stays silent.
#
# Known, accepted limits:
#   - Command substitution and variables other than $HOME are not evaluated.
#     A recursive delete whose target is one of them is "ask" when the command
#     mentions CrossOver, bottles or drive_c, and allowed otherwise.
#   - `mv` is not guarded: a move is reversible.
#   - A delete performed by a script file the command runs is not seen.
#   - `cxbottle --removeall` and `--uninstall` are not guarded: they remove
#     menus and file associations, which `cxbottle --install` re-creates.
#   - Fails open. A malformed payload, or any internal error, allows the call.

use strict;
use warnings;
use JSON::PP ();
use Cwd ();
use File::Glob qw(bsd_glob GLOB_QUOTE GLOB_BRACE);

my $TAG = '[crossover]';
my $MAX_DEPTH = 4;    # nesting limit for `bash -c` / `eval` re-analysis

# Shell words this script treats as "the real command follows".
my %WRAPPER = map { $_ => 1 } qw(sudo env command builtin exec nice nohup time caffeinate do then else ! { );

# Words that make a command worth analysing at all. Anything else is allowed
# before a single file is read, so ordinary Bash calls cost one regex.
my $PREFILTER = qr/\brm\b|\bunlink\b|\bfind\b|\brsync\b|cxbottle|cxuninstall|RemovalTool|\bxargs\b/i;

# Raw-text mentions that make an unresolvable delete worth asking about.
my $MENTIONS = qr/crossover|bottles?\b|drive_c|cxbottle|WINEPREFIX|CX_BOTTLE/i;

# Files whose loss leaves a bottle unusable even though its folder survives.
# Measured on 25.1.1: with system.reg deleted, `wine --bottle X --cx-app cmd.exe`
# exits 1 and the file is not recreated.
my %BOTTLE_FILES = map { $_ => 1 } qw(system.reg user.reg userdef.reg cxbottle.conf);

# find actions that delete.
my %FIND_DELETE_ACTIONS = map { $_ => 1 } qw(-delete -exec -execdir -ok -okdir);

# Every file-scope variable must be above this line: `exit main()` runs before
# anything below it at file scope.

exit main();

sub main {
    my $out = eval { run() };
    if ($@) {    # fail open; CROSSOVER_GUARD_DEBUG=1 surfaces the error for tests
        print STDERR "$TAG internal error: $@" if $ENV{CROSSOVER_GUARD_DEBUG};
        return 0;
    }
    if ($out) { print $out }
    return 0;
}

sub run {
    my $raw = do { local $/; <STDIN> };
    return '' unless defined $raw && length $raw;
    my $payload = eval { JSON::PP->new->decode($raw) };
    return '' unless ref $payload eq 'HASH';
    return '' unless ($payload->{tool_name} // '') eq 'Bash';
    my $command = (ref $payload->{tool_input} eq 'HASH') ? ($payload->{tool_input}{command} // '') : '';
    return '' unless $command =~ /\S/;
    return '' unless $command =~ $PREFILTER;

    my $cwd = $payload->{cwd};
    $cwd = Cwd::getcwd() unless defined $cwd && length $cwd;

    my $ctx = {
        home     => home_dir(),
        cwd      => $cwd,
        raw      => $command,
        verdicts => [],
    };
    $ctx->{bottles} = discover_bottles($ctx->{home});

    analyse($ctx, $command, 0);

    my @v = @{ $ctx->{verdicts} };
    return '' unless @v;
    my ($pick) = grep { $_->[0] eq 'deny' } @v;
    $pick ||= $v[0];
    return JSON::PP->new->canonical->encode({
        hookSpecificOutput => {
            hookEventName            => 'PreToolUse',
            permissionDecision       => $pick->[0],
            permissionDecisionReason => "$TAG $pick->[1]",
        },
    }) . "\n";
}

sub home_dir {
    return $ENV{HOME} if defined $ENV{HOME} && length $ENV{HOME};
    my @pw = getpwuid($<);
    return $pw[7] // '/';
}

# --------------------------------------------------------------------------
# Bottle discovery

sub discover_bottles {
    my ($home) = @_;
    my %roots;
    my $add = sub {
        for my $v (@_) {
            next unless defined $v && length $v;
            my $p = $v;
            $p =~ s/^~(?=\/|$)/$home/;
            $roots{$p} = 1;
        }
    };

    $add->("$home/Library/Application Support/CrossOver/Bottles");
    $add->('/Library/Application Support/CrossOver/Bottles');

    for my $domain ('com.codeweavers.CrossOver', 'com.codeweavers.CrossOverGames') {
        my $plist = "$home/Library/Preferences/$domain.plist";
        next unless -f $plist;
        $add->(plist_strings($plist, 'BottleDir'));
        $add->(map { split /:/ } plist_strings($plist, 'ManagedBottleDirs'));
    }

    $add->(map { expand_conf_value($_, $home) } split /:/, ($ENV{CX_BOTTLE_PATH} // ''));

    my @confs = ("$home/Library/Application Support/CrossOver/CrossOver.conf");
    for my $apps ('/Applications', "$home/Applications") {
        push @confs, map { "$_/Contents/SharedSupport/CrossOver/etc/CrossOver.conf" }
            bsd_glob("$apps/CrossOver*.app");
    }
    for my $conf (@confs) {
        next unless -f $conf;
        $add->(map { expand_conf_value($_, $home) } conf_bottle_paths($conf));
    }

    my @bottles;
    my %seen;
    for my $root (sort keys %roots) {
        next unless -d $root;
        opendir(my $dh, $root) or next;
        for my $entry (readdir $dh) {
            next if $entry eq '.' || $entry eq '..';
            my $b = "$root/$entry";
            next unless -d $b && -f "$b/cxbottle.conf";
            my $key = lc(lexical_abs($b, '/'));
            next if $seen{$key}++;
            push @bottles, { name => $entry, root => $root, path => $b };
        }
        closedir $dh;
    }
    return \@bottles;
}

# String values of one key in a plist, via plutil (binary plists need it).
sub plist_strings {
    my ($file, $key) = @_;
    return () unless -x '/usr/bin/plutil';
    my $xml = '';
    my $pid = open(my $fh, '-|');
    return () unless defined $pid;
    if ($pid == 0) {    # child: a missing key is normal, so keep plutil quiet
        open(STDERR, '>', '/dev/null');
        exec('/usr/bin/plutil', '-extract', $key, 'xml1', '-o', '-', $file) or exit 1;
    }
    {
        local $/;
        $xml = <$fh> // '';
    }
    close $fh;
    my @out;
    while ($xml =~ m{<string>(.*?)</string>}gs) {
        my $s = $1;
        $s =~ s/&lt;/</g; $s =~ s/&gt;/>/g; $s =~ s/&quot;/"/g; $s =~ s/&apos;/'/g; $s =~ s/&amp;/&/g;
        push @out, $s;
    }
    return @out;
}

# "CX_BOTTLE_PATH"="..." and "BottlePath" = "..." lines, comments skipped.
sub conf_bottle_paths {
    my ($file) = @_;
    local $/ = "\n";    # by line, whatever the caller set
    open(my $fh, '<', $file) or return ();
    my @out;
    while (my $line = <$fh>) {
        next if $line =~ /^\s*;/;
        if ($line =~ /^\s*"?(?:CX_BOTTLE_PATH|BottlePath)"?\s*=\s*"([^"]*)"/) {
            push @out, split /:/, $1;
        }
    }
    close $fh;
    return @out;
}

# ${USER}, ${HOME}, ${VAR}, and the KB's own "{USER}" spelling.
sub expand_conf_value {
    my ($v, $home) = @_;
    my $user = $ENV{USER} // (getpwuid($<))[0] // '';
    $v =~ s/\$\{(\w+)\}|\{(USER)\}/
        my $n = defined $1 ? $1 : $2;
        $n eq 'USER' ? $user : $n eq 'HOME' ? $home : ($ENV{$n} \/\/ '')
    /ge;
    return $v;
}

# --------------------------------------------------------------------------
# Paths

# Absolute, with . and .. collapsed lexically. Never touches the disk.
sub lexical_abs {
    my ($p, $cwd) = @_;
    $p = "$cwd/$p" unless $p =~ m{^/};
    my @out;
    for my $part (split m{/+}, $p) {
        next if $part eq '' || $part eq '.';
        if ($part eq '..') { pop @out; next }
        push @out, $part;
    }
    return '/' . join('/', @out);
}

# Every spelling of a path worth comparing: lexical and symlink-resolved,
# case-folded because the default macOS volume is case-insensitive.
sub forms {
    my ($abs) = @_;
    my %f = (lc($abs) => 1);
    my $real = Cwd::realpath($abs);
    $f{ lc($real) } = 1 if defined $real;
    # A symlink's own location matters too: realpath of its parent + its name.
    if ($abs =~ m{^(.*)/([^/]+)$} && length $1) {
        my $pr = Cwd::realpath($1);
        $f{ lc("$pr/$2") } = 1 if defined $pr;
    }
    return keys %f;
}

sub within {    # $a equal to $b, or inside it
    my ($a, $b) = @_;
    return $a eq $b || index($a, $b eq '/' ? '/' : "$b/") == 0;
}

# What deleting $abs recursively would destroy, or undef if nothing guarded.
#   ('bottle', $b)   -- the bottle, an ancestor of it, its C: drive, or a
#                       top-level folder of the C: drive
#   ('inside', $b)   -- somewhere deeper inside a bottle
sub classify_recursive {
    my ($ctx, $abs) = @_;
    my @t = forms($abs);
    my $inside;
    for my $b (@{ $ctx->{bottles} }) {
        my @bf = forms($b->{path});
        for my $t (@t) {
            for my $bp (@bf) {
                return ('bottle', $b) if within($bp, $t);                     # ancestor or equal
                return ('bottle', $b) if $t eq "$bp/drive_c";
                return ('bottle', $b) if $t =~ m{^\Q$bp\E/drive_c/[^/]+$};   # Program Files, users, ...
                $inside ||= $b if within($t, $bp);
            }
        }
    }
    return ('inside', $inside) if $inside;
    return;
}

# A single file whose loss breaks the bottle outright.
sub classify_file {
    my ($ctx, $abs) = @_;
    my @t = forms($abs);
    for my $b (@{ $ctx->{bottles} }) {
        for my $bp (forms($b->{path})) {
            for my $t (@t) {
                return $b if $t =~ m{^\Q$bp\E/([^/]+)$} && $BOTTLE_FILES{$1};
            }
        }
    }
    return;
}

# --------------------------------------------------------------------------
# Tokenizer
#
# Splits a command line into statements of words. Each word is a hash:
#   text   -- the word with quotes removed, ~ and $HOME expanded
#   opaque -- contains a substitution or variable this script cannot evaluate
#   glob   -- contains an unquoted *, ? or [
#   pat    -- the word re-quoted for bsd_glob (only meaningful when glob)
# An unmatched quote ends tokenizing; statements read so far are kept and
# the context is flagged so the coarse backstop can ask.

sub tokenize {
    my ($ctx, $s) = @_;
    my @stmts;
    my @cur;
    my $w;
    my $home = $ctx->{home};
    my $new = sub { { text => '', opaque => 0, glob => 0, pat => '', started => 1 } };
    my $flush = sub {
        if ($w) { push @cur, $w; undef $w }
    };
    my $end = sub {
        $flush->();
        push @stmts, [@cur] if @cur;
        @cur = ();
    };
    my $lit = sub {    # append literal (quoted) text
        my ($t) = @_;
        $w ||= $new->();
        $w->{text} .= $t;
        (my $q = $t) =~ s/([\\*?\[\]{}~])/\\$1/g;
        $w->{pat} .= $q;
    };
    my $var = sub {    # append a $NAME / ${NAME} reference
        my ($name) = @_;
        $w ||= $new->();
        if ($name eq 'HOME') {
            $w->{text} .= $home;
            (my $q = $home) =~ s/([\\*?\[\]{}~])/\\$1/g;
            $w->{pat} .= $q;
        } else {
            $w->{text} .= "\$$name";
            $w->{pat}  .= "\\\$$name";
            $w->{opaque} = 1;
        }
    };

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
        if ($c eq '#' && !$w) {    # comment to end of line
            my $nl = index($s, "\n", $i);
            $i = $nl < 0 ? $n : $nl;
            next;
        }
        if ($c eq '<' || $c eq '>') {    # redirection: the operator and its target are not arguments
            if ($w && $w->{text} =~ /^\d+$/) { undef $w } else { $flush->() }    # 2>, 1>&2
            $i++ while $i < $n && substr($s, $i, 1) =~ /[<>&0-9]/;
            $i++ while $i < $n && substr($s, $i, 1) =~ /[ \t]/;
            $i++ while $i < $n && substr($s, $i, 1) !~ /[\s;&|()<>]/;
            next;
        }
        if ($c eq '\\') {
            if ($i + 1 < $n) {
                my $nx = substr($s, $i + 1, 1);
                if ($nx eq "\n") { $i += 2; next }    # line continuation
                $lit->($nx);
            }
            $i += 2;
            next;
        }
        if ($c eq "'") {
            my $close = index($s, "'", $i + 1);
            if ($close < 0) { $ctx->{unbalanced} = 1; undef $w; last }
            $lit->(substr($s, $i + 1, $close - $i - 1));
            $i = $close + 1;
            next;
        }
        if ($c eq '"') {
            $w ||= $new->();
            my $j = $i + 1;
            my $closed = 0;
            while ($j < $n) {
                my $d = substr($s, $j, 1);
                if ($d eq '"') { $closed = 1; last }
                if ($d eq '\\' && $j + 1 < $n && substr($s, $j + 1, 1) =~ /["\\\$`\n]/) {
                    $lit->(substr($s, $j + 1, 1));
                    $j += 2;
                    next;
                }
                if ($d eq '$') {
                    my $len = dollar($s, $j, $ctx, $var, $w);
                    $j += $len;
                    next;
                }
                if ($d eq '`') {
                    my $close = index($s, '`', $j + 1);
                    $j = $close < 0 ? $n : $close + 1;
                    $w->{opaque} = 1;
                    next;
                }
                $lit->($d);
                $j++;
            }
            if (!$closed) { $ctx->{unbalanced} = 1; undef $w; last }
            $i = $j + 1;
            next;
        }
        if ($c eq '$') {
            $w ||= $new->();
            $i += dollar($s, $i, $ctx, $var, $w);
            next;
        }
        if ($c eq '`') {
            $w ||= $new->();
            my $close = index($s, '`', $i + 1);
            $i = $close < 0 ? $n : $close + 1;
            $w->{opaque} = 1;
            next;
        }
        if ($c eq '~' && !$w) {    # tilde at word start
            my $next = $i + 1 < $n ? substr($s, $i + 1, 1) : '';
            if ($next eq '' || $next eq '/' || $next =~ /[\s;&|()]/) {
                $w = $new->();
                $w->{text} .= $home;
                (my $q = $home) =~ s/([\\*?\[\]{}~])/\\$1/g;
                $w->{pat} .= $q;
                $i++;
                next;
            }
        }
        # plain character
        $w ||= $new->();
        $w->{text} .= $c;
        $w->{pat}  .= $c;
        $w->{glob} = 1 if $c =~ /[*?\[]/;
        $i++;
    }
    $end->();
    return \@stmts;
}

# Consume a $ expansion at $s[$i]; return how many characters it used.
sub dollar {
    my ($s, $i, $ctx, $var, $w) = @_;
    my $rest = substr($s, $i);
    if ($rest =~ /^\$\{(\w+)\}/) { $var->($1); return length($&) }
    if ($rest =~ /^\$(\w+)/)     { $var->($1); return length($&) }
    if ($rest =~ /^\$\(/) {    # $( ... ) with nesting
        my $depth = 0;
        my $k = 0;
        my $len = length $rest;
        while ($k < $len) {
            my $ch = substr($rest, $k, 1);
            $depth++ if $ch eq '(';
            if ($ch eq ')') { $depth--; if ($depth == 0) { $k++; last } }
            $k++;
        }
        $w->{opaque} = 1;
        return $k;
    }
    if ($rest =~ /^\$[\@*#?\$!0-9-]/) { $w->{opaque} = 1; return 2 }
    $w->{text} .= '$';
    $w->{pat}  .= '\\$';
    return 1;
}

# --------------------------------------------------------------------------
# Analysis

sub verdict {
    my ($ctx, $decision, $reason) = @_;
    push @{ $ctx->{verdicts} }, [$decision, $reason];
}

sub analyse {
    my ($ctx, $command, $depth) = @_;
    return if $depth > $MAX_DEPTH;
    my $stmts = tokenize($ctx, $command);
    for my $words (@$stmts) {
        statement($ctx, [@$words], $depth);
    }
    if ($ctx->{unbalanced} && !@{ $ctx->{verdicts} }) {
        coarse($ctx, 'The command has an unmatched quote, so its targets could not be read.')
            if $command =~ /\brm\b|\bfind\b|\bunlink\b/;
    }
}

sub texts { map { $_->{text} } @_ }

sub basename_of {
    my ($t) = @_;
    $t =~ s{.*/}{};
    return $t;
}

sub statement {
    my ($ctx, $words, $depth) = @_;

    # Leading assignments and wrappers.
    my %inline_env;
    while (@$words) {
        my $t = $words->[0]{text};
        if ($t =~ /^([A-Za-z_]\w*)=(.*)$/s && !$words->[0]{glob}) {
            $inline_env{$1} = $2;
            shift @$words;
            next;
        }
        my $b = basename_of($t);
        last unless $WRAPPER{$b};
        shift @$words;
        if ($b eq 'sudo') {
            while (@$words && $words->[0]{text} =~ /^-/) {
                my $opt = shift(@$words)->{text};
                last if $opt eq '--';
                shift @$words if $opt =~ /^-[ugpChDRrT]$/ && @$words;
            }
        } elsif ($b eq 'env') {
            while (@$words && $words->[0]{text} =~ /^-/) {
                my $opt = shift(@$words)->{text};
                shift @$words if $opt =~ /^-[uPS]$/ && @$words;
            }
        } elsif ($b eq 'nice') {
            if (@$words && $words->[0]{text} eq '-n') { splice(@$words, 0, 2) }
            elsif (@$words && $words->[0]{text} =~ /^-\d+$/) { shift @$words }
        } elsif ($b eq 'caffeinate' || $b eq 'time' || $b eq 'command') {
            shift @$words while @$words && $words->[0]{text} =~ /^-/;
        }
    }
    return unless @$words;

    my $cmd = basename_of($words->[0]{text});
    my @args = @$words[1 .. $#$words];

    if ($cmd eq 'cd' || $cmd eq 'pushd') {
        my $to = @args ? $args[0] : { text => $ctx->{home}, opaque => 0 };
        if ($to->{opaque} || $to->{text} eq '-') { $ctx->{cwd} = undef }
        elsif (defined $ctx->{cwd} || $to->{text} =~ m{^/}) {
            $ctx->{cwd} = lexical_abs($to->{text}, $ctx->{cwd} // '/');
        }
        return;
    }

    if ($cmd =~ /^(?:ba|z|da|k)?sh$/) {
        for my $k (0 .. $#args) {
            if ($args[$k]{text} =~ /^-\w*c\w*$/ && $k + 1 <= $#args) {
                analyse_nested($ctx, $args[$k + 1]{text}, $depth);
                return;
            }
        }
        return;
    }
    if ($cmd eq 'eval') {
        analyse_nested($ctx, join(' ', texts(@args)), $depth);
        return;
    }

    if ($cmd eq 'rm')                     { return rm_like($ctx, \@args, 0) }
    if ($cmd eq 'unlink')                 { return rm_like($ctx, \@args, 1) }
    if ($cmd eq 'find')                   { return find_cmd($ctx, \@args) }
    if ($cmd eq 'rsync')                  { return rsync_cmd($ctx, \@args) }
    if ($cmd eq 'xargs')                  { return xargs_cmd($ctx, \@args) }
    if ($cmd eq 'cxbottle')               { return cxbottle_cmd($ctx, \@args, \%inline_env) }
    if ($cmd eq 'cxuninstall') {
        return if grep { $_->{text} =~ /^(?:--help|-h)$/ } @args;
        return verdict($ctx, 'ask',
            'cxuninstall removes CrossOver and its files from this account, which can include bottles. '
          . 'Archive every bottle worth keeping first (`cxbottle --bottle NAME --tar ~/NAME.cxarchive`).');
    }
    # Launching it, not downloading or unzipping it.
    if ($words->[0]{text} =~ /CrossOver_RemovalTool/i
        || ($cmd eq 'open' && grep { $_->{text} =~ /CrossOver_RemovalTool/i } @args)) {
        return verdict($ctx, 'ask',
            'The CrossOver Removal Tool deletes CrossOver, all of its files, and every bottle with every '
          . 'Windows application in it. CodeWeavers says to archive bottles before running it.');
    }
}

sub analyse_nested {
    my ($ctx, $text, $depth) = @_;
    my $saved = $ctx->{cwd};
    analyse($ctx, $text, $depth + 1);
    $ctx->{cwd} = $saved;
}

# Resolve one argument to absolute paths, or undef when it cannot be known.
sub resolve {
    my ($ctx, $word) = @_;
    return undef if $word->{opaque};
    my $t = $word->{text};
    return undef if !defined $ctx->{cwd} && $t !~ m{^/};
    my $cwd = $ctx->{cwd} // '/';
    if ($word->{glob}) {
        my $pat = $word->{pat};
        $pat = "$cwd/$pat" unless $pat =~ m{^/};
        my @m = grep { -e $_ || -l $_ } bsd_glob($pat, GLOB_QUOTE | GLOB_BRACE);
        return [ map { lexical_abs($_, $cwd) } @m ];
    }
    return [ lexical_abs($t, $cwd) ];
}

sub shq {
    my ($s) = @_;
    return $s if $s =~ m{^[\w./-]+$};
    $s =~ s/'/'\\''/g;
    return "'$s'";
}

sub archive_hint {
    my ($name) = @_;
    my $q = shq($name);
    (my $file = $name) =~ s/[^\w.-]+/_/g;
    return "`cxbottle --bottle $q --tar ~/$file.cxarchive`";
}

sub rm_like {
    my ($ctx, $args, $is_unlink) = @_;
    my $recursive = 0;
    my @targets;
    my $opts_done = 0;
    for my $a (@$args) {
        my $t = $a->{text};
        if (!$opts_done && !$a->{opaque} && $t eq '--') { $opts_done = 1; next }
        if (!$opts_done && !$is_unlink && $t =~ /^-/ && length $t > 1) {
            $recursive = 1 if $t =~ /^-[a-zA-Z]*[rR]/ || $t eq '--recursive';
            next;
        }
        push @targets, $a;
    }
    for my $a (@targets) {
        my $paths = resolve($ctx, $a);
        if (!$paths) {
            coarse($ctx, "A recursive delete targets `$a->{text}`, which this guard cannot resolve without running the shell.")
                if $recursive;
            next;
        }
        for my $p (@$paths) {
            # Removing a symlink removes the link, not what it points at --
            # unless a trailing slash makes rm follow it.
            next if -l $p && $a->{text} !~ m{/$};
            if (my $b = classify_file($ctx, $p)) {
                return verdict($ctx, 'deny',
                    "This deletes `$p`, a file bottle \"$b->{name}\" cannot run without. Bottle registry and "
                  . "configuration files are not regenerated; the bottle is unusable afterwards. Change "
                  . "settings with regedit, Wine Configuration or Advanced Settings instead. To keep a way back, "
                  . "archive the bottle first: " . archive_hint($b->{name}) . '.');
            }
            next unless $recursive;
            my ($kind, $b) = classify_recursive($ctx, $p);
            next unless $kind && $kind eq 'bottle';
            return verdict($ctx, 'deny',
                "This recursively deletes `$p`, which destroys bottle \"$b->{name}\" or its C: drive -- "
              . "the installed Windows applications, their licences, saves and settings. There is no undo. "
              . "Archive it first with " . archive_hint($b->{name}) . ", then remove it with "
              . "`cxbottle --bottle " . shq($b->{name}) . " --delete`, which the user confirms.");
        }
    }
}

sub find_cmd {
    my ($ctx, $args) = @_;
    my @starts;
    my $i = 0;
    # find's leading options (-H -L -P -E -X -x -s -f path)
    while ($i < @$args && $args->[$i]{text} =~ /^-[HLPEXxsdf]$/) {
        if ($args->[$i]{text} eq '-f' && $i + 1 < @$args) { push @starts, $args->[$i + 1]; $i += 2; next }
        $i++;
    }
    while ($i < @$args && $args->[$i]{text} !~ /^[-(!]/) { push @starts, $args->[$i]; $i++ }
    my @expr = @$args[$i .. $#$args];
    my $deletes = 0;
    for my $k (0 .. $#expr) {
        my $t = $expr[$k]{text};
        next unless $FIND_DELETE_ACTIONS{$t};
        if ($t eq '-delete') { $deletes = 1; last }
        my $runner = $k + 1 <= $#expr ? basename_of($expr[$k + 1]{text}) : '';
        if ($runner eq 'rm' || $runner eq 'unlink') { $deletes = 1; last }
    }
    return unless $deletes;
    @starts = ({ text => '.', opaque => 0 }) unless @starts;
    for my $s (@starts) {
        my $paths = resolve($ctx, $s);
        if (!$paths) { coarse($ctx, "`find` deletes under `$s->{text}`, which this guard cannot resolve."); next }
        for my $p (@$paths) {
            my ($kind, $b) = classify_recursive($ctx, $p);
            next unless $kind;
            next if $kind eq 'bottle' && !is_bottle_or_below($ctx, $p, $b);
            return verdict($ctx, 'ask',
                "`find` deletes files under `$p`, inside bottle \"$b->{name}\". Which files depends on the "
              . "filters, so confirm them first by running the same `find` without the delete action. "
              . "To keep a way back, archive the bottle: " . archive_hint($b->{name}) . '.');
        }
    }
}

# For find and rsync: fire from the bottle folder, the bottle, or below --
# not from ancestors like ~ or ~/Library, where a filtered find is ordinary
# housekeeping.
sub is_bottle_or_below {
    my ($ctx, $p, $b) = @_;
    my @roots = forms($b->{root});
    for my $t (forms($p)) {
        return 1 if grep { $t eq $_ } @roots;
        for my $bp (forms($b->{path})) { return 1 if within($t, $bp) }
    }
    return 0;
}

sub rsync_cmd {
    my ($ctx, $args) = @_;
    my $deletes = grep { $_->{text} =~ /^--(?:delete|del$|remove-source-files)/ } @$args;
    return unless $deletes;
    my @pos = grep { $_->{text} !~ /^-/ } @$args;
    return unless @pos >= 2;
    my $remove_src = grep { $_->{text} eq '--remove-source-files' } @$args;
    my @check = $remove_src ? @pos : ($pos[-1]);
    for my $a (@check) {
        next if $a->{text} =~ /^[^\/]*:/;    # remote host:path
        my $paths = resolve($ctx, $a) or next;
        for my $p (@$paths) {
            my ($kind, $b) = classify_recursive($ctx, $p);
            next unless $kind && is_bottle_or_below($ctx, $p, $b);
            return verdict($ctx, 'ask',
                "This rsync deletes files in `$p`, inside bottle \"$b->{name}\". Run it with `--dry-run` "
              . "first to see what it removes, and archive the bottle (" . archive_hint($b->{name}) . ').');
        }
    }
}

sub xargs_cmd {
    my ($ctx, $args) = @_;
    my @rest = @$args;
    while (@rest && $rest[0]{text} =~ /^-/) {
        my $opt = shift(@rest)->{text};
        shift @rest if $opt =~ /^-[IJLnPsER]$/ && @rest;    # options that take a value
    }
    return unless @rest;
    my $runner = basename_of($rest[0]{text});
    return unless $runner eq 'rm' || $runner eq 'unlink';
    my $recursive = grep { $_->{text} =~ /^-[a-zA-Z]*[rR]/ || $_->{text} eq '--recursive' } @rest;
    coarse($ctx, 'xargs supplies the delete targets from its input, which this guard cannot see.')
        if $recursive;
}

sub cxbottle_cmd {
    my ($ctx, $args, $env) = @_;
    my $delete = grep { $_->{text} eq '--delete' } @$args;
    return unless $delete;
    my $name;
    for my $k (0 .. $#$args) {
        my $t = $args->[$k]{text};
        if ($t eq '--bottle' && $k + 1 <= $#$args) { $name = $args->[$k + 1]{text}; last }
        if ($t =~ /^--bottle=(.*)$/s) { $name = $1; last }
    }
    $name //= $env->{CX_BOTTLE} // $ENV{CX_BOTTLE} // 'default';
    my ($known) = grep { lc($_->{name}) eq lc($name) } @{ $ctx->{bottles} };
    my $where = $known ? " at `$known->{path}`" : '';
    verdict($ctx, 'ask',
        "This permanently deletes bottle \"$name\"$where: everything in it, including its C: drive, "
      . "installed applications, licences and saves. cxbottle's own confirmation does not appear in a "
      . "non-interactive shell, so this prompt is the only one. If the bottle may be wanted again, "
      . "archive it first: " . archive_hint($name) . '.');
}

# The backstop for targets that cannot be resolved: ask, never deny, and only
# when the command is visibly about CrossOver.
sub coarse {
    my ($ctx, $why) = @_;
    return unless $ctx->{raw} =~ $MENTIONS;
    return if $ctx->{coarse_done}++;
    verdict($ctx, 'ask',
        "$why The command mentions CrossOver or a bottle, and a recursive delete there cannot be undone. "
      . 'Confirm the expanded target is not a bottle, or archive the bottle first.');
}
