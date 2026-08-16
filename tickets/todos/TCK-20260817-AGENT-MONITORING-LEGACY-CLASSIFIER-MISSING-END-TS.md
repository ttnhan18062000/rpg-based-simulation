---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-AGENT-MONITORING-LEGACY-CLASSIFIER-MISSING-END-TS
phase: open
date: 2026-08-17
tags: [observability, testing]
---

# TCK-20260817-AGENT-MONITORING-LEGACY-CLASSIFIER-MISSING-END-TS

## Title
`EPIC-TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC`'s run record has a `final_status` but no
`end_ts`, causing `test_agent_monitoring_legacy_reader.py` to misclassify it as legacy schema

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while running `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP`'s full `tests/tools`
regression sweep: `test_agent_monitoring_legacy_reader.py::test_recent_runs_records_classify_as_current_and_agree_with_validate`
fails because the real, already-committed run record for
`EPIC-TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC` in `agent-monitoring/runs.jsonl` has a
`final_status` set but no `end_ts` field, which the legacy-schema classifier flags as
`shape2_final_status_no_end_ts` (a shape the classifier expects only from genuinely old/legacy
records, not current-schema ones).

## Scope
- Determine why that specific epic-level run record was written without `end_ts` (check the
  `implement-epic` workflow's own batch-record-writing code path vs. the per-ticket
  `implement-ticket` path — this session's own hand-orchestration of `implement-epic`-shaped work
  may have omitted it).
- Decide the correct fix: append a real correction record (monitoring data is append-only — do not
  edit the historical row in place) with the missing `end_ts` backfilled from a real, defensible
  source (e.g. the epic's own closing commit timestamp), or accept this as a known, documented,
  permanent gap in that one historical record and adjust the classifier/test to tolerate it
  explicitly (with a dated, named exception) rather than silently.
- Fix (or confirm no fix needed for) the root cause so future epic-level run records don't repeat
  this gap.

## Out of Scope
- Any other pre-existing `agent-monitoring/` data-quality issue not related to this specific
  shape/record.
- Rewriting the append-only monitoring log's history.

## Acceptance Criteria
- [ ] Root cause of the missing `end_ts` is identified with real evidence (not guessed).
- [ ] A real, disclosed decision is made and implemented: backfill via a correction record, or an
      explicit, named, permanent tolerance in the classifier — not a silent test change.
- [ ] `test_agent_monitoring_legacy_reader.py::test_recent_runs_records_classify_as_current_and_agree_with_validate`
      passes.

## Related Tickets
- `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP` (found this while sweeping the `tests/tools`
  CI lane)
- `TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC` (the epic whose run record has the gap)

## Related Docs
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tests/tools/test_agent_monitoring_legacy_reader.py`
- `agent-monitoring/runs.jsonl`
- `tools/agent-monitoring/record_run.py`
- `.claude/workflows/implement-epic.js` (batch monitoring record write path)

## Assumptions / Open Questions
- Whether other epic-level run records from earlier hand-orchestrated `implement-epic` work share
  this same gap is unconfirmed — worth a quick scan before declaring this a one-off.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
