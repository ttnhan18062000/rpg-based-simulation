---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-AGENCY
phase: done
date: 2026-06-29
tags: [simq, observability, event-gap, agency, routing]
---

# TCK-20260629-SIMQ-EMIT-AGENCY

## Title
SimQ: Emit AGENCY Pillar Events from Adventure Decision Phase

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The AGENCY pillar requires `route_selected`, `action_executed`, `defer_with_reason`,
`project_started/completed/abandoned`, `commitment_abandoned`, `rejection_cascade_tick`,
`route_family_first_use`. Investigation found that `event_recorder` is NOT available in
the pipeline (both `AuthoritativeApplyPipeline.refine()` and `AdventureDecisionPhase.apply()`
are `@staticmethod` with no event_recorder param). The events feasible from state diff were
implemented: `route_selected` and `action_executed` from `EntityUpdate.property_updates`.

## Scope
Extend `EventExtractor.extract()` to emit `route_selected` and `action_executed` from
`EntityUpdate.property_updates["last_routing_family"]` set by `AdventureDecisionPhase`.

## Out of Scope
- `defer_with_reason`: DEFER path does `continue` in adventure phase — no EntityUpdate
- `rejection_cascade_tick`: requires counting DEFERs per tick across all entities
- `route_family_first_use`: requires per-entity 200-tick window state
- `commitment_abandoned`: requires strategic lifecycle tracking
- Threading `event_recorder` through pipeline (separate architectural change)
- COGNITION events: TCK-20260629-SIMQ-EMIT-COGNITION

## Acceptance Criteria
- [x] `route_selected` emitted when `last_routing_family` in EntityUpdate.property_updates
- [x] `action_executed` emitted at same condition
- [x] Neither emitted when `property_updates` has no routing family (DEFER or no decision)
- [x] Defer gap documented in test comments
- [x] Unit tests pass (9 new tests)
- [x] No import of `src/simulation_quality/` from observability layer

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite — done)
- TCK-20260629-SIMQ-EMIT-STATE-DIFF (companion — done)
- TCK-20260629-SIMQ-EMIT-COGNITION (sibling — next)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 AGENCY & ACTION
- `docs/parity_ledger/infrastructure.yaml` SIMQ-CALIBRATED-001

## Related Stored Artifacts
- `stored_artifacts/TCK-20260629-SIMQ-EMIT-AGENCY/`

## Related Code Areas
- `src/observability/event_extractor.py` — added routing event emission
- `tests/unit/observability/test_event_extractor_agency.py` — new test file

## Assumptions / Open Questions
- `event_recorder` threading into pipeline: architectural change needed for `defer_with_reason` et al.
- `StrategicProjectChanged` translation (done in E1) already covers `project_started/completed/abandoned`

## Implementation Notes
`AdventureDecisionPhase.apply()` writes `property_updates["last_routing_family"]` into
`EntityUpdate` when a non-DEFER route is committed. EventExtractor already receives the
`update: StateUpdate` object. Detection: `e_upd.property_updates.get("last_routing_family")`.
Both events use `event_category="strategy"` (matches valid SimulationEvent literals).

## Test Summary
9 new tests in `tests/unit/observability/test_event_extractor_agency.py`.
822 tests pass total (all simq + observability).

## Files Changed
- `src/observability/event_extractor.py` — added route_selected/action_executed emission block
- `tests/unit/observability/test_event_extractor_agency.py` — new (9 tests)
- `docs/parity_ledger/infrastructure.yaml` — SIMQ-CALIBRATED-001 updated with agency progress
- `staging_artifacts/TCK-20260629-SIMQ-EMIT-AGENCY/` → `stored_artifacts/`

## Completion Summary
AGENCY events `route_selected` and `action_executed` are now emitted from EventExtractor
when AdventureDecisionPhase commits a non-DEFER route. Four events (defer_with_reason,
rejection_cascade_tick, route_family_first_use, commitment_abandoned) require pipeline-level
hooks and are deferred — gap is documented in tests and investigation.md.
