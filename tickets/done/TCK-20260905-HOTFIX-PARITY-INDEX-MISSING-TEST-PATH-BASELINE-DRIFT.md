---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260905-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT
phase: open
date: 2026-09-05
tags: []
---

# TCK-20260905-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT

## Title
Update the hardcoded `missing_test_path_count` baseline in `test_parity_index_baseline.py` after SUB-327's fix

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
PR #129 CI's "API / tools / logging" job failed on
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`:
`assert 1315 == 1316`. Root cause confirmed via direct local reproduction (exact CI pytest
invocation, `.venv/bin/python3 -m pytest tests/api tests/cli tests/tools tests/logging
tests/engine tests/observability -m "not slow and not extra_slow"`) rather than assumed from the
job name, per this repo's CI Failure Triage rule.

This is the documented, self-describing drift pattern this same test's own comment block already
names (two prior precedent tickets: `TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`,
`TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`) — not a real regression, not
flakiness. This session's own earlier `TCK-20260905-SUB-327-FABRICATED-CITATION-FIX` (closed
2026-09-05, same session) repointed `docs/parity_ledger/substrate.yaml`'s `SUB-327` entry from
`test_path: null` to a real citation
(`tests/unit/movement/test_spatial_index.py::test_spatial_grid_rebuild_logic`), which correctly
drops the live `missing_test_path_count` scan from 1316 to 1315. The hardcoded baseline in the test
itself was not updated in that ticket's own commit — this ticket closes that gap.

## Scope
- Update the hardcoded `assert live_missing == 1316` to `1315` in
  `tests/tools/test_parity_index_baseline.py`.
- Append a new dated comment entry to the existing drift-history comment block (matching the
  established format of the prior 6 entries) citing `SUB-327` and this ticket.
- Re-run the affected test file directly to confirm it now passes.

## Out of Scope
- Any other test in the `tests/api tests/cli tests/tools tests/logging tests/engine
  tests/observability` CI job — all others passed on direct local reproduction.
- Any further parity-ledger content changes — `SUB-327`'s own fix is already complete and closed.

## Acceptance Criteria
- [x] `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
      passes against current `docs/parity_ledger/` content.
- [x] The drift-history comment block documents this update with the real cause (SUB-327's
      `test_path` fix) and date, matching the existing format.
- [x] No other parity-ledger or test-baseline file is touched.

## Related Tickets
- `TCK-20260905-SUB-327-FABRICATED-CITATION-FIX` (the change that caused this drift)
- `TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent, same pattern)
- `TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent, same pattern)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tests/tools/test_parity_index_baseline.py`
- `docs/parity_ledger/substrate.yaml` (source of the drift, not itself modified here)

## Assumptions / Open Questions
None.

## Implementation Notes
Confirmed via direct local reproduction of the exact failing CI job command
(`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
slow and not extra_slow" --tb=short -q`, run against `.venv/bin/python3` from the shared repo venv,
since this worktree has no local `.venv`) that this was the only failure among 2861 passed/17
skipped/1 xfailed tests in that job's scope — everything else in "API / tools / logging" is green
locally, confirming the CI failure is fully attributable to this single baseline drift, not a
broader regression. Cross-checked the sandbox's earlier TLS failure fetching raw GitHub Actions
logs against `productionresultssa0.blob.core.windows.net` via
`openssl s_client`/`x509 -noout -subject -issuer`, confirming a Fortinet/Fortiguard SDNS block page
cert (network-filter block, not a real SSL issue) before falling back to local reproduction, per
this repo's own documented CI Failure Triage fallback procedure.

## Test Summary
`pytest tests/tools/test_parity_index_baseline.py -q` — all pass after the baseline update.
Full CI-matching job scope (`tests/api tests/cli tests/tools tests/logging tests/engine
tests/observability`) already independently confirmed green apart from this one assertion via the
local reproduction run above (2861 passed, 17 skipped, 1 xfailed, 1 failed before the fix).

## Files Changed
- `tests/tools/test_parity_index_baseline.py`

## Completion Summary
Updated the hardcoded baseline assertion from 1316 to 1315 with a dated comment entry documenting
the cause (SUB-327's `test_path` fix). Confirmed the specific test passes standalone. This unblocks
PR #129's "API / tools / logging" CI job, which was failing only on this single stale-baseline
assertion, not any real regression.
