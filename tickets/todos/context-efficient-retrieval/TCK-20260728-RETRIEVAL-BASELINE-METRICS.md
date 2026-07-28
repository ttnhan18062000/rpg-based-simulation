---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-BASELINE-METRICS
phase: open
date: 2026-07-28
tags: [observability]
---

# TCK-20260728-RETRIEVAL-BASELINE-METRICS

## Title
Baseline Measurement of Current Retrieval and Context-Loading Behavior

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Before any mandatory workflow changes, collect a baseline measurement period over current retrieval/context-loading behavior. Record only available, safe metadata and never synthesize unknowns; capture scenario-specific ranges for context tokens, follow-up search count, phase duration, test/gate outcome, and review rework. This produces measurement artifacts only — no workflow change.

## Scope
- Build a read-only aggregation tool/report over existing agent-monitoring/runs.jsonl, events.jsonl, tools.jsonl data
- Report context-tokens dimension explicitly marked 'unavailable' (not zero/omitted), citing docs/agent-monitoring/schema.md's platform block
- Report follow-up-search-count marked 'not_yet_instrumented' or derived only from existing tool_call_count data with the derivation cited
- Report phase-duration using a gap-aware/active-duration view if available, or visibly flag raw duration_s as pause-contaminated (never presented as clean)
- Report test/gate outcome and review-rework derived only from existing fields (final_status, reason_code, Review/Architecture-Verify status transitions), documented as a derived proxy, not fabricated
- Handle >=5-6 legacy schema generations via the existing LEGACY_COMPLETION_FIELDS pattern (legacy_reader.py), not reimplemented

## Out of Scope
- Does NOT build the ContextPacket/retrieval-event schema described in later Sequenced Future Epic phases
- Does NOT depend on or require docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md being implemented first — this ticket proceeds with an explicit raw-duration-contamination caveat if that idea has not been picked up
- No mutation of agent-monitoring/*.jsonl — strictly read-only, matching tools/agent-monitoring/manifest.py precedent
- No new mandatory workflow gate or change to how runs/events are recorded

## Acceptance Criteria
- [ ] Baseline report explicitly marks context-tokens as 'unavailable' (not zero/omitted), citing schema.md's platform block
- [ ] Follow-up-search-count is marked 'not_yet_instrumented' or derived only from existing tool_call_count data with cited computation
- [ ] Phase-duration uses a gap-aware active-duration view OR visibly flags raw duration_s as pause-contaminated, never presented as clean
- [ ] Test/gate outcome and review-rework are derived only from existing fields (final_status, reason_code, Review/Architecture-Verify status transitions), documented as derived proxy not fabricated
- [ ] Tool/report performs zero mutation of agent-monitoring/*.jsonl (read-only, matches manifest.py precedent)

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/manifest.py
- tools/agent-monitoring/legacy_reader.py
- tools/agent-monitoring/vocabulary.py
- tools/agent-monitoring/cost_proxy.py
- agent-monitoring/runs.jsonl
- agent-monitoring/events.jsonl
- agent-monitoring/tools.jsonl

## Assumptions / Open Questions
- No scenario taxonomy exists yet to bucket runs (small bugfix vs ticket implementation vs review vs architecture) — new classification work may be needed within this ticket
- Dependency-ordering resolved as: proceed now with an explicit raw-duration caveat rather than waiting on idea_agent_monitoring_active_duration.md being implemented
- tool_call_count/cost_proxy_score are only computed for the implement-ticket workflow today; create-tickets/implement-epic workflows have no sidecar data for these fields

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
