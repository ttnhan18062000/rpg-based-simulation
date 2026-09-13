---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT
phase: done
date: 2026-09-13
tags: []
---

# TCK-20260913-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT

## Title
Update the hardcoded `missing_test_path_count` baseline in `test_parity_index_baseline.py` after PROG-014's correction

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
PR #178 CI's "API / tools / logging" job failed on
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`:
`assert 1314 == 1315`. Root cause confirmed via a fresh local live-scan reproduction of the exact
counting logic the test itself uses (not assumed from the job name), per this repo's CI Failure
Triage rule — the live count is genuinely 1314 now, not a flake or a real regression.

This is the same documented, self-describing drift pattern this test's own comment block already
names (three prior precedent tickets: `TCK-20260830-`, `TCK-20260902-`, `TCK-20260905-HOTFIX-
PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`). This batch's own `TCK-20260912-VETERANCY-STAT-
MULTIPLIER-NEVER-APPLIED` corrected `docs/parity_ledger/progression.yaml`'s `PROG-014` from `status:
verified` (with `test_path: null`) to `status: missing` (still `test_path: null`, plus a real
`support_boundary`) — moving it *out* of this test's counted set, which only counts `status in
("verified", "divergent")` entries with a missing `test_path`. `missing` status is never counted,
so this correctly drops the live scan from 1315 to 1314. The hardcoded baseline in the test itself
was not updated in that ticket's own commit — this ticket closes that gap.

## Scope
- Update the hardcoded `assert live_missing == 1315` to `1314` in
  `tests/tools/test_parity_index_baseline.py`.
- Append a new dated comment entry to the existing drift-history comment block (matching the
  established format of the prior entries) citing `PROG-014` and this ticket.
- Re-run the affected test file directly to confirm it now passes.

## Out of Scope
- Any other test in the `tests/api tests/cli tests/tools tests/logging tests/engine
  tests/observability` CI job scope — the only failure observed in this PR's run was this single
  baseline assertion (the sibling "Migration lanes" job failure in the same run is an unrelated
  infra runner-acquisition failure, not a test failure — confirmed via
  `check-runs/.../annotations`: "The job was not started because it repeatedly failed to be
  acquired," resolved separately via `gh run rerun --failed`).
- Any further parity-ledger content changes — `PROG-014`'s own correction is already complete and
  closed as part of `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`.

## Acceptance Criteria
- [x] `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
      passes against current `docs/parity_ledger/` content.
- [x] The drift-history comment block documents this update with the real cause (`PROG-014`'s
      status correction) and date, matching the existing format.
- [x] No other parity-ledger or test-baseline file is touched.

## Related Tickets
- `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` (the change that caused this drift)
- `TCK-20260905-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent, same pattern)
- `TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent, same pattern)
- `TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent, same pattern)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tests/tools/test_parity_index_baseline.py`
- `docs/parity_ledger/progression.yaml` (source of the drift, not itself modified here)

## Assumptions / Open Questions
None.

## Implementation Notes
Confirmed via a fresh local run of the exact live-scan logic
`test_baseline_manifest_does_not_coerce_missing_test_path` itself uses (iterate every
`docs/parity_ledger/*.yaml` entry, count `status in ("verified", "divergent")` with falsy
`test_path`) that the current live count is 1314, matching the CI failure's own `assert 1314 ==
1315` exactly — not a flake, a real, expected drop caused by this same PR's own legitimate
`PROG-014` correction.

## Test Summary
`pytest tests/tools/test_parity_index_baseline.py -q` — all pass after the baseline update.

## Files Changed
- `tests/tools/test_parity_index_baseline.py`

## Completion Summary
Updated the hardcoded baseline assertion from 1315 to 1314 with a dated comment entry documenting
the cause (`PROG-014`'s status correction). Confirmed the specific test passes standalone. This
unblocks PR #178's "API / tools / logging" CI job, which was failing only on this single
stale-baseline assertion, not any real regression.
