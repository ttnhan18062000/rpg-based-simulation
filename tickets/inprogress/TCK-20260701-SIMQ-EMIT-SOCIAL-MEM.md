---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-SOCIAL-MEM
phase: open
date: 2026-07-01
tags: [simq, event-emission, social, scoring, infrastructure]
---

# TCK-20260701-SIMQ-EMIT-SOCIAL-MEM

## Title
Wire social_memory_created emitter: add event recorder to SocialMemoryExporter

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`social_memory_created` is a SocialScorer event type (+2 `relationship_depth` signal)
that the engine cannot emit because `SocialMemoryExporter.export()` has no event recorder
interface. The social memory system writes to the timeline buffer but there is no path to
emit a `SimulationEvent` at the point of creation.

This was identified during the simq-emit epic (TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY)
and left blocked. It is the higher-priority of the two remaining §3.8 gaps because
`social_memory_created` fires every time a relationship is durably recorded — a rich
signal for relationship depth.

## Scope
1. Investigate `src/domains/social/` or `src/systems/social/` — find `SocialMemoryExporter`
   and `SocialMemoryRecord`; confirm where `export()` is called from.
2. Add an optional `event_recorder: Optional[EventRecorder]` parameter to
   `SocialMemoryExporter` (or its caller) without breaking existing callers.
3. In `export()`, after the memory is written to the timeline buffer, emit:
   ```python
   SimulationEvent(
       event_type="social_memory_created",
       event_category="social",
       entity_id=memory.entity_id,
       payload={"memory_type": memory.memory_type, "subject_id": memory.subject_id},
   )
   ```
4. Wire the recorder into the call site (likely a pipeline phase or domain system).
5. Add unit tests: memory creation fires exactly one `social_memory_created` event with
   correct payload fields.

## Out of Scope
- Changing the SocialMemoryRecord schema
- Modifying SocialScorer weights

## Acceptance Criteria
- [ ] `social_memory_created` emitted whenever a social memory record is written
- [ ] Event reaches SocialScorer (verified via unit test)
- [ ] No regression in existing social/cooperation tests
- [ ] `event_type_coverage.md §3.8` updated — `social_memory_created` row removed

## Related Tickets
- TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY — identified the block
- TCK-20260628-SIMQ-EPIC — parent epic

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.8`
- `docs/simulation_quality/quality_scoring_contract.md §5 SOCIAL`

## Related Code Areas
- `src/domains/social/` or `src/systems/social/` — SocialMemoryExporter
- `src/observability/event_recorder.py` — EventRecorder interface

## Assumptions / Open Questions
- Confirm whether `SocialMemoryExporter` is instantiated per-tick or once at startup.
  If per-tick, the recorder can be passed directly; if singleton, it needs an
  `attach_recorder()` method.
- Confirm `memory_type` and `subject_id` are fields on `SocialMemoryRecord`.

## Test Summary
- Unit: create a SocialMemoryRecord → assert `social_memory_created` event emitted
- Unit: payload contains `memory_type` and `subject_id`
- Unit: no event fired when recorder is None (backwards compat)

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
