---
ticket_id: TCK-20260619-E21-RESOURCE-ECOLOGY
phase: investigation
date: 2026-06-20
---

# Investigation: Resource Ecology Regeneration

## Current State (verified 2026-06-20)

### ResourceNodeState — `src/core/state.py:L808`
Already has:
- `remaining_charges: int` (current charges — depletes on harvest)
- `max_charges: int`
- `required_ticks: int` (harvest duration)
- `respawn_cooldown: int = 100` (ticks until respawn after depletion — node-level reset)
- `cooldown_remaining: int = 0` (countdown decrement in HarvestSystem)

**Missing:** `regen_rate_per_tick: int = 0` — no per-tick charge regeneration field exists.

### HarvestSystem — `src/systems/world_systems/harvesting.py`
- Checks `node.remaining_charges <= 0` to abort harvest (L26)
- Creates `ResourceTransferIntent(source_kind="NODE", items_add=[...], transfer_kind="HARVEST")` on completion (L51)
- Decrements `cooldown_remaining` per tick (L66-L79)
- Does NOT emit `RESOURCE_DEPLETED` event when charges reach 0
- `charges_delta` is set in `ResourceNodeUpdate` by the apply path, not here

### ResourceEcologyService — `src/world/ecology.py:L11`
- Runs every 200 ticks (`ECOLOGY_INTERVAL = 200`)
- Seeds **new nodes** when region density < target
- Does NOT regen charges on existing depleted nodes

### Event Schema — `src/domains/world_emergence/schema.py:L12`
`WorldEventCategory.RESOURCE_DEPLETED = "RESOURCE_DEPLETED"` exists (L16).
`resource_recovered` does NOT exist — must be added to `WorldEventCategory`.

### Existing Consumers (ready, just need emitter)
- `src/domains/world_emergence/models.py:L100` — `RESOURCE_DEPLETED` triggers scarcity aggregation
- `src/domains/world_emergence/models.py:L164` — `RESOURCE_DEPLETED` used in `RegionalPressureModel`
- `src/domains/campaigns/behavior_change.py:L97` — behavior trigger on `"resource_depleted"`
- `src/domains/optimization/cache_strategy.py:L41` — cache invalidation on `resource_depleted`

### AdventureRouteScorer — `src/domains/adventure/scoring.py`
No depletion-aware scoring. `expected_benefit` is computed independently of node charge state.

### RegionalPressureModel — `src/domains/world_emergence/models.py:L14`
Already the right hook for ecology-linked regen rate modulation.

## Gap Summary

| Gap | File | Size |
|---|---|---|
| `regen_rate_per_tick` field missing from `ResourceNodeState` | `src/core/state.py` | 1 field |
| `resource_recovered` event kind missing | `src/domains/world_emergence/schema.py` | 1 enum value |
| `RESOURCE_DEPLETED` never emitted | harvest apply path | ~10 lines |
| Charge regen logic missing | `src/world/ecology.py` | ~30 lines |
| Depletion-aware scoring missing | `src/domains/adventure/scoring.py` | ~15 lines |

## Risk

- `ResourceNodeState` is `frozen=True, slots=True` — adding a field is safe but existing callers that construct `ResourceNodeState(...)` with positional args may need default values (use `regen_rate_per_tick: int = 0` default).
- The apply path for `ResourceTransferIntent(source_kind="NODE")` must be traced to find where `charges_delta` is applied — that's the right place to emit `RESOURCE_DEPLETED`.
