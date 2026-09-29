---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-SOCIAL-MEMORY-DECISION-CONTEXT
phase: open
date: 2026-08-22
tags: [social, observability]
---

# TCK-20260822-SOCIAL-MEMORY-DECISION-CONTEXT

## Title
Attach Same-Episode Decision Context to Social Memory Interaction Records

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Attach decision-making context to social memory relationship records so InteractionRecord can carry why a relevant decision happened, not just that an interaction occurred. Investigation confirms relationship_scores is still a bare Dict[int,float] and InteractionRecord has no decision_context field, so the underlying proposal is not stale. However, CampaignState/CampaignOrchestrator track no run_id per episode, which structurally blocks any cross-episode join against a past episode's decision_trace.jsonl -- only same-episode LIVE annotation is currently feasible, via DecisionTraceWriter's existing 1-tick _latest_goal_scores cache (top-3 goal_scores only, not the full route/risk_penalty breakdown). This ticket is scoped to that same-episode case; the run_id gap is a separate prerequisite decision, not solved here. Also noted: SocialMemoryExporter.export() currently populates interaction_history=() unconditionally -- the code comment claiming 'E43C enriches this field' is inaccurate, since E43C only shipped decay, not enrichment.

## Scope
- Add an optional decision_context field to InteractionRecord as a typed frozen sub-record (with its own to_dict()/from_dict()) defaulting to None
- Implement a same-episode LIVE join keyed by (entity_id, tick) against DecisionTraceWriter's existing 1-tick _latest_goal_scores cache
- Update SocialMemoryExporter.export() to populate decision_context best-effort when available, leaving it None otherwise
- Add round-trip tests for both a populated and an empty decision_context, following the existing interaction_record_round_trip pattern

## Out of Scope
- Solving the CampaignState/CampaignOrchestrator run_id-per-episode gap itself -- flagged as a separate prerequisite decision, not undertaken in this ticket
- Any cross-episode decision-context joining, since no run_id-per-episode mechanism exists to make it possible
- Building the sibling ring-buffer ticket's IntentionSnapshot type -- this ticket consumes DecisionTraceWriter's existing dict-shaped cache entry directly instead of depending on an unbuilt type
- Chronicle surprise-significance work (separate ticket TCK-20260822-CHRONICLE-SURPRISE-SIGNIFICANCE-TERM)
- Fixing the pre-existing field-name drift in docs/simulation/domains/social_memory_contract.md (last_seen_episode/interaction_log vs. actual last_betrayal_tick/last_cooperation_tick/interaction_history) -- worth correcting, but not required by this ticket's acceptance criteria
- Fully enriching interaction_history (still effectively empty per the stale E43C comment) beyond what decision_context itself requires

## Acceptance Criteria
- [ ] InteractionRecord gains a new optional decision_context field as a typed frozen sub-record (own to_dict()/from_dict(), per CLAUDE.md's Durable State Rule) -- not a free-form dict -- defaulting to None; existing round-trips of records without it are unchanged, verified by existing tests continuing to pass
- [ ] A populated decision_context round-trips bit-identically through to_dict()/from_dict(), following the same pattern as interaction_record_round_trip
- [ ] This ticket is scoped to same-episode LIVE annotation only, sourced from DecisionTraceWriter's existing 1-tick _latest_goal_scores cache (top-3 goal_scores, not the full route/risk_penalty breakdown); cross-episode joining is explicitly out of scope because CampaignState/CampaignOrchestrator track no run_id per episode today
- [ ] The join/enrichment step looks up decision-trace data by (entity_id, tick); when no matching entry exists, decision_context stays None rather than raising or blocking
- [ ] SocialMemoryExporter.export() continues to produce valid records whether or not decision_context is available, with zero behavior change to relationship_scores, faction_reputation, or decay for records without decision_context

## Related Tickets
- TCK-20260619-E43-SOCIAL-MEMORY
- TCK-20260619-E43A-SOCIAL-MEM-MODEL
- TCK-20260619-E43B-EXPORT-IMPORT
- TCK-20260619-E43C-DECAY
- TCK-20260619-E22A-TRACE-WRITER
- TCK-20260702-OBSISO-TRACE-ASYNC
- TCK-20260627-P1H-GOAL-RUNNERUP

## Related Docs
- docs/simulation/domains/social_memory_contract.md
- docs/architecture/observability_hot_path_safety_contract.md
- docs/plans/archive/observability_process_isolation.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/campaigns/social_memory.py
- src/domains/campaigns/state.py
- src/domains/campaigns/orchestrator.py
- src/observability/cognition/decision_trace_writer.py
- src/observability/cognition/tick_index.py

## Assumptions / Open Questions
- No IntentionSnapshot type exists yet anywhere in code; this ticket consumes the existing dict-shaped decision_trace.jsonl / DecisionTraceWriter cache entry directly rather than depending on an unbuilt type
- CampaignState/CampaignOrchestrator track no run_id per episode, structurally blocking cross-episode joins -- only same-episode live annotation is feasible for this ticket
- decision_trace.jsonl has accepted crash-loss/queue-overflow windows by design; attachment must be strictly best-effort/optional, never treated as an error on absence
- If a future design moves beyond passive post-hoc join into feeding context back into live strategic AI behavior, SimQ process-isolation constraints (docs/plans/archive/observability_process_isolation.md §4) must be reviewed first -- not applicable to this ticket's same-episode-annotation-only scope
- layer assigned as `observability` rather than a social/campaigns-specific layer, since no such layer is registered and the ticket's core mechanism (joining against DecisionTraceWriter's cache) is observability-domain; flagged here per CLAUDE.md's misc/registration guidance

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
