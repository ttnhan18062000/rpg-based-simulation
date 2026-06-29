---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-AGENCY
phase: open
date: 2026-06-29
tags: [simq, observability, event-gap, agency, routing]
---

# TCK-20260629-SIMQ-EMIT-AGENCY

## Title
SimQ: Emit AGENCY Pillar Events from Adventure Decision and Action Routing Phases

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The AGENCY pillar scores 9 event types (`action_executed`, `route_selected`,
`defer_with_reason`, `project_started`, `project_completed`, `project_abandoned`,
`commitment_abandoned`, `rejection_cascade_tick`, `route_family_first_use`) — none of
which are currently emitted by the engine. These events require hooks in the adventure
decision (PP-12) and action routing (PP-13/14/15) phases, not state diff extraction.

## Scope
Add `EventRecorder.record()` calls in the engine phases PP-12 through PP-15.
Locate the relevant phase implementations and add emission at the decision/dispatch sites.

**Events to emit and their source sites:**

| Event type | Emission site |
|---|---|
| `action_executed` | PP-13 action routing: after a non-DEFER action resolves successfully |
| `defer_with_reason` | PP-13: when a DEFER_WITH_REASON action is produced for an entity |
| `route_selected` | PP-14/15: when a navigation route is committed for an entity |
| `route_family_first_use` | PP-14/15: when a route family is used for the first time in a 200-tick window (requires per-entity window tracking) |
| `rejection_cascade_tick` | PP-13: when the count of DEFERs population-wide exceeds 100 in a tick |
| `commitment_abandoned` | PP-12: when an active commitment is dropped before completion |

Note: `project_started`, `project_completed`, `project_abandoned` are partially covered by
the translation layer (TCK-20260629-SIMQ-EVENT-TRANSLATE maps `StrategicProjectChanged`).
Do NOT re-emit them here — only add what the translation layer cannot cover.

**Payload requirements per event:**

- `action_executed`: `{"action_type": str, "entity_id": int, "tick": int}`
- `defer_with_reason`: `{"reason": str, "entity_id": int, "consecutive_defers": int}`
- `route_selected`: `{"route_family": str, "destination_region_id": str, "entity_id": int}`
- `route_family_first_use`: `{"route_family": str, "entity_id": int, "window_tick": int}`
- `rejection_cascade_tick`: `{"defer_count": int, "tick": int}`
- `commitment_abandoned`: `{"commitment_id": str, "entity_id": int, "reason": str}`

**Architecture constraint:** `src/simulation_quality/` must NOT be imported from engine
phases. Pass `event_recorder` as an existing dependency — it is already threaded through
kernel to phases via `event_recorder=self._event_recorder` (see `kernel.py:840`).

## Out of Scope
- COGNITION events (belief, lead certainty): TCK-20260629-SIMQ-EMIT-COGNITION
- Changing existing DEFER logic or routing decisions (emit only, no behavior change)
- `population_stasis` detection (that is a scorer-level aggregate, not an event)

## Acceptance Criteria
- [ ] `action_executed` emitted on every successful non-DEFER action in PP-13
- [ ] `defer_with_reason` emitted with `consecutive_defers` count per entity
- [ ] `route_selected` emitted when navigation route committed in PP-14/PP-15
- [ ] `rejection_cascade_tick` emitted when population DEFER count > 100
- [ ] `commitment_abandoned` emitted when active commitment is dropped
- [ ] No import of `src/simulation_quality/` from any engine phase
- [ ] Events carry the correct payloads as specified above
- [ ] Unit tests mock the relevant phase and assert events are recorded
- [ ] Running `tools/calibrate_simq.py --ticks 200 --seed 42` shows non-zero AGENCY events
- [ ] AGENCY pillar grade is something other than C (default) after 200 ticks

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite)
- TCK-20260629-SIMQ-EMIT-STATE-DIFF (companion ticket for state-diff events)
- TCK-20260629-SIMQ-EMIT-COGNITION (sibling — cognition phase hooks)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 AGENCY & ACTION
- `docs/engine/kernel.md` — phase execution order

## Related Code Areas
- Engine phases PP-12 through PP-15 (adventure_decision, action_routing, position_swaps, movement_routing)
- `src/engine/kernel.py` — event_recorder is threaded to phases at L840
- `src/observability/events.py` — may need new SimulationEvent subclasses for new types

## Assumptions / Open Questions
- PP-12/13/14/15 are concrete phase classes discoverable via `graphify query "adventure_decision action_routing"`
- `event_recorder` is available in each phase's `execute()` signature or accessible via context
- DEFER_WITH_REASON is a distinct action type (not the same as DEFER) — verify in action routing source
- `route_family` is a string label on the route decision output — verify field name before implementing
