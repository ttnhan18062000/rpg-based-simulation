---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-LEGACY-READER-IN-PROGRESS-MISCLASSIFICATION
phase: done
date: 2026-08-17
tags: [agent-monitoring, bug]
---

# TCK-20260817-HOTFIX-LEGACY-READER-IN-PROGRESS-MISCLASSIFICATION

## Title
Fix `legacy_reader.py` misclassifying current-schema `final_status: "IN_PROGRESS"` run-start
records as legacy shape2, and fix the test's per-record (not per-run_id) completeness check

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Real CI failure on the "API / tools / logging" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/tools/test_agent_monitoring_legacy_reader.py::test_recent_runs_records_classify_as_current_and_agree_with_validate`
failed: `recent run_id='TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP' classified as
legacy — expected current schema`.

Root cause (confirmed via investigation): `legacy_reader.py::_classify_runs()`'s shape2 rule
(`"final_status" in record and "end_ts" not in record`) doesn't exclude the current schema's own
documented `final_status: "IN_PROGRESS"` run-start record
(`docs/agent-monitoring/schema.md`: "Run-start record written; end record not yet written...
Should not appear in completed runs"). Every `implement-ticket` run writes exactly this shape as
its start record — the flagged run_id is not special, just the first `IN_PROGRESS` record in the
test's tail-20 sample.

A second, related bug surfaced once the first was fixed: the test's own
`_record_is_complete(record)` assertion checked each sampled record individually, but
`validate.py`'s real production completeness check (`validate.py:271-276`) groups records by
`run_id` first and only flags a `run_id` as incomplete if *none* of its records are complete — a
run_id can legitimately have both an `IN_PROGRESS` start record and a later `DONE` record (this
happened for the flagged run_id: it has both). The test needed to mirror that grouping.

## Scope
- `tools/agent-monitoring/legacy_reader.py::_classify_runs()`: exclude
  `record.get("final_status") == "IN_PROGRESS"` from the shape2 rule.
- `tests/tools/test_agent_monitoring_legacy_reader.py::test_recent_runs_records_classify_as_current_and_agree_with_validate`:
  group sampled records by `run_id` before asserting `_record_is_complete`, mirroring
  `validate.py`'s own real grouping logic.

## Out of Scope
- Any other ticket in this batch.

## Acceptance Criteria
- [ ] `IN_PROGRESS` run-start records classify as current schema (empty frozenset), not legacy.
- [ ] The completeness check agrees with `validate.py`'s real, grouped semantics.
- [ ] All tests in `test_agent_monitoring_legacy_reader.py` pass.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
- `docs/agent-monitoring/schema.md` (documents `IN_PROGRESS` as a valid, expected current-schema
  value — no doc change needed, confirms the fix)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tools/agent-monitoring/legacy_reader.py`
- `tests/tools/test_agent_monitoring_legacy_reader.py`

## Implementation Notes
Added an `IN_PROGRESS` exclusion to the shape2 rule in `_classify_runs()`. Rewrote the round-trip
test to group sampled `runs.jsonl` records by `run_id` and assert `any(_record_is_complete(r) for r
in group)` per group, exactly mirroring `validate.py:271-276`'s real production logic, instead of
asserting per-record completeness.

## Test Summary
- `pytest tests/tools/test_agent_monitoring_legacy_reader.py -q`: 31 passed.

## Files Changed
- `tools/agent-monitoring/legacy_reader.py` — `_classify_runs()` shape2 rule.
- `tests/tools/test_agent_monitoring_legacy_reader.py` —
  `test_recent_runs_records_classify_as_current_and_agree_with_validate` grouping fix.

## Completion Summary
Fixed a real classifier bug (a documented, valid current-schema value was misclassified as legacy)
and a companion test bug (checking completeness per-record instead of per-run_id-group, diverging
from the real production check it claims to agree with). Both fixes are grounded directly in
`docs/agent-monitoring/schema.md` and `validate.py`'s own documented/actual semantics.
