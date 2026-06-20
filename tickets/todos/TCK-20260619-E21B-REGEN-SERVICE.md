---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21B-REGEN-SERVICE
phase: open
date: 2026-06-20
tags: [resource-ecology, regeneration, event-emitter, phase-2]
---

# TCK-20260619-E21B-REGEN-SERVICE

## Title
Epic 2.1B · Depletion Emitter + Charge Regen Loop

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Two things are missing: (1) `RESOURCE_DEPLETED` is never emitted — the schema and consumers exist but no code fires the event. (2) `ResourceEcologyService` seeds new nodes but never regenerates charges on existing depleted nodes. This ticket wires the emitter and adds the fixed-rate regen loop.

**Requires:** TCK-20260619-E21A-NODE-SCHEMA (regen_rate_per_tick field + RESOURCE_RECOVERED enum)

## Scope

### 1. Emit `RESOURCE_DEPLETED` in the harvest apply path

**First step:** trace where `ResourceTransferIntent(source_kind="NODE")` is applied and `charges_delta` is decremented. Likely `src/engine/interaction.py` or the `ResourceTransactionResolver`. Find the exact line where `remaining_charges` is decremented to find the right injection point.

At that point, after decrementing charges: if `new_charges == 0`, create and append a `WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=state.tick, region_id=<node's region>, subject=str(node_id), severity=1.0)` to the `StateUpdate`.

### 2. Add charge regen to `ResourceEcologyService.process_ecology()`

```python
# In process_ecology(), before density seeding:
node_updates = {}
for node in state.resource_nodes.values():
    if node.regen_rate_per_tick <= 0:
        continue
    if node.remaining_charges >= node.max_charges:
        continue
    was_depleted = node.remaining_charges == 0
    new_charges = min(node.max_charges, node.remaining_charges + node.regen_rate_per_tick)
    node_updates[node.id] = ResourceNodeUpdate(node_id=node.id, charges_set=new_charges)
    if was_depleted and new_charges > 0:
        # Emit RESOURCE_RECOVERED
        events_add.append(WorldEvent(
            category=WorldEventCategory.RESOURCE_RECOVERED,
            tick=state.tick,
            region_id=<node's region>,
            subject=str(node.id),
            severity=1.0
        ))
```

Return these node_updates and events in the `StateUpdate`.

**Note:** `ECOLOGY_INTERVAL = 200` — regen only fires every 200 ticks. Set `regen_rate_per_tick` on content nodes (e.g. `regen_rate_per_tick=1`) so full recovery of a 5-charge node takes ~1000 ticks (5 ecology intervals).

### 3. Set `regen_rate_per_tick` on resource nodes in world content

In `data/content/world/` or wherever `ResourceNodeState` instances are initialized, set `regen_rate_per_tick=1` as the default for harvestable nodes (IRON, WOOD, STONE). Nodes with `regen_rate_per_tick=0` are permanent/static (no regen).

## Out of Scope
- `seasonal` and `ecology_linked` regen models (post-E21 scope)
- Changing `ECOLOGY_INTERVAL` value
- Depletion-aware scoring (E21C)

## Acceptance Criteria
- After a harvest exhausts a node's charges: `RESOURCE_DEPLETED` appears in `state.world_events` (or equivalent event log)
- After sufficient ecology ticks: `RESOURCE_RECOVERED` appears
- `remaining_charges` increases by `regen_rate_per_tick` per ecology interval (capped at `max_charges`)
- Tests in `tests/unit/world/test_resource_ecology.py` pass (see test plan)

## Related Tickets
- TCK-20260619-E21-RESOURCE-ECOLOGY (parent epic)
- TCK-20260619-E21A-NODE-SCHEMA (required first)
- TCK-20260619-E21C-SCORING-WIRE (blocked on this)
- TCK-20260619-E21D-SCARCITY-VERIFY (blocked on this)

## Related Code Areas
- `src/world/ecology.py` (ResourceEcologyService.process_ecology — add regen loop)
- `src/engine/interaction.py` (harvest apply path — add RESOURCE_DEPLETED emitter; confirm location by grep)
- `src/domains/world_emergence/schema.py` (WorldEventCategory — must import RESOURCE_RECOVERED from E21A)
- `src/core/updates.py` (StateUpdate — check if `world_events` field exists; if not, add it or use existing event list)

## Assumptions / Open Questions
- Where exactly is `charges_delta` applied? Grep `"charges_delta"` in `src/engine/` and `src/core/authoritative_pipeline.py`. The apply path is the right place to emit `RESOURCE_DEPLETED`.
- Does `StateUpdate` have a `world_events` field or similar? Check `src/core/updates.py` before adding events — use existing pattern.
- Does `ResourceNodeUpdate` support `charges_set` (absolute) or only `charges_delta` (relative)? Check `src/core/updates.py`. Use whichever is available.

## Implementation Notes
- Do not emit `RESOURCE_DEPLETED` more than once per depletion event (guard: only fire when `old_charges > 0 and new_charges == 0`).
- Do not emit `RESOURCE_RECOVERED` more than once per recovery (guard: only fire when `was_depleted and new_charges > 0`).
- `ResourceEcologyService` currently returns `StateUpdate(nodes_add=..., next_node_id_set=...)` — extend to also return `node_updates` and `events_add`.
- Run `graphify update src/` after implementation.
- Run `make knowledge-index-update` if any docs/ changed.

## Test Summary
See `staging_artifacts/TCK-20260619-E21-RESOURCE-ECOLOGY/test_plan.md` for full test list.

Key tests in `tests/unit/world/test_resource_ecology.py`:
```bash
pytest tests/unit/world/test_resource_ecology.py -x -v
pytest tests/unit/resource/ -x -v  # regression
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
