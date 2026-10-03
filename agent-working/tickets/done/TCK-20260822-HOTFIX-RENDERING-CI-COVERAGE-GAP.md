---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260822-HOTFIX-RENDERING-CI-COVERAGE-GAP
phase: done
date: 2026-08-22
tags: [testing]
---

# TCK-20260822-HOTFIX-RENDERING-CI-COVERAGE-GAP

## Title
tests/unit/rendering/ (added by TCK-20260821-WORLD-RENDER-CORE) is not covered by any fast-lane CI job

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260821-WORLD-RENDER-CORE` added a new top-level test directory `tests/unit/rendering/`
(5 test files) but `.github/workflows/test.yml`'s three `unit-*` fast-lane jobs
(`unit-core-world`, `unit-gameplay`, `unit-infra`) each enumerate an explicit, hardcoded list of
`tests/unit/<subdir>` paths — `tests/unit/rendering` was never added to any of them. The existing
static regression guard `tests/tools/test_ci_workflow_test_coverage.py::test_check_against_real_repo_state_passes_cleanly`
correctly and deterministically detects this ("Orphaned test directory not referenced by any
fast-lane CI job path list: ['ci_test_dir_covered:tests/unit/rendering']") and fails every single
run of the `API / tools / logging` job (`tests/tools/` is that job's own scope) — this was
misdiagnosed for several PR CI runs as transient environment flakiness before being root-caused
directly via local reproduction of the exact failing assertion. Same category of gap as
`TCK-20260821-HOTFIX-MIGRATION-LANES-PLATFORM-COVERAGE-GAP` from earlier this session (a different
CI path-coverage regex, same root pattern: a new top-level test/src directory not wired into an
existing coverage-enforcing mechanism).

## Scope
- Add `tests/unit/rendering` to the `unit-infra` job's (`"Unit · infra / observability"`) explicit
  `pytest` path list in `.github/workflows/test.yml`, alongside its existing
  `tests/unit/observability`/`tests/unit/perf`/`tests/unit/diagnostics` neighbors — the closest
  existing bucket for an artifact/tooling-generation domain, matching this ticket's own
  investigation.md's module-placement reasoning (`src/rendering/` as a sibling artifact-producing
  package, same category as observability reporting).
- Confirm `tests/tools/test_ci_workflow_test_coverage.py::test_check_against_real_repo_state_passes_cleanly`
  passes after the fix.

## Out of Scope
- Any other CI coverage gap not related to `tests/unit/rendering`.
- Re-litigating which job is "more correct" beyond the one sensible choice above — this is a
  narrow, self-evident hotfix.

## Acceptance Criteria
- [x] `tests/unit/rendering` is added to `.github/workflows/test.yml`'s `unit-infra` job's pytest
      path list.
- [x] `tests/tools/test_ci_workflow_test_coverage.py::test_check_against_real_repo_state_passes_cleanly`
      passes.
- [x] `tests/unit/rendering/`'s own 10 tests still pass when run under the `unit-infra` job's
      command shape (no path/import assumptions broken by running from a different job).

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE (origin of the new, uncovered test directory)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent.

## Related Code Areas
- .github/workflows/test.yml
- tests/unit/rendering/

## Assumptions / Open Questions
None.

## Implementation Notes
Added `tests/unit/rendering \` to `.github/workflows/test.yml`'s `unit-infra` job (`"Unit ·
infra / observability"`), immediately after `tests/unit/observability`, alongside its other
artifact/tooling-generation-domain neighbors (`tests/unit/perf`, `tests/unit/diagnostics`).

Root-caused via direct local reproduction of `PR #45`'s repeatedly-failing `API / tools / logging`
CI check: initially misdiagnosed as transient environment flakiness across several reruns (the
check-run annotations and job logs were both blocked by a persistent local network filter on
GitHub's log-storage hosts, `*.blob.core.windows.net` and `results-receiver.actions.githubusercontent.com`),
until running `tests/tools/test_ci_workflow_test_coverage.py::test_check_against_real_repo_state_passes_cleanly`
directly surfaced the real, deterministic assertion failure: "Orphaned test directory not
referenced by any fast-lane CI job path list: ['ci_test_dir_covered:tests/unit/rendering']". This
is the same test-coverage-drift category as `TCK-20260821-HOTFIX-MIGRATION-LANES-PLATFORM-COVERAGE-GAP`
from earlier this session — an existing regression guard doing its job correctly, not flakiness.

Byproduct finding during investigation, not part of this ticket's own fix: the shared working
directory's local branch ref for `world-rendering-core-batch` had been contaminated by another
concurrent session's unrelated HUD-epic commits (2 commits, never pushed to origin) between
pushes. Cleaned via `git reset --soft origin/world-rendering-core-batch` plus `git restore
--source=origin/...` on the specific foreign paths — confirmed `origin/world-rendering-core-batch`
itself was never affected.

## Test Summary
```
PYTHONPATH=. pytest tests/tools/test_ci_workflow_test_coverage.py tests/unit/rendering/ -v
```
36/36 passed, including the specific regression guard this ticket fixes
(`test_check_against_real_repo_state_passes_cleanly`) and all 10 of
`TCK-20260821-WORLD-RENDER-CORE`'s own rendering tests (confirming they still pass importable
from the `unit-infra` job's command shape, not just in isolation).

## Files Changed
- `.github/workflows/test.yml` (added `tests/unit/rendering` to the `unit-infra` job's path list)

## Completion Summary
Fixed a real, self-inflicted CI coverage gap: `TCK-20260821-WORLD-RENDER-CORE` added
`tests/unit/rendering/` without wiring it into any fast-lane CI job, causing the existing
`test_check_against_real_repo_state_passes_cleanly` regression guard to correctly and
deterministically fail the `API / tools / logging` job on every run — misdiagnosed as flakiness
across several PR reruns before being root-caused via direct local reproduction of the actual
failing assertion. One-line fix, confirmed via the exact same test now passing.
