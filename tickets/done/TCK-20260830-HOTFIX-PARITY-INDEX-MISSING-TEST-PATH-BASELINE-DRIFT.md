---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT
phase: open
date: 2026-08-30
tags: [testing, calibration]
---

# TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT

## Title
Update `test_baseline_manifest_does_not_coerce_missing_test_path`'s Hardcoded `live_missing`
Baseline (1332 → 1322)

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
asserts the manifest's `missing_evidence_health.missing_test_path_count` matches a fresh live scan
(this assertion passes), then separately asserts the live count equals a hardcoded `1332` (this
assertion fails: actual is `1322`). The test's own comment history documents this exact,
recurring, expected drift pattern — the count naturally moves downward whenever a legitimate
ticket adds a real `test_path` to a previously-`test_path: null` entry, and the file's own
convention is to update the hardcoded number with a dated evidence comment each time, never
silently.

This session's own work (numerous tickets adding new parity entries with real `test_path`s —
e.g. `PROG-121`, `INFRA-397`, `INFRA-398`, `INFRA-399`, `WORLD-117`, `SOC-245`'s cooldown
`v2_evidence` update, and others across the M1 batch and its follow-ups) plausibly accounts for
the 10-entry drop. Independently verified: a fresh live scan of `docs/parity_ledger/*.yaml`
confirms the count is genuinely `1322` today, matching the manifest.

## Scope
- Update the hardcoded `1332` to `1322` in `tests/tools/test_parity_index_baseline.py`.
- Append a dated evidence comment to the existing comment chain above the assertion, following
  the file's own established convention (cite the session/date; do not need to enumerate every
  individual contributing ticket if there were many — a summary reference is consistent with how
  prior drift entries were recorded).

## Out of Scope
- Any other baseline/manifest value in this file.
- Investigating individual parity entries for correctness — this is a pure count re-sync.

## Acceptance Criteria
- `test_baseline_manifest_does_not_coerce_missing_test_path` passes.
- The comment chain is updated with a dated entry, not just the bare number changed.

## Related Docs
- tests/tools/test_parity_index_baseline.py (own comment history documents this pattern)

## Related Code Areas
- tests/tools/test_parity_index_baseline.py

## Assumptions / Open Questions
None.

## Implementation Notes
Verified live-missing count via direct scan of docs/parity_ledger/*.yaml: 1322, matches
build_manifest()'s own computed value (first assertion in the test already passes). Updating the
hardcoded comparison value to match.

## Test Summary
tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path
passes after the update.

## Files Changed
tests/tools/test_parity_index_baseline.py

## Completion Summary
Hardcoded baseline updated 1332 -> 1322 with a dated evidence comment, matching the file's
established drift-documentation convention. No production code changed.
