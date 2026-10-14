---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261014-PRE-PUSH-CI-LANE-PARITY
phase: open
date: 2026-10-14
tags: [delivery, testing, workflows, process-improvement]
---

# TCK-20261014-PRE-PUSH-CI-LANE-PARITY

## Title
Let a push run, locally, the CI test lanes its changes touch, read from test.yml rather than a copied list

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
rpg-planner's process review of #536: the PR went red in CI six times on checks that local runs never covered:
perf inventories, API metadata, the `tests/visual_assets` census and a thread leak. The local pre-push step is
`tools/delivery/pre_push_advisory_hook.py` (there is no `tools/delivery/pre_push.py`); it checks commit subjects,
the monitoring shard and squash-merged branches, and runs no tests at all. Implementers pick scoped pytest commands
by hand, so a lane CI runs can be missed. The ruff/ast-grep pin half of the review is #583 (codebase-planner and
lead-planner), not here.

## Scope
1. A small resolver, `tools/delivery/ci_lanes.py`, that reads `.github/workflows/test.yml` (the single source; no
   hand-copied lane list) and, for a set of changed paths (`git diff --name-only origin/main...HEAD` by default),
   returns the CI jobs/steps whose path filters and test paths those changes touch, with each step's exact `run:`
   command.
2. A CLI on it: `--list` prints the affected lanes and commands; `--run` runs them in order locally and prints a
   pass/fail line per lane. Exit non-zero on a failing lane when `--run` is used (it is a command the implementer
   chooses to run, not a hook).
3. A fourth advisory check, D, in `pre_push_advisory_hook.py`: name the affected lanes and the one command to run
   them. Advisory only, never blocks, never runs tests inside the hook (hook timeouts), offline.
4. Agree with testing-planner, before implementing, how a CI step maps to changed paths (path filters, `changed`
   job outputs, steps without filters). test.yml is testing's; this ticket must not edit it. If the mapping needs a
   change in test.yml, file it as a request to testing-planner.
5. Document the command in `docs/guides/delivery_process.md` (PR Lifecycle, before push).

## Out of Scope
- Editing `.github/workflows/test.yml` or any testing-owned file.
- Slow and nightly lanes (`slow-regression*.yml`, `schedule:` triggers).
- Lint/ruff/ast-grep pins (#583).
- Making any check blocking.

## Acceptance Criteria
- For #536's changed-file list, `ci_lanes.py --list` names the lanes that held the 4 checks it missed (perf
  inventories, API metadata, visual_assets census, the thread-leak test). A test pins this with a fixture file list.
- Check D appears in the hook output when lanes are affected and says nothing otherwise; the hook still always exits 0.
- A test parses the real `test.yml` and fails if a job has a pytest step the resolver cannot map, so new CI lanes are
  not silently missed.
- testing-planner's agreement on the mapping is linked in Review notes.

## Related Tickets
- TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
- #583 (ruff/ast-grep pin half)

## Related Docs
- docs/guides/delivery_process.md
- docs/testing/migration_ci_lanes.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/delivery/pre_push_advisory_hook.py, tests/tools/test_delivery_pre_push_advisory.py
- .github/workflows/test.yml (read only)

## Assumptions / Open Questions
- The exact checks behind "perf inventories" and "thread leak" are to be confirmed from #536's CI logs during
  investigation, not guessed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
