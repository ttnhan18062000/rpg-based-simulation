---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-COST-PROXY-EPIC-TICKETS
phase: open
date: 2026-09-04
tags: [ai, agent-monitoring]
---

# TCK-20260904-COST-PROXY-EPIC-TICKETS

## Title
Extend cost proxy scoring to epic and ticket-creation workflows

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Only implement-ticket.js currently emits cost_proxy_score/tool_call_count; implement-epic.js and create-tickets.js report null for both, and the proposal framed this as simply wiring the existing tools/agent-monitoring/cost_proxy.py computation into two more call sites — "the same computation, two more call sites, no new logic." Investigation found this significantly understates the real work: implement-epic.js and create-tickets.js never register a .claude/current_run sidecar per agent() call in the first place, which is documented as a DELIBERATE prior exclusion from TCK-20260719-COST-PROXY-WRITE-PATH (with an existing regression test asserting the no-sidecar behavior). This ticket is therefore a deliberate scope reversal of that earlier decision — real work requires adding sidecar-writing calls at ~9 call sites across the two files plus widening record_events.py's hardcoded workflow filter, not just relaxing one filter.

## Scope
- Add orchestrator-side sidecar-writing bash() calls (mirroring implement-ticket.js's writeSidecar(seq, phase, agent) pattern) at every agent() call site in implement-epic.js (lines 86, 287, 316, 353, 796, 818) and create-tickets.js (lines 131, 156, 439)
- Handle implement-epic.js's 2 non-standard fire-and-forget record_events.py calls (hardcoded seq:1, lines 189, 215) case-by-case since they don't fit a straight copy of the writeSidecar(seq) pattern
- Widen tools/agent-monitoring/record_events.py::compute_tool_stats()'s hardcoded infer_workflow(run_id) == "implement-ticket" filter to a set/membership check covering implement-epic ('EPIC-'/'FOLDER-' prefixes) and create-tickets ('CREATE-TICKETS-' prefix) per tools/agent-monitoring/vocabulary.py::infer_workflow()
- Update tests/tools/test_record_events.py::test_implement_epic_and_create_tickets_records_unaffected_no_sidecar to assert non-null values, with a corrected docstring/comment reflecting the reversed design decision
- State explicitly in the ticket that this reverses TCK-20260719-COST-PROXY-WRITE-PATH's declared Out-of-Scope decision, with rationale for why

## Out of Scope
- Backfilling already-written null rows for past runs, including the runs that created earlier tickets in this same batch — historical rows stay null, only future runs after this ships show non-null values
- tests/tools/test_cost_proxy.py's formula/computation logic — unaffected by this change
- Redesigning record_events.py's rule that it always overrides caller-supplied tool_call_count/cost_proxy_score at write time — must extend that rule identically to the two newly-covered workflows, not change it

## Acceptance Criteria
- [ ] After adding sidecar registration at every agent() call site in both files plus widening the filter, a real implement-epic run's events.jsonl rows have non-null tool_call_count/cost_proxy_score matching the real (run_id,seq)-grouped tools.jsonl rows
- [ ] A real create-tickets run likewise produces non-null values
- [ ] test_implement_epic_and_create_tickets_records_unaffected_no_sidecar is updated (not left contradicting) to assert non-null values with a corrected docstring/comment reflecting the reversed design decision
- [ ] A mixed-batch test confirms implement-ticket/implement-epic/create-tickets buckets compute independently without cross-contamination

## Related Tickets
- TCK-20260708-AGENT-COST-OBSERVABILITY
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260719-COST-PROXY-WRITE-PATH
- TCK-20260719-LIVE-PHASE-AGENT-LABEL
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY

## Related Docs
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/cost_proxy.py
- tools/agent-monitoring/record_events.py
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- .claude/workflows/create-tickets.js
- docs/agent-monitoring/schema.md
- tests/tools/test_record_events.py
- tests/tools/test_cost_proxy.py

## Assumptions / Open Questions
- This is a deliberate reversal of TCK-20260719-COST-PROXY-WRITE-PATH's explicit prior exclusion and must be documented as such in the ticket, not treated as an unnoticed oversight
- The 2 non-standard fire-and-forget call sites in implement-epic.js need individualized handling rather than a straight copy of the writeSidecar(seq) pattern
- Both the sidecar-coverage addition and the record_events.py filter-widening are required together — shipping either alone produces no visible effect

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
