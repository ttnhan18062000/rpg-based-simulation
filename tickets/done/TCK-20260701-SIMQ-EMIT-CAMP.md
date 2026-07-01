---
status: closed
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-CAMP
phase: done
date: 2026-07-01
tags: [simq, event-emission, world-dynamics, camp, scoring, infrastructure]
---

# TCK-20260701-SIMQ-EMIT-CAMP

## Title
Wire camp_constructed emitter: add event recorder to CampService

## Status
DONE — CLOSED, WRONG PREMISE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`camp_constructed` is a WorldDynamicsScorer event type (+1 `persistent_structure` signal)
that cannot be emitted because `CampService` (or `src/world/camp.py`) has no event recorder
interface. Camp construction produces a durable state change (camp entity added to world),
but the service that handles it has no way to emit a `SimulationEvent`.

This was identified during `TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS` and left blocked.

## Scope
1. Investigate `src/world/camp.py` — find where camp construction is finalized (entity
   created and committed to StateUpdate).
2. Add an optional `event_recorder: Optional[EventRecorder]` parameter to `CampService`
   or its construction call site without breaking existing callers.
3. After a camp entity is added to the StateUpdate, emit:
   ```python
   SimulationEvent(
       event_type="camp_constructed",
       event_category="lifecycle",
       entity_id=camp_entity.id,
       payload={"camp_id": camp_entity.id, "region_id": region_id, "tick": tick},
   )
   ```
4. Wire the recorder at the pipeline phase that calls CampService (likely PP-14 or WD-14).
5. Unit tests: camp construction fires exactly one `camp_constructed` event.

## Out of Scope
- Changing the camp entity schema
- Modifying WorldDynamicsScorer weights
- Camp destruction / lifecycle events

## Acceptance Criteria
- [ ] `camp_constructed` emitted whenever a new camp entity is created
- [ ] Event reaches WorldDynamicsScorer (verified via unit test)
- [ ] No regression in existing camp/world tests
- [ ] `event_type_coverage.md §3.9` updated — `camp_constructed` row removed

## Related Tickets
- TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS — identified the block
- TCK-20260628-SIMQ-EPIC — parent epic

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.9`
- `docs/simulation_quality/quality_scoring_contract.md §5 WORLD DYNAMICS`

## Related Code Areas
- `src/world/camp.py` — CampService construction call
- `src/observability/event_recorder.py` — EventRecorder interface
- `src/engine/pipeline_phases/` — pipeline phase that calls CampService (WD-14)

## Assumptions / Open Questions
- Confirm whether CampService is called once per tick or once per camp placement.
  If per-placement, a single recorder injection suffices. If called every tick to
  process queued requests, confirm which call corresponds to actual construction.
- Confirm `region_id` is available at the point of camp entity creation.

## Test Summary
- Unit: CampService creates camp → `camp_constructed` event emitted
- Unit: no event when recorder is None
- Unit: payload contains camp_id and region_id

## Files Changed
(to be filled at implementation)

## Completion Summary
**Closed — premise incorrect, no viable engine path.**

Investigation (2026-07-01) found:
- `StateUpdate` has no `camps_add` field — only `camp_updates: Dict[str, CampUpdate]`
- `CampUpdate` only supports: `maturity_delta`, `active_set`, `last_raid_tick_set` — no construction
- `CampService.process_camps()` only evolves existing camps (maturity, monster spawns, raids)
- Camps are pre-placed at world generation; no dynamic camp construction occurs during simulation ticks

The ticket assumed "CampService has no event recorder" but the real issue is deeper: there is
no camp construction mechanic in the simulation at all. Adding an event recorder to CampService
would not fix this — the code path that creates new camps does not exist.

Implementing `camp_constructed` requires first adding a camp placement mechanic (new entity
action, world event, or pipeline phase that creates `CampState` entries dynamically). That is a
gameplay feature, not a SimQ wiring task. Closing this ticket; if camp placement is added in the
future, create a new SimQ emit ticket at that time.
