---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-AGENCY
artifact_type: plan
tags: [simq, agency, event-extractor]
---

# Plan: TCK-20260629-SIMQ-EMIT-AGENCY

## Constraint

`event_recorder` is NOT available in the pipeline or adventure phase — both are static.
All agency events will be derived from `StateUpdate.entity_updates[eid].property_updates`
which is already passed into `EventExtractor.extract(prior_state, current_state, update, mode)`.

## Ordered Steps

1. In `EventExtractor.extract()` entity loop — after the resource-node section, inside
   the entity loop (after XP/level-up, before quest loop):
   
   a. Emit `route_selected` — if `entity_upd.property_updates.get("last_routing_family")`.
      Get `e_upd = update.entity_updates.get(eid)` (already pattern used in the file).
      Emit `SimulationEvent(event_type="route_selected", event_category="agency", ...)`.
      Payload: `{"family": family, "score": entity_upd.property_updates.get("last_routing_score")}`.
      Note: "last_routing_score" may not be set — store None if absent.
   
   b. Emit `action_executed` at the same condition — any non-DEFER route committed = action.
      Payload: `{"family": family}`.

2. Write new tests in `tests/unit/observability/test_event_extractor_agency.py`.

## Scope Guards

- Do NOT emit `defer_with_reason` — DEFER path writes no EntityUpdate; impossible from update.
- Do NOT modify `AdventureDecisionPhase`, `pipeline.py`, or `kernel.py`.
- Do NOT add volumization guards — calibration needs them always.
- `property_updates` may be absent or empty on EntityUpdate — guard with `.get()`.

## Acceptance Criteria → Steps

- `route_selected` emitted when `property_updates["last_routing_family"]` set → step 1a
- `action_executed` emitted at same condition → step 1b  
- Neither emitted when `property_updates` has no `last_routing_family` → tests
- Tests document the defer gap explicitly → test_event_extractor_agency.py
