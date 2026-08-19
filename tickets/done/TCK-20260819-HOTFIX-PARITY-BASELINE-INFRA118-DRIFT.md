---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-PARITY-BASELINE-INFRA118-DRIFT
phase: done
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-HOTFIX-PARITY-BASELINE-INFRA118-DRIFT

## Title
Fix stale parity-index baseline count after TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER's INFRA-118 fix

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on PR #23's "API / tools / logging" job:
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
asserts a hardcoded `live_missing` baseline (`1337`) that the test's own comment documents as
expected to drift downward whenever parity-ledger entries legitimately gain a `test_path`
(precedent: `TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT`, which moved this same baseline
from `1343` to `1337`).

`TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER`'s Parity phase did exactly that:
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-118` entry gained a real, non-null `test_path`
(previously `null`) citing the 2 guard tests that now enforce it. Independently re-derived the live
count via the test's own logic (scan all `docs/parity_ledger/*.yaml` for `status in
(verified, divergent)` entries with no `test_path`): confirmed `1336`, matching the CI failure
(`assert 1336 == 1337`) exactly. The manifest's own count also matches this live scan (first
assertion in the test passed) — only the hardcoded second assertion is stale.

## Scope
- `tests/tools/test_parity_index_baseline.py`: update the hardcoded `assert live_missing == 1337`
  to `assert live_missing == 1336`, with a comment addendum citing this ticket and the INFRA-118
  fix as the cause of the latest drift (matching the existing comment's format/precedent for the
  prior 1343→1337 change).

## Out of Scope
- The manifest builder / `build_manifest()` itself — untouched; its own count already matches the
  live scan (this is a hardcoded-second-assertion staleness fix, not a builder bug).
- `docs/parity_ledger/infrastructure.yaml`'s INFRA-118 entry — already correctly updated by the
  prior hotfix ticket; not re-touched here.
- The separately-failing `tests/api/test_live_health_api.py::test_live_health_api_suite[asyncio]`
  in the same CI job — per `docs/testing/regression_policy.md:62`, this test is explicitly
  documented as "Require a running server; environment-dependent; failures indicate deployment
  issues, not code regressions," and this session made no change to any code path that test
  exercises (health API navigation-stuck counter, live uvicorn subprocess). Not investigated
  further as part of this ticket; flagged to the orchestrator as a candidate CI re-run rather than
  a code fix.

## Acceptance Criteria
- [x] `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path` passes.
- [x] The live independently-recomputed `missing_test_path_count` matches both the manifest's own
      count and the updated hardcoded assertion (1336).

## Related Tickets
- TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER (caused this drift via its INFRA-118 fix)
- TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT (identical precedent pattern, 1343->1337)

## Related Docs
None requiring update — this is a single hardcoded test-baseline correction, no behavior/mechanics
change.

## Related Stored Artifacts
None (hotfix tier — no staging artifacts required).

## Related Code Areas
- `tests/tools/test_parity_index_baseline.py`

## Assumptions / Open Questions
None — mechanical, evidence-backed (live-recomputed count matches CI's exact failure value).

## Implementation Notes
Updated `live_missing == 1337` to `live_missing == 1336`, appending a comment note citing
`TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER`'s INFRA-118 `test_path` fix as the
cause, consistent with the existing comment's precedent format.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_parity_index_baseline.py -v --tb=short`

## Files Changed
- `tests/tools/test_parity_index_baseline.py` — updated hardcoded baseline 1337 -> 1336.

## Completion Summary
Updated the hardcoded `live_missing == 1337` assertion in
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
to `1336`, with a comment addendum citing `TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER`'s
INFRA-118 fix as the cause. Verified via a full local run of the file: 15/15 passed. The live
count was independently recomputed via the test's own scan logic before editing, confirming 1336
matched the real CI failure value exactly, not just the expected direction of drift.
