---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260818-HOTFIX-LEGACY-REGRESSION-LANE-MISSING-RESOURCE-BUDGET
phase: open
date: 2026-08-18
tags: [testing, bug]
---

# TCK-20260818-HOTFIX-LEGACY-REGRESSION-LANE-MISSING-RESOURCE-BUDGET

## Title
`lane-legacy-regression`'s Makefile target never passed `--resource-budget large`, causing
`test_arena_stress_50v50` to time out under the default 60s budget on its first-ever real CI run

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure: "Legacy regression" step of the "Slow regression" job (run 32100864254, commit
ba95336e) — this step's `make lane-legacy-regression` (`pytest tests/ -m "legacy_compat"`) had
never run to completion on real CI before today (gated as the last step of a job that was itself
gated behind everything else, per this session's established `-m slow` throughline).

Investigation initially misled by an incomplete local reproduction: a naive `pytest tests/ -m
"legacy_compat"` run locally showed 4 failures (`test_arena_stress_50v50`,
`test_long_run_pure_stability`, `test_long_run_runtime_stability`,
`test_long_run_determinism_parity`) plus 1 error (`test_compile_report_contents`). Reading the 3
long-run tests' own source revealed each carries `@pytest.mark.skipif(os.environ.get("CI") ==
"true", ...)` — GitHub Actions sets `CI=true` automatically for every job, but a plain local
`pytest` invocation does not, so these tests correctly EXECUTE (and fail/timeout) locally while
they correctly SKIP on real CI. Re-running with `CI=true` explicitly set locally (faithfully
matching real GitHub Actions) confirmed: the 3 skipif-gated tests skip as intended, the
`test_compile_report_contents` error also disappears (it was a side effect of the timeout-raising
`SIGALRM`-based `tests/conftest.py::timeout_handler` leaking state into an adjacent test, not a
real defect), and exactly **one** genuine failure remains: `test_arena_stress_50v50` —
`TimeoutError: Test execution exceeded the resource time limit.` — under the default
`--resource-budget medium` (60s), which `lane-legacy-regression`'s Makefile target never
overrides, unlike every other slow/heavy test invocation in this repo (all of which explicitly
pass `--resource-budget large`, 600s).

## Scope
Add `--resource-budget large` to `lane-legacy-regression`'s `pytest` invocation in the Makefile,
matching every other slow-test lane's convention.

## Out of Scope
- The 3 `skipif(CI=="true")`-gated long-run tests (`test_long_run_pure_stability`,
  `test_long_run_runtime_stability`, `test_long_run_determinism_parity`) — correctly skip on real
  CI already, not touched. `test_long_run_determinism_parity`'s own real, unresolved determinism
  bug (Mechanism B / audit finding F7, found earlier this session by
  `TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE`) remains open there regardless —
  irrelevant to this lane since the test never runs on CI at all.
- `test_compile_report_contents`'s teardown/setup ERROR — confirmed to be a knock-on artifact of
  the `test_arena_stress_50v50` timeout (SIGALRM handler state), not a real defect; disappears
  once the root timeout is fixed.
- Any `src/` change.

## Acceptance Criteria
- [x] `lane-legacy-regression` passes `--resource-budget large`.
- [x] Full lane reproduced locally with `CI=true` set (faithfully matching real GitHub Actions)
      and the fix applied: 80 passed, 4 skipped (the 3 intentional CI skips + 1 more), 0 failed,
      0 errors.
- [x] No `src/` file changed.

## Related Tickets
- `TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE` (the real, still-open Mechanism
  B/F7 determinism finding in `test_long_run_determinism_parity` — unaffected by this ticket since
  that test correctly never runs on real CI)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- `Makefile`

## Assumptions / Open Questions
None.

## Implementation Notes
A key methodology correction during this investigation: local reproduction of any CI job/lane
must set `CI=true` to faithfully match GitHub Actions' own automatic environment, especially for
lanes containing `skipif(os.environ.get("CI") == "true", ...)`-gated tests — omitting it produces
a materially different (and here, misleading) local test selection than what real CI actually
runs.

## Test Summary
- Pre-fix, `CI=true` (accurate reproduction): `1 failed, 79 passed, 4 skipped, 9021 deselected` —
  `test_arena_stress_50v50` `TimeoutError`.
- Post-fix, `CI=true` + `--resource-budget large`: `80 passed, 4 skipped, 9021 deselected, 0
  failed`.

## Files Changed
- `Makefile`

## Completion Summary
Root-caused a real CI failure on this lane's first-ever completed run to a genuine Makefile
configuration gap (missing `--resource-budget large`), after an initial local reproduction
without `CI=true` set produced a misleading picture (3 tests that correctly skip on real CI, plus
1 knock-on teardown error from their timeouts, none of which are real problems). Verified the fix
against a faithful, `CI=true`-accurate local reproduction of the full lane before considering this
resolved.
