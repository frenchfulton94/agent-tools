# Phase 10 record: game development on Metal

Evidence for `docs/specs/2026-10-18-phase10-games-design.md` and
`docs/plans/2026-10-18-phase10-games.md`. The spec's "Verification results"
section gives the verdict for each definition-of-done item, with pointers
into this directory. One directory per task, each with its report:

| Directory | Task | What it holds |
|---|---|---|
| `survey/` | before the plan | Corpus size, the seed probe, and the toolchain checks |
| `task-0-sweep/` | 0 | The kill-switch scan, the catalog regeneration, and the header check |
| `task-1-manifest/` | 1 | `manifest.tsv`: one row for each corpus page |
| `task-2-gates/` | 2 | The pinned metal-cpp version, the gate self-tests, and the whole-catalog Swift gate before and after |
| `task-3-slices/` | 3 | `sources.tsv` and `slices.tsv`, the 19 reading slices, and the script that makes them |
| `ledger/`, `notes/` | 4 and 7 | One read ledger and one notes file for each slice |
| `task-4-read/`, `task-7-read/` | 4 and 7 | The copy and field checks over the ledgers and notes |
| `task-5-write/`, `task-8-write/` | 5 and 8 | Gate logs, one claim-to-source sidecar for each reference, and `runtime/` logs for each "Measured" claim |
| `task-6-probe/` | 6 | R1, R2, R3, and R5 |
| `task-9-r4/` | 9 | R4, Processor Trace |
| `task-10-r6/` | 10 | The direct-distribution checks, and the reason R6 did not run |
| `task-12-evals/` | 12 | The trigger-eval sweep and its classification |
| `task-13-release/` | 13 | The release gates, the load check, and the clean-state check |

Task 11 has no directory. It was a two-line edit that the controller made,
and its gate counts are in the SDD ledger. The controller copies that ledger
to `sdd-ledger.md` at the close, after the final review. It holds every
controller ruling (P1–P47) and every deferred finding.

## What is not committed, and where it is

### Apple's text, the book, and the specifications

The reading rule kept every downloaded page and every PDF extract in
`authoring/apple-studio/pipeline/tmp/` (`$TMP`), which is gitignored. Nothing
in this record quotes Apple's documentation, the MSL specification, the
Feature Set Tables, or the book. The ledgers and notes are in our own words.

| Path in `$TMP` | What it is | Made by |
|---|---|---|
| `corpus/` | The `.md` body of each manifest page | `pipeline/crawl_corpus.py` |
| `pdf/` | The `pdftotext` output of the MSL 4.1 specification and the Feature Set Tables, and reader m06's chapter splits | Tasks 3 and 4 |
| `metal-cpp/26.4/` | The metal-cpp headers that the C++ gate compiles against | `pipeline/fetch_metal_cpp.sh 26.4` |
| `rust-gate/` | The Rust gate's scratch crates | `pipeline/typecheck_native.py` |
| `r01-extra/` | Apple's "Supported capabilities (macOS)" page, which reader r01 used | Task 7 |
| `g09/`, `m02/`, `m03/`, `m08/` | The readers' helper files | Tasks 4 and 7 |

The survey's PDFs are not committed either. The Numbers export of the
Feature Set Tables failed in Task 3 (an AppleEvent timeout), so no CSV
exists. `task-3-slices/report.md` records it.

### Raw session transcripts

The trigger-eval sessions are compressed under `raw/`, which `.gitignore`
excludes:

- `raw/task-12-evals-session-logs.tar.xz` holds the baseline sweep.
- `raw/task-12-evals-rerun-session-logs.tar.xz` holds the `conc-fire`
  re-run and the diagnostic.

Each archive keeps the original relative paths. A citation such as
`baseline/conc-fire.log:24` resolves after
`tar -xJf raw/<archive> -C task-12-evals`. The transcripts are not published,
because a session log carries the recording machine's environment
(CONVENTIONS.md, Verification records). The committed summaries cite them:
`results.tsv`, `classification.md`, and the console logs.

### Task 6 traces

The Task 6 runtime probe (`authoring/apple-studio/pipeline/fixtures/metal-probe/`)
keeps its traces in `$TMP`. They exist only on the machine that recorded
them: an Apple M4 Pro with macOS 27.0.1 and Xcode 27.1 (an Apple9 GPU).
`run.sh` in the fixture records them again. The logs in `task-6-probe/` cite
them as `$TMP/<name>`.

| Trace or output | Claim | Made by |
|---|---|---|
| `probe.gputrace` | R2 | `MetalProbe capture`. The profiling block's `profile run --embed` writes a profile into it. |
| `probe-compile-in-capture.gputrace` | R2 | `MetalProbe capture --compile-in-capture`. `profile run` hangs on it. |
| `r2/` (`draw0.png`, `cost.png`, `draw0_fragment_cost_top100.json`, `compile-in-capture-draw0.png`, the scripts run) | R2 | The `gpudebug` blocks and `fetch` commands |
| `r3-1.trace` | R3 | Metal System Trace, 100,000 frames. `xctrace export` crashes on it. |
| `r3-2.trace` | R3 | Game Performance, 100,000 frames |
| `r3-3.trace` | R3 | Metal System Trace, ended by `--time-limit 1s` |
| `r3-true.trace`, `r3-false.trace` | R3 | Time Profiler on `/usr/bin/true` and `/usr/bin/false`: the exit-status check |
| `r3-streams/` | R3 | Time Profiler on a shell that writes to stdout and stderr, with and without `--target-stdout` |
| `r3-*.toc.xml`, `r3-*.submissions.xml`, `r3-*.stdout` | R3 | `xctrace export` and `--target-stdout` output |
| `r5-cpp-host.gputrace`, `r5-rust-host.gputrace` | R5 | Each host's `--capture` |
| `r5-pre-fix/` | R5 | Copies of the project with the pre-fix argument string, unquoted and quoted |
| `r5-cpp-host.trace`, `r5-rust-host.trace`, `r5-*.toc.xml`, `r5-*.submissions.xml` | R5 | Metal System Trace on each host |

The crash reports that R2 and R3 cite (`GPUToolsReplayService`,
`GPUToolsDebugService`, `xctrace`) are in `~/Library/Logs/DiagnosticReports/` on
that machine. They are not copied here, because they carry the machine's
environment.

### Task 9 traces

R4's recordings are in `$TMP` too, on the same machine. `run.sh r4`,
`run.sh r4-finding`, and `run.sh r4-selftest` make them again.

| Trace or output | Claim | Made by |
|---|---|---|
| `r4.trace`, `r4.stdout`, `r4-export/` | R4 | Processor Trace on `sim --ticks 100000 --slow` (bundle 390M) |
| `r4-control.trace`, `r4-control.stdout`, `r4-control-export/` | R4 | Processor Trace on the control run (bundle 767M) |
| `r4-selftest-slow.trace`, `r4-selftest-normal.trace`, their `.stdout` and `-export/` | R4 self-test | Time Profiler, the analysis script's own check |
| `r4-explore.trace`, `r4-check.trace` and their outputs | R4, before the restart | The runs that `task-9-r4/r4-attempt-1.log` logs |
| `tp-dev.trace` and its exports | none | A recording that no committed log cites |

### Task 10 certificates

`r06-certs/` holds the two Apple Development certificates that
`task-10-r6/identity.log` reads, as PEM files. `r06-extra/` holds the account
help pages that Task 10 read beyond the corpus. Neither is committed: a
certificate names its Apple ID, and the pages are Apple's text. `identity.log` replaces each Apple ID with
`<Apple ID 1>` or `<Apple ID 2>`, and the record names the teams by team ID
only.

### Task 13 load check

`task-13/` holds the two load-check debug logs, the prompt, the answer, and
the `stream-json` output. `task-13-release/load-check.log` keeps the lines
that show the registration. It writes this worktree's absolute path as
`<worktree>`.

### Task briefs

Each task brief is a verbatim section of the committed plan ("Task N"), so
none is copied. The controller's additions to each brief are rulings, and
`sdd-ledger.md` holds them.

## Compressed but committed

Nothing in this record is compressed. `task-2-gates/catalog-before.log`,
`task-2-gates/catalog-after.log`, and `task-13-release/catalog-after.log`
are each under 260 KB, so they stay as text.
`task-13-release/catalog-diff.log` compares the first and the last of them,
and `task-13-release/catalog_diff.py` makes the comparison.
