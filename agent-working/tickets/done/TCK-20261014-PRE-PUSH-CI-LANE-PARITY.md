---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261014-PRE-PUSH-CI-LANE-PARITY
phase: done
date: 2026-10-14
tags: [delivery, testing, workflows, process-improvement]
---

# TCK-20261014-PRE-PUSH-CI-LANE-PARITY

## Title
Let a push run, locally, the CI test lanes its changes touch, read from test.yml rather than a copied list

## Status
DONE

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
- `tools/delivery/ci_lanes.py` reads `.github/workflows/test.yml` (read only). Path-filtered lanes are evaluated from the
  `changed-files` step's PERF_RE/MIG_RE/FRONTEND_RE/DOCKER_RE (Python `re`; no new dependency) and, for scenario-lane, the
  in-process `scenario_lane_paths.classify`. A job's `if:` is evaluated over a fixed set of atoms (an unknown atom fails open).
  Always-on = a job that does not need `changed-files`, derived, never listed; they are reported `runs` for any diff, with a
  `hint` where a changed file sits under a pytest step path (honouring `--ignore-glob`). `resync-gate` is a gate, not a lane.
- Mapping agreed with testing-planner (cross-session message, 2026-10-14): four changes taken (always-on never "not affected";
  three-dot committed diff with uncommitted warning; fail-open as `runs (fail-open)`; derive always-on; slow-regression lanes
  listed as not on PR). A stable regex module shared with CI is a request to testing-planner, not built here.
- Check D in `pre_push_advisory_hook.py`: advisory, offline, no test run, silent unless a path-filtered lane runs or an
  always-on lane has a hint; degrades to no finding on any error. `docs/guides/delivery_process.md` PR Lifecycle step 2b.
- Open question from the ticket: the fourth missed check of #536 (thread leak) could not be traced to a changed test file, so the
  fixture pins the three that could (perf, API metadata, visual_assets). The 453-file list is trimmed to one path per area.

## Test Summary
- `tests/tools/test_delivery_ci_lanes.py` (28 tests): guards on the real test.yml (missing/duplicate/uncompilable regex variable,
  unmapped output, pytest step with no tests/ path), #536 fixture naming perf-cert-arena and api-cli-engine, never-skipped always-on
  lanes, fail-open on diff/classifier/if errors, ignore-glob halves, three-dot diff, run_lanes pass/fail, check D (names lanes,
  silent otherwise, degrades on error, part of run_all_checks). With `test_delivery_pre_push_advisory.py`, `test_session_*.py`,
  `test_delivery_*.py`: 868 passed, 1 failed (`test_session_status.py::test_collect_runs_against_the_real_repository_without_failing`,
  `TimeoutError` from conftest's resource limit at load average 14-37 on 6 cores with 52 worktrees; it does not touch these
  files; reran alone under load: same timeout). Rerun at load average 1.2 (2026-10-14 evening): `test_session_status.py` 13 passed in 16 s.

## Files Changed
- tools/delivery/ci_lanes.py (new), tools/delivery/pre_push_advisory_hook.py, tests/tools/test_delivery_ci_lanes.py (new),
  docs/guides/delivery_process.md

## Completion Summary
`python3 -m tools.delivery.ci_lanes` lists, and `--run` runs, the CI lanes a diff touches, read from test.yml; the pre-push hook's
advisory check D names them. A test fails when test.yml gains something the resolver cannot map.
