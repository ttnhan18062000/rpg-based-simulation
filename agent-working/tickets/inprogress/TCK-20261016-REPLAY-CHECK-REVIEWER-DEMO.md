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
TBD.

## Test Summary
TBD.

## Files Changed
TBD.

## Completion Summary
TBD.
