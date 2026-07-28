---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-RETENTION-REDACTION
phase: open
date: 2026-07-28
tags: [ai, observability, agent-monitoring]
---

# TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Title
Define Retention and Redaction Policy for Retrieval Events and Cache Entries

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants a decision document resolving Open Decision 4: what retention and redaction policy applies to retrieval events and cache entries, consistent with the source doc's risk mitigation that telemetry must store only hashes, IDs, counts, and reason codes — never raw prompts or retrieved chunks. This matters because there is no existing "redaction" convention anywhere in the repo outside the Phase 2 planning docs, and getting this wrong risks durable-state that leaks raw prompt/content data through cache or event telemetry.

## Scope
- Author a decision document (expected: docs/observability/retrieval_retention_redaction_policy.md) enumerating fields a retrieval event/cache entry MAY contain (hashes, IDs, counts, reason codes, scores) vs PROHIBITED fields (raw prompt text, raw retrieved chunk/source text, unredacted tool payloads).
- Resolve Open Decision 4 with a cited answer.
- Specify a concrete retention duration/category for each of the 3 cache levels (embedding/index cache, query-result cache, context-packet cache) plus retrieval events themselves, explicitly extending src/observability/reporting/retention.py's RetentionPolicy categories (recent_run=7d, important_failed_run=30d, baseline_source_run=~permanent).
- Update the parent epic's Open Decision 4 line item to cross-reference the new decision doc once it lands.

## Out of Scope
- Any changes to src/observability/reporting/retention.py, src/core/retention.py, or any tools/agent-monitoring/*.py writer — decision-only, no code lands.
- Any src/ or tools/ implementation.
- Phase 3 retrieval/cache implementation.
- Phase 4 observability events/dashboard work.
- Phase 5-6 shadow packets or workflow adoption.
- Force-resolving any Open Decision other than Decision 4.

## Acceptance Criteria
- [ ] Written decision doc enumerates MAY-contain fields (hashes, IDs, counts, reason codes, scores) vs PROHIBITED fields (raw prompt text, raw retrieved chunk/source text, unredacted tool payloads), resolving Open Decision 4 with a cited answer.
- [ ] Doc specifies a concrete retention duration/category for each of the 3 cache levels (embedding/index cache, query-result cache, context-packet cache) plus retrieval events, explicitly extending retention.py's RetentionPolicy categories.
- [ ] Doc declares itself decision-only: no changes land in retention.py, core/retention.py, or any tools/agent-monitoring/*.py writer.
- [ ] Parent epic's Open Decision 4 line item is updated to cross-reference the new decision doc once it lands.

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-EVAL-FIXTURE-REPAIR
- TCK-20260721-MONITORING-WRITER-DECISION

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- docs/observability/loki_label_policy.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- src/observability/reporting/retention.py
- src/core/retention.py
- docs/observability/loki_label_policy.md
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md
- tickets/todos/context-efficient-retrieval/SEQUENCE.md
- expected: docs/observability/retrieval_retention_redaction_policy.md

## Assumptions / Open Questions
- No prior "redaction" convention exists anywhere in the repo outside the two Phase 2 planning docs — this ticket establishes new vocabulary even while reusing retention.py's duration/lifecycle pattern.
- The 3 differently-keyed/invalidated cache levels need per-level treatment, not one blanket policy.
- Exact doc location/filename is not prescribed by the source plan; docs/observability/retrieval_retention_redaction_policy.md is a working suggestion for the ticket's Plan phase, not a mandate.
- Whether this ticket should be standalone or bundled with siblings was flagged in investigation; TCK-20260721-MONITORING-WRITER-DECISION's precedent of bundling two decisions into one ticket exists as an alternative, but this batch keeps it standalone per the default one-concern-one-ticket rule.
- Tier is standard rather than hotfix because assigning concrete retention categories and a new redaction vocabulary across 3 cache levels plus events is policy-design work with privacy/security implications, not mere citation of already-produced evidence.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
