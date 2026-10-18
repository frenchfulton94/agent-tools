#!/usr/bin/perl
#
# rust-check-gate.pl -- keep a session from ending on a Rust build that does not compile.
#
#   track -- PostToolUse on Edit|Write|MultiEdit. Records each edited `.rs` file
#            and `Cargo.toml` for this session. Nothing else is recorded and
#            nothing is run.
#   stop  -- Stop. If this session edited Rust, finds the Cargo workspace of
#            each edited file and runs `cargo check --workspace --all-targets`.
#            Errors located in a source file block the stop, with the first ones
#            quoted. Warnings never block.
#
# Why errors only: a warning is a judgement the project makes through its own
# `[lints]` and `build.warnings`, and a gate that blocks on them gets switched
# off. A compile error is never what the user wants left behind.
#
# Fails open, with a notice to the user, whenever cargo cannot give an answer:
# no cargo on PATH, an offline dependency fetch, a held build lock, a timeout,
# or any internal error. Only errors that name a file and line block, so an
# environment problem can never trap a session.
#
# Loop guard: Claude Code re-runs Stop after Claude continues. Skipping the
# check whenever `stop_hook_active` is set would let a still-broken build
# through on the very next stop, so instead the gate counts its blocks and
# lets the session end, with a notice, after MAX_BLOCKS consecutive ones. A
# crate that was already broken before the session cannot hold it forever.
#
# RUST_CHECK_GATE=0 in the environment turns the gate off. RUST_CHECK_GATE_DEBUG=1
# prints internal errors to stderr (the test suite asserts it never does).
#
# State lives in $CLAUDE_PLUGIN_DATA/rust-check-gate/<session>.{edited,blocks}.
# Perl, core modules only, like the plugin's registry guard.

use strict;
use warnings;
use JSON::PP ();
use File::Spec ();
use File::Temp ();

my $MAX_BLOCKS  = 2;      # consecutive blocks before the gate lets the stop through
my $TIMEOUT     = 240;    # seconds; under the 300 s hook timeout so the notice gets out
my $MAX_QUOTED  = 8;      # error lines quoted back to Claude
my $TAG         = '[rust check gate]';

exit main();

sub main {
    my $mode = shift @ARGV // '';
    my $out = eval { $mode eq 'track' ? track() : $mode eq 'stop' ? stop() : '' };
    if ($@) {
        print STDERR "$TAG internal error: $@" if $ENV{RUST_CHECK_GATE_DEBUG};
        return 0;
    }
    print $out if $out;
    return 0;
}

sub payload {
    my $raw = do { local $/; <STDIN> };
    return undef unless defined $raw && length $raw;
    my $p = eval { JSON::PP->new->decode($raw) };
    return ref $p eq 'HASH' ? $p : undef;
}

sub state_dir {
    my $base = $ENV{CLAUDE_PLUGIN_DATA};
    $base = File::Spec->tmpdir unless defined $base && length $base;
    my $dir = "$base/rust-check-gate";
    mkdir $base unless -d $base;
    mkdir $dir  unless -d $dir;
    return -d $dir ? $dir : undef;
}

sub session_key {
    my ($p) = @_;
    my $s = $p->{session_id} // 'unknown';
    $s =~ s/[^A-Za-z0-9._-]/_/g;    # used in a filename
    return $s;
}

# --------------------------------------------------------------------------

sub track {
    my $p = payload() or return '';
    my $input = ref $p->{tool_input} eq 'HASH' ? $p->{tool_input} : {};
    my $file = $input->{file_path} // $input->{filePath} // '';
    return '' unless $file =~ /\.rs$/ || $file =~ m{(?:^|/)Cargo\.toml$};
    return '' if $file =~ m{/target/|/\.cargo/registry/|/\.cargo/git/};
    my $dir = state_dir() or return '';
    open(my $fh, '>>', "$dir/" . session_key($p) . '.edited') or return '';
    print $fh "$file\n";
    close $fh;
    return '';
}

# --------------------------------------------------------------------------

sub stop {
    return '' if ($ENV{RUST_CHECK_GATE} // '') eq '0';
    my $p = payload() or return '';
    my $dir = state_dir() or return '';
    my $key = session_key($p);
    my $marker = "$dir/$key.edited";
    my $blocks = "$dir/$key.blocks";
    return '' unless -f $marker;

    open(my $fh, '<', $marker) or return '';
    my %seen;
    my @files = grep { length && !$seen{$_}++ } map { chomp; $_ } <$fh>;
    close $fh;

    my $cwd = $p->{cwd};
    my %workspaces;
    for my $f (@files) {
        $f = "$cwd/$f" if defined $cwd && $f !~ m{^/};
        my $manifest = nearest_manifest($f) or next;
        my $ws = workspace_manifest($manifest) // $manifest;
        $workspaces{$ws} = 1;
    }
    unless (%workspaces) {
        unlink $marker, $blocks;
        return '';
    }

    my (@errors, @unavailable);
    for my $ws (sort keys %workspaces) {
        my ($status, $out) = run_cargo($ws);
        if (!defined $status) {
            push @unavailable, "$ws: $out";
            next;
        }
        next if $status == 0;
        my @located = grep { /^\S.*?:\d+:\d+: error(?:\[E\d{4}\])?: / } split /\n/, $out;
        if (@located) {
            push @errors, [$ws, \@located];
        } else {
            my ($first) = grep { /^error/ } split /\n/, $out;
            push @unavailable, "$ws: " . ($first // "cargo check exited $status without a located error");
        }
    }

    if (!@errors) {
        unlink $marker, $blocks;
        return '' unless @unavailable;
        return notice("Could not check the Rust build, so the session was not held: "
            . join('; ', @unavailable));
    }

    my $count = 0;
    if (-f $blocks && open(my $bh, '<', $blocks)) { $count = (<$bh> // 0) + 0; close $bh }
    if ($count >= $MAX_BLOCKS) {
        unlink $marker, $blocks;
        return notice("The Rust build still fails after $MAX_BLOCKS attempts to fix it; "
            . 'letting the session end. Run `cargo check --workspace --all-targets` to see the errors.');
    }
    if (open(my $bh, '>', $blocks)) { print $bh $count + 1; close $bh }

    my $left = $MAX_BLOCKS - $count - 1;    # blocks still possible after this one
    my $total = 0;
    $total += scalar @{ $_->[1] } for @errors;
    my @quoted;
    for my $e (@errors) {
        for my $line (@{ $e->[1] }) {
            push @quoted, "  $line" if @quoted < $MAX_QUOTED;
        }
    }
    my $where = join(', ', map { $_->[0] } @errors);
    my $reason = "$TAG `cargo check --workspace --all-targets` fails after Rust edits in this session "
        . "($total error" . ($total == 1 ? '' : 's') . " in $where). Fix them before finishing. "
        . 'This gate re-runs cargo check at each stop and does not read replies; '
        . ($left == 0 ? 'the next stop is allowed even if the build still fails'
                      : "it will block at most $left more time" . ($left == 1 ? '' : 's'))
        . '. If the user asked for code that does not compile, say so in your final reply and stop again. '
        . ($total > $MAX_QUOTED ? "First $MAX_QUOTED:\n" : "Errors:\n")
        . join("\n", @quoted)
        . ($total > $MAX_QUOTED ? "\nFor this many errors, hand the build to the rust-build-triage agent." : '');
    return JSON::PP->new->canonical->encode({ decision => 'block', reason => $reason }) . "\n";
}

sub notice {
    my ($msg) = @_;
    return JSON::PP->new->canonical->encode({ systemMessage => "$TAG $msg" }) . "\n";
}

sub nearest_manifest {
    my ($file) = @_;
    (my $dir = $file) =~ s{/[^/]*$}{};    # a Cargo.toml finds itself
    while (length $dir) {
        return "$dir/Cargo.toml" if -f "$dir/Cargo.toml";
        last if $dir !~ m{/};
        $dir =~ s{/[^/]*$}{};
    }
    return -f '/Cargo.toml' ? '/Cargo.toml' : undef;
}

sub workspace_manifest {
    my ($manifest) = @_;
    my ($status, $out) = capture(10, 'cargo', 'locate-project', '--workspace',
        '--message-format', 'plain', '--manifest-path', $manifest);
    return undef unless defined $status && $status == 0;
    my ($path) = grep { m{Cargo\.toml$} } split /\n/, $out;
    return $path;
}

sub run_cargo {
    my ($ws) = @_;
    return capture($TIMEOUT, 'cargo', 'check', '--workspace', '--all-targets',
        '--message-format=short', '--quiet', '--manifest-path', $ws);
}

# Run a command without a shell, merging stderr into stdout. Returns
# (exit status, output), or (undef, reason) when it could not finish.
sub capture {
    my ($timeout, @cmd) = @_;
    my $tmp = File::Temp->new;
    my $pid = fork();
    return (undef, "fork failed: $!") unless defined $pid;
    if ($pid == 0) {
        open(STDIN, '<', '/dev/null');
        open(STDOUT, '>', $tmp->filename) or exit 127;
        open(STDERR, '>&', \*STDOUT);
        $ENV{CARGO_TERM_COLOR} = 'never';
        exec { $cmd[0] } @cmd;
        exit 127;
    }
    my $timed_out = 0;
    eval {
        local $SIG{ALRM} = sub { die "timeout\n" };
        alarm $timeout;
        waitpid($pid, 0);
        alarm 0;
    };
    if ($@) {
        $timed_out = 1;
        kill 'TERM', $pid;
        waitpid($pid, 0);
    }
    my $status = $? >> 8;
    open(my $fh, '<', $tmp->filename) or return (undef, 'could not read cargo output');
    my $out = do { local $/; <$fh> } // '';
    close $fh;
    return (undef, "timed out after ${timeout}s") if $timed_out;
    return (undef, "`$cmd[0]` not found on PATH") if $status == 127 && $out eq '';
    return ($status, $out);
}
