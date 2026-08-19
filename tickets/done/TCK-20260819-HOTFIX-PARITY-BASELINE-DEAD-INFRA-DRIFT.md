---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT
phase: done
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT

## Title
Fix stale parity-index baseline count after TCK-20260817-DEAD-INFRA-REMOVAL-EPIC's ledger reconciliation

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on the `codebase-resilience-p0-batch` PR's "API / tools / logging" job:
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
asserts a hardcoded `missing_test_path_count` baseline (`1343`) that the test's own comment
documents as expected to drift downward whenever parity-ledger entries legitimately gain a
`test_path`. `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` did exactly that: 11
`docs/parity_ledger/infrastructure.yaml` entries moved from `verified`/`legacy_verified` to
`unsupported` (removing them from this count's `verified`/`divergent` scope entirely, since no
RabbitMQ/Kafka broker code remains to have disabled-mode behavior), and a 12th (`INFRA-174`) plus
the new `INFRA-358` both gained real `test_path` values instead of `null`. Real count is now
`1337`, confirmed by an independent live scan (`build_manifest()`'s own assertion, unchanged,
already matches).

## Scope
- Update `tests/tools/test_parity_index_baseline.py`'s hardcoded `1343` to the real, current
  `1337`, with a comment update following the file's own established precedent format (citing
  the causing ticket ID and the specific ledger change).

## Out of Scope
- Any other CI failure on the same job (two unrelated skill-invocation-staleness test failures
  are tracked separately, not caused by this or the dead-infra-removal ticket — see
  TCK-20260819-HOTFIX-SKILL-STALENESS-14DAY-GRACE-FLIP).
- Any change to `build_manifest()`/`parity_index_baseline.py` itself — only the test's hardcoded
  expectation needed updating; the manifest's own live-scan cross-check already passed unchanged.

## Acceptance Criteria
- [x] `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
      passes against the real, current parity-ledger state.
- [x] The full `tests/tools/test_parity_index_baseline.py` file still passes (no other regression).

## Related Tickets
- TCK-20260817-DEAD-INFRA-REMOVAL-EPIC (the causing ticket — its `docs/parity_ledger/infrastructure.yaml`
  reconciliation is what shifted this count)
- TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP (prior precedent for this exact same test's
  baseline-update pattern, 1347 → 1343)

## Related Docs
- None (test-only fix; no behavior change, no docs/ update required)

## Related Stored Artifacts
None (hotfix — no staging artifacts)

## Related Code Areas
- tests/tools/test_parity_index_baseline.py

## Assumptions / Open Questions
- None — the drift is fully explained and reconciled against a fresh independent live scan
  (`live_missing == 1337`, verified via direct execution before this fix, matching CI's own
  reported failure value).

## Implementation Notes
Updated `tests/tools/test_parity_index_baseline.py`'s hardcoded assertion from `1343` to `1337`
and extended the explanatory comment to name `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` as the cause
(11 entries moved to `unsupported`, `INFRA-174`/`INFRA-358` gained real `test_path`s), following
the same comment-update convention the prior `1347 → 1343` fix established in this same file.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_parity_index_baseline.py -q` → 15 passed.

## Files Changed
- `tests/tools/test_parity_index_baseline.py` — updated hardcoded baseline count and its
  explanatory comment.

## Completion Summary
Fixed the one real, in-scope CI failure on the P0 batch PR: the parity-index baseline test's
hardcoded `missing_test_path_count` expectation was stale relative to
TCK-20260817-DEAD-INFRA-REMOVAL-EPIC's own legitimate parity-ledger reconciliation. Updated
`1343` → `1337` with a comment explaining the cause, verified via a fresh independent live scan
matching CI's reported value exactly, and confirmed the full test file (15 tests) passes clean.
