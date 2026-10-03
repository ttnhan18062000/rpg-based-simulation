---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-AGENCY
artifact_type: investigation
tags: [simq, agency, adventure-phase, event-emission]
---

# Investigation: TCK-20260629-SIMQ-EMIT-AGENCY

## Architecture finding: event_recorder NOT available in pipeline

`AuthoritativeApplyPipeline.refine()` is a `@staticmethod` with no `event_recorder` param.
`AdventureDecisionPhase.apply()` is also a `@staticmethod`. Kernel calls:
  `AuthoritativeApplyPipeline.refine(self._state, raw_update, cadence=..., force_full_scan=...)`
No event_recorder is threaded. Adding it would require touching kernel.py + pipeline.py.

## Detectable from StateUpdate (no phase hooks needed)

`AdventureDecisionPhase.apply()` writes to `EntityUpdate.property_updates`:
  `{"last_routing_tick": tick, "last_routing_family": result.selected.family.value}`

`EventExtractor.extract()` already receives `update: StateUpdate`. We can detect:
- **`route_selected`**: `update.entity_updates[eid].property_updates.get("last_routing_family")` is set
- **`action_executed`**: same condition — any non-DEFER selection = meaningful action taken

DEFERs (DEFER_WITH_REASON) cause `continue` in the adventure phase — NO EntityUpdate created.
So DEFER decisions are invisible to state diff + update.

## Events feasible via EventExtractor (this ticket)

| Event | Method | Availability |
|---|---|---|
| `route_selected` | `update.entity_updates[eid].property_updates["last_routing_family"]` | ✓ |
| `action_executed` | Same — non-DEFER route family committed | ✓ |

## Events requiring phase hooks (NOT in this ticket)

| Event | Blocker |
|---|---|
| `defer_with_reason` | DEFER path does `continue`; no EntityUpdate; invisible to extractor |
| `rejection_cascade_tick` | Requires counting DEFERs per tick — no aggregate in update |
| `route_family_first_use` | Requires per-entity 200-tick window state not in extractor |
| `commitment_abandoned` | Requires strategic lifecycle tracking (already partially via StrategicProjectChanged) |

Note: `project_started`, `project_completed`, `project_abandoned` are already covered by
translation of `StrategicProjectChanged` (TCK-20260629-SIMQ-EVENT-TRANSLATE).

## Parity overlap

SIMQ-CALIBRATED-001 — partial, will show AGENCY non-zero events after this ticket.
