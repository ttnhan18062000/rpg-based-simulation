---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261016-REPLAY-CHECK-REVIEWER-DEMO
phase: inprogress
date: 2026-10-16
tags: [determinism, testing]
---

# TCK-20261016-REPLAY-CHECK-REVIEWER-DEMO

## Title
`make replay-check`: a one-command reviewer demo that the same seed gives the same final state hash under the Canonical signal contract

## Status
INPROGRESS

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
Source: owner approval via lead-planner (2026-10-16), dispatched by codebase-planner. A reviewer can see determinism working
without reading the engine contracts: one command runs the simulation CLI twice with the same seed under
`RPG_SIGNAL_CONTRACT=canonical` and reports whether the two `Final State Hash:` values match. Verified by the planner on origin/main
927700be4: seed 42 / 300 ticks gives the same hash 3 times out of 3 under Canonical, and two different hashes under the default
LIVE contract (known gap, #585, PERF-D1 A2). No `src/` change.

## Scope
1. `codebase/reports/replay_check.py` (`python3 -m codebase.reports.replay_check`): runs the CLI twice as subprocesses from the repo
   root with `RPG_SIGNAL_CONTRACT=canonical` (defaults `--seed 42 --ticks 300`, `sys.executable`), parses `Final State Hash:`, prints
   both hashes and MATCH or DIFFER. Exit 0 match, 1 differ, 2 could not run (crash, timeout, missing hash). `--live` is opt-in,
   never the default, runs the pair again on the default contract, prints "expected to differ today (known gap, #585)", and never
   changes the exit code. It deletes only the `data/runs` directories its own runs created.
2. Makefile target `replay-check`.
3. `docs/guides/reviewer_replay_check.md`: the command, the expected output, what it proves and what it does not.
4. README.md: one link line under a new "For reviewers" heading.
5. `tests/codebase/test_replay_check.py`: unit tests with a fake CLI, no real simulation.

## Out of Scope
- Any `src/` change; the `--entities` flag (ignored for sandbox_world, lead is taking it to rpg on #617).
- The README determinism row (rpg's, on #617).
- Making the LIVE contract reproducible (#585).
- The `import-linter-flip` branch.

## Acceptance Criteria
- `make replay-check` prints two equal hashes and MATCH for seed 42 / 300 ticks and exits 0.
- Exit codes 0 / 1 / 2 as above; the `--live` label is printed and the exit code is unchanged by it.
- The env var is set on both runs; only the run's own `data/runs` directories are removed.
- The guide states what it does not prove (LIVE runs, the modelled-cost Canonical contract is not the full PERF-M1 one, short-run
  measurement not a proof) and cites `docs/engine/deterministic_execution.md` ("What runs today").
- tests/codebase scoped, ruff, and all of tests/tools (Makefile edit) pass.

## Related Tickets
- TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY

## Related Docs
- docs/engine/deterministic_execution.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
- None.

## Related Code Areas
- codebase/reports/, tests/codebase/, Makefile, README.md, docs/guides/

## Assumptions / Open Questions
- The CLI does not print the run id on stdout (only inside a watchdog alert on stderr), so the run's own directories are identified
  by the child process id embedded in the run id (`run_<epoch>_<n>_<pid>_<hex>`), not by a directory diff. Told to codebase-planner.

## Implementation Notes
`codebase/reports/replay_check.py`: `main(argv, command_builder, repo_root)` runs `run_once` twice per contract (Popen from the repo root, `sys.executable -m src cli --seed S --ticks N`, stderr discarded, per-run timeout default 300 s). The Canonical pair sets `RPG_SIGNAL_CONTRACT=canonical`; the `--live` pair removes the variable. Exit 0 / 1 / 2 from the Canonical pair alone. A non-zero CLI exit, a timeout or a missing `Final State Hash:` line is exit 2.

Cleanup: the CLI never prints the run id on stdout (it only appears inside a watchdog alert on stderr), and `--replay <dir>` does not stop it writing `data/runs/<run_id>`. So `own_run_dirs` matches `run_<epoch>_<n>_<pid>_<hex>` on the child pid from Popen and removes exactly those directories, also after a timeout kill. No directory diff. Pids recycle, so a dir also needs an epoch no older than the run's own start (less 1 s slack); a same-pid dir with an older epoch survives (planner review). On a crash or a missing hash the last 5 stderr lines are added to the reason, so exit 2 says why.

`docs/guides/reviewer_replay_check.md`, a README "For reviewers" section (one link line; the determinism row is untouched), and a `replay-check` Makefile target (picked up by `make help`).

## Test Summary
`tests/codebase/test_replay_check.py`: 14 tests against a fake CLI script (hash parsing, match 0, differ 1, crash / no hash / timeout 2, env var on both runs and no live pair by default, `--live` label with exit code unchanged, cleanup removes only its own run dirs, pid match is exact). `tests/codebase`: 491 passed, 2 skipped (after review fixes); real `make replay-check` rerun: same MATCH, data/runs empty. ruff clean on the two new files (`ruff check codebase` has 55 pre-existing findings, none in them).

Real run, `systemd-run --user --scope -p MemoryMax=3G make replay-check` (exit 0, `data/runs` left empty):
```
canonical contract (RPG_SIGNAL_CONTRACT=canonical) (seed=42, ticks=300)
  run 1: 43e5263e113907ec0119c9b7124c24ac0c16524fce80cec9559153b03e0e10b3
  run 2: 43e5263e113907ec0119c9b7124c24ac0c16524fce80cec9559153b03e0e10b3
MATCH
```
Real `--live --ticks 100` (exit 0): Canonical pair `95f0372b...` twice, MATCH; live pair `ca4c2d1b...` vs `17546857...`, DIFFER, labelled "expected to differ today (known gap, #585)".

## Files Changed
codebase/reports/replay_check.py, tests/codebase/test_replay_check.py, Makefile, README.md, docs/guides/reviewer_replay_check.md, docs/REGISTRY.yaml

## Completion Summary
TBD (tests/tools, knowledge-index and closure pending).
