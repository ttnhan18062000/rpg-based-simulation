---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Ecology and Calamity Contract

**Source:** `src/world/ecology.py`, `src/world/calamity.py`, `src/world/environment.py`
**Related docs:** [docs/mechanics/05_world_evolution.md](../mechanics/05_world_evolution.md) (mechanics law parent), [threat_and_consequences_contract.md](threat_and_consequences_contract.md)

---

## Purpose

Ecology governs resource node replenishment and fauna population in world regions. Calamity is the world's emergency escalation mechanism — a forced event that resets a region's trajectory when trauma reaches critical levels. Environment applies per-tick hazard and weather effects to entities in affected regions.

---

## Ecology — `ecology.py`

### Tick cadence

Ecology runs every **200 ticks**, not every tick. This is a background maintenance process, not a real-time simulation.

### Node replenishment

Target node count per region is computed as:

```
target = int((region.area / 40_000) * (1 + region.stability))
minimum = 1
```

For each region below target, a 50% roll determines whether a node seeds this cycle. Seeding is biome-mapped:

| Biome | Node kind |
|---|---|
| FOREST | WOOD |
| MOUNTAIN | IRON |
| all others | STONE |

Nodes are seeded at the region's default resource position. They start with full charges.

### Fauna respawn

Not separately modelled in `ecology.py` — fauna (monsters, camp creatures) respawn through `spawn.py` and `camp.py`. Ecology manages only resource nodes.

---

## Calamity — `calamity.py`

### Trigger conditions

Calamity fires on **forced 5000-tick intervals**, subject to a minimum gap of **2000 ticks** between events:

1. Last calamity tick + 2000 ≤ current tick (minimum gap gate)
2. Current tick mod 5000 == 0 (forced interval gate)
3. Target region must have `intensity > 0.3`

The region with the highest calamity intensity is selected.

**Dead code note:** A `CALAMITY_RANDOM_CHANCE = 0.005` constant is defined but is not wired into any active code path. Only the forced-interval path fires calamities in the current implementation.

### Calamity effect

When triggered, a calamity:
- Spawns a `world_boss` entity at the target region centre with `difficulty_tier=4`
- Increases region `trauma_score` by a fixed increment
- Broadcasts a `CALAMITY_START` event to all entities in the region (triggers force_route_reevaluation via the world_emergence domain signal bridge)

### Calamity intensity accumulation

Hero death in a region with `hazard_level > 0.5` raises that region's `calamity_intensity` by **+0.05** per death. Intensity decays naturally if the region stabilises (no hazard deaths for many ticks).

---

## Environment — `environment.py`

Environment effects run **every tick** for entities in affected regions. These are entity-level modifiers applied before combat and movement resolution.

### Active effects

| Effect | Condition | Modification |
|---|---|---|
| Hazard drain | `region.hazard_level > 0` | HP drain proportional to hazard intensity |
| Weather multiplier | Season/weather state | Move speed ×0.7 in heavy rain/snow |
| MIASMA | Region has MIASMA flag | Stamina drain; perception range halved |
| FROST | Region has FROST flag | Move speed ×0.6; ATK×0.85 |
| HEAT | Region has HEAT flag | Stamina drain; fatigue accumulates faster |
| CURSE | Region has CURSE flag | All combat stats ×0.9 |
| Stronghold aura | Entity within stronghold radius | HP regen +2/tick if faction-aligned |

Environment effects are applied as temporary per-tick modifiers — they do not write durable EntityUpdates. The entity state snapshot used for combat/movement resolution has these applied in-place.

---

## Mutation rules

- Ecology writes new resource node records to world state (authoritative apply path via WorldObjectUpdate)
- Calamity spawns `world_boss` via the entity spawn path (authoritative)
- Environment effects are in-tick modifiers only — no durable state written
- Calamity intensity on regions is a durable world field updated via StateUpdate

---

## Regression tests

- `tests/integration/test_ecology.py` — node replenishment cadence, biome mapping, minimum count
- `tests/integration/test_calamity.py` — forced-interval trigger, world_boss spawn, intensity accumulation
- `tests/unit/test_environment.py` — hazard drain rates, MIASMA/FROST/HEAT effect application

---

## Extension rules

1. To add a new biome type: extend the biome-to-node mapping table in `ecology.py`. Minimum count guarantee must still hold.
2. To add a new environment effect: add the condition check and modifier calculation in `environment.py`. Do not write durable state — effects are per-tick snapshots only.
3. To activate `CALAMITY_RANDOM_CHANCE`: wire the constant into the calamity trigger check. This is currently dead code — enabling it changes calamity frequency significantly; update mechanics/05_world_evolution.md and add a parity ledger entry.
4. Ecology cadence (200 ticks) is configurable in world config — do not hardcode it in new code.
