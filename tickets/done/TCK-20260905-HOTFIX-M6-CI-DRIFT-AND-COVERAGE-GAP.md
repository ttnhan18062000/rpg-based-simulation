---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260905-HOTFIX-M6-CI-DRIFT-AND-COVERAGE-GAP
phase: done
date: 2026-09-05
tags: [strategy]
---

# TCK-20260905-HOTFIX-M6-CI-DRIFT-AND-COVERAGE-GAP

## Title
Fix 2 real CI failures after the M6 batch: parity next-id drift + a new test directory missing from any fast-lane CI job

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
CI's "API / tools / logging" job failed on PR #133 (branch `m6-implementation`). First confirmed
this was NOT pre-existing on `main` (its own latest CI run at this branch's exact fork point passes
this exact job) before investigating further. Root-caused via local reproduction of the exact CI
command to exactly 2 failing tests:

1. **`test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`** —
   the same documented "hardcoded test baseline drift" class this session has hit three times now
   (M4, M5 twice). `TCK-20260905-HOME-EXILE-REFUGEE-THREADS`'s own already-verified new
   `WORLD-DISPLACE-001` parity entry legitimately moved `next_available_id()`'s real output past the
   test's stale `WORLD-BELIEF-003` expectation. Verified the live function output
   (`WORLD-DISPLACE-002`) directly against the real ledger content before touching the test —
   confirmed correct, not a bug in `next_available_id()` itself.
2. **`test_ci_workflow_test_coverage.py::test_check_against_real_repo_state_passes_cleanly`** — a
   genuinely new finding, not seen before this batch: `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`
   created a brand-new test directory, `tests/unit/replay/`, with real test files
   (`test_fingerprint_identity_coverage.py`), but never added that directory to any fast-lane CI
   job's explicit pytest path list in `.github/workflows/test.yml`. That ticket's own Test phase did
   run `tests/unit/replay/` as part of its own scoped local verification, so the tests themselves are
   real and passing — but without this fix, they would never actually execute in real CI (only the
   nightly/manual `slow` job's blanket `tests` path would ever touch them, and this repo's own
   `ci_workflow_test_coverage` check exists specifically to catch that silent gap before it ships).

## Scope
- `tests/tools/test_parity_updater_static.py` — update the hardcoded expected value from
  `WORLD-BELIEF-003` to `WORLD-DISPLACE-002`, with the test's own comment rewritten to cite the real,
  current evidence.
- `.github/workflows/test.yml` — add `tests/unit/replay` to the "Unit · core / world" job's pytest
  path list (both the main `Run` step and the `Base branch test collection` step, to stay
  consistent), alongside the other core/determinism-adjacent directories (`tests/unit/core`,
  `tests/unit/kernel`, `tests/unit/engine`).

## Out of Scope
- Any change to `next_available_id()`'s own implementation — confirmed correct, not a bug.
- Any other test directory's CI coverage — not audited here; this fix addresses only the one real
  gap `test_ci_workflow_test_coverage.py` itself flagged.
- Any change to the actual `tests/unit/replay/` test content — those tests are real and already
  passing; this ticket only wires them into real CI execution.

## Acceptance Criteria
- [x] `tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`
      passes against the live `docs/parity_ledger/world_dynamics.yaml` corpus.
- [x] `tests/tools/test_ci_workflow_test_coverage.py::test_check_against_real_repo_state_passes_cleanly`
      passes — `tests/unit/replay` is now referenced by a real fast-lane CI job.
- [x] No production code (`tools/gate_checks/parity_updater_static.py`,
      `tools/gate_checks/ci_workflow_test_coverage.py`) is touched.

## Related Tickets
- TCK-20260905-HOME-EXILE-REFUGEE-THREADS (idea 65, DONE — the ticket whose new `WORLD-DISPLACE-*`
  parity entry caused the first drift)
- TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE (idea 39, DONE — the ticket whose new `tests/unit/replay/`
  directory caused the second gap)
- TCK-20260905-HOTFIX-PARITY-NEXT-ID-WORLD-BELIEF-DRIFT (the immediately-prior M5-batch precedent for
  the same drift class, same test file)

## Related Docs
- CLAUDE.md's CI Failure Triage section (documents the hardcoded-baseline-drift class as an accepted
  hotfix pattern)
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None — hotfix tier, self-evident intent captured in this ticket.

## Related Code Areas
- tests/tools/test_parity_updater_static.py
- .github/workflows/test.yml

## Assumptions / Open Questions
None.

## Implementation Notes
Both fixes verified locally before commit: the parity test against the live ledger's real computed
`next_available_id()` output, and the CI-coverage test against the updated `.github/workflows/test.yml`.
Confirmed via local reproduction of the exact original CI command that no other failures exist beyond
these two.

## Test Summary
- `tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_parity_updater_static.py
  tests/tools/test_parity_index_baseline.py` — 62 passed, 0 failed.
- Full original CI command (`tests/api tests/cli tests/tools tests/logging tests/engine
  tests/observability`) previously showed 2 failed, 2860 passed — both failures fixed here.

## Files Changed
- `tests/tools/test_parity_updater_static.py`
- `.github/workflows/test.yml`

## Completion Summary
Fixed the same documented parity-next-id hardcoded-baseline drift class this session has now hit
four times, plus a genuinely new finding: a new M6 test directory (`tests/unit/replay/`) was never
wired into any fast-lane CI job's path list, meaning its real, passing tests would never actually run
in CI without this fix. Both root-caused via local reproduction of the exact CI command, not guessed
from the job name. No production code touched.
