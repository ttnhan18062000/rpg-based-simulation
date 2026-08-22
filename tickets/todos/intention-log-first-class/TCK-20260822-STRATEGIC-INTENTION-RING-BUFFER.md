---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260822-STRATEGIC-INTENTION-RING-BUFFER
phase: open
date: 2026-08-22
tags: [strategy, cognition, determinism, calibration]
---

# TCK-20260822-STRATEGIC-INTENTION-RING-BUFFER

## Title
Strategic Intention Ring Buffer for AI Decision Recall

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add an in-memory, bounded ring buffer of recent decision intentions that strategic AI can consult, matching the idea doc's unbuilt "read side". Investigation confirms this must be implemented as typed, durable StrategicComponent state following the TCK-20260812-COMMITTED-INTENTION-SEQUENCE precedent (a capped typed tuple field threaded through StrategicPatch.apply(), StateFingerprinter._strategic_identity(), and CapacityEnforcementPhase's order-preserving trim) so it participates in deterministic replay -- NOT an extension of DecisionTraceWriter's existing _latest_goal_scores cache, which is a module-singleton, 1-tick-deep, non-durable, read-only debug cache and would violate the Durable State Rule the moment strategic AI actually reads it to influence a decision. The real plug-in point is AdventureGoalScorer.score() (src/ai/goals/adventure_scorer.py:152-156), the sole live decision-trace producer since AdventureDecisionPhase was deleted. Because this changes decision behavior, SimQ anchor recalibration is a mandatory closing step, not optional.

## Scope
- Add StrategicComponent.recent_intentions: Tuple[IntentionSnapshot, ...] typed bounded field, capped at N=20 pending a memory-cost check
- Thread the field through StrategicPatch.apply(), StateFingerprinter._strategic_identity(), and CapacityEnforcementPhase's order-preserving trim, matching the committed_intentions precedent
- Wire population of the buffer into AdventureGoalScorer.score() at the same point _writer.write_trace() is currently called (src/ai/goals/adventure_scorer.py:152-156)
- Demonstrate at least one strategic-cognition decision path that actually reads/consults prior-tick buffer entries, not just populate-and-ignore
- Add a regression test proving ring size never exceeds N entries per entity after more than N ticks
- Run SimQ anchor recalibration (tools/calibrate_simq.py against grade_anchors.json) and disclose any pillar-score delta in the ticket's Completion Summary

## Out of Scope
- Chronicle surprise-significance work (separate ticket TCK-20260822-CHRONICLE-SURPRISE-SIGNIFICANCE-TERM)
- Social memory decision_context attachment (separate ticket TCK-20260822-SOCIAL-MEMORY-DECISION-CONTEXT)
- Cross-entity intention visibility -- self-entity-only buffer for this ticket; cross-entity visibility is an unresolved design question with materially different durable-state implications, not decided here
- Extending or reusing DecisionTraceWriter's _latest_goal_scores cache as the storage mechanism -- explicitly rejected per the Durable State Rule
- Locking N=20 without first running scripts/memory_probe.py to check ring-buffer-size x N-entities memory cost at scale

## Acceptance Criteria
- [ ] New typed bounded field StrategicComponent.recent_intentions (capped tuple, N=20 default) is threaded through StrategicPatch.apply(), StateFingerprinter._strategic_identity(), and CapacityEnforcementPhase's order-preserving trim -- matching the committed_intentions precedent exactly -- so it participates in deterministic replay; this is durable typed state per CLAUDE.md's Durable State Rule, explicitly not an extension of DecisionTraceWriter's cache
- [ ] AdventureGoalScorer.score() populates the buffer at the same point it currently calls _writer.write_trace(), and a strategic-cognition decision path is shown to actually consult (read, not just store) prior-tick entries
- [ ] CapacityEnforcementPhase enforces ring size never exceeds N entries per entity after more than N ticks, verified by a dedicated regression test
- [ ] SimQ anchor recalibration is re-run as a mandatory closing step per docs/plans/archive/observability_process_isolation.md §4 point 1, and any resulting pillar-score delta is disclosed in the ticket before it can move to done

## Related Tickets
- TCK-20260812-COMMITTED-INTENTION-SEQUENCE
- TCK-20260702-OBSISO-TRACE-ASYNC
- TCK-20260619-E22A-TRACE-WRITER
- TCK-20260702-OBSISO-EPIC
- TCK-20260805-COGNITION-STRATEGY-SKILL

## Related Docs
- docs/plans/archive/observability_process_isolation.md
- docs/architecture/observability_hot_path_safety_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/cognition/decision_trace_writer.py
- src/ai/goals/adventure_scorer.py
- src/systems/strategic_systems/intelligence.py
- src/core/strategic.py
- src/observability/live/entity_inspector.py
- src/engine/pipeline_phases/capacity_enforcement.py
- src/engine/patches.py
- src/replay/fingerprint.py
- src/observability/cognition/tick_index.py
- src/api/routes/decisions.py

## Assumptions / Open Questions
- Ring buffer size x N entities memory cost at scale is unmeasured; must be checked with scripts/memory_probe.py before locking N=20
- Self-only vs cross-entity intention visibility is unresolved and has materially different durable-state design implications; must be decided before implementation but is not this ticket's default
- SimQ's 25-anchor calibration corpus lock requires re-verification and will likely shift pillar grades -- treated as mandatory, not optional
- AdventureGoalScorer.score() is reached unconditionally every tick for every eligible entity, so buffer-write logic must stay allocation-cheap (append+trim, no per-write IO)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
