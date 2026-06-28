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

Nodes are seeded at the region's default resource position. They start with full charges. Ecology-seeded nodes are assigned `regen_rate_per_tick=1` at creation. Compiler-seeded nodes also default to `regen_rate_per_tick=1` (via `ResourceNodeSpec.regen_rate` default=1, wired in `compiler.py`). World authors may set `regen_rate: 0` in the world spec for intentionally static (non-regenerating) nodes.

### Charge regeneration

Each ecology cycle also regenerates charges on existing depleted or partially-depleted nodes. The regen loop runs **before** density seeding in `process_ecology()`.

**Rules:**
- A node is eligible if `regen_rate_per_tick > 0`, `remaining_charges < max_charges`, and `cooldown_remaining == 0`.
- Nodes in cooldown (`cooldown_remaining > 0`) are skipped — the cooldown-recharge path in `world_dynamics.py` owns those nodes.
- `charges_delta = min(max_charges, remaining_charges + regen_rate_per_tick) - remaining_charges` (always positive; capped at max).
- With the default `regen_rate_per_tick=1` and `max_charges=5`, a fully depleted ecology-seeded node recovers in 5 ecology intervals (~1000 ticks).

**Events emitted:**
- `RESOURCE_DEPLETED` (`WorldEventCategory.RESOURCE_DEPLETED`): emitted by `economy.py:_apply_world_effects()` when an accepted harvest reduces a node's `remaining_charges` from `> 0` to `<= 0`. Guard: only fires once per depletion (`old_charges > 0 and new_charges <= 0`).
- `RESOURCE_RECOVERED` (`WorldEventCategory.RESOURCE_RECOVERED`): emitted by `ecology.py:process_ecology()` when the regen loop brings a fully-depleted node (`remaining_charges == 0`) above zero. Guard: only fires when `was_depleted and delta > 0`.

Both events are carried via `StateUpdate.world_events_add` and accumulated on `AuthoritativeState.recent_world_events` (rolling window of 500 events) by `ApplyPath.apply_generation()`. The `WorldEmergencePhase` in `pipeline.py` reads `recent_world_events` from state.

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

- Ecology writes new resource node records and regen node updates to world state (authoritative apply path via `StateUpdate.nodes_add` and `StateUpdate.node_updates`)
- Calamity spawns `world_boss` via the entity spawn path (authoritative)
- Environment effects are in-tick modifiers only — no durable state written
- Calamity intensity on regions is a durable world field updated via StateUpdate

---

## Regression tests

- `tests/unit/world/test_resource_ecology.py` — regen loop (charges_delta, cap, cooldown guard, rate guard), RESOURCE_DEPLETED emitter, RESOURCE_RECOVERED emitter, parity guards (TCK-20260619-E21B)
- `tests/integration/world/test_long_run_stability.py` — node replenishment cadence, biome mapping, minimum count
- `tests/certification/test_cert_long_run_stability.py` — forced-interval trigger, world_boss spawn, intensity accumulation
- `tests/unit/world/test_interaction_system.py` — hazard drain rates, MIASMA/FROST/HEAT effect application

---

## Population Density Demand Signal (E52D)

The population density signal is the feedback path from the demographic cohort model into the regional pressure system. It is computed by `RegionalPressureModel.evaluate()` in `src/domains/world_emergence/models.py`.

### Formula

```
population_density = total_cohort_count / max(1, region_area)
demand_multiplier  = 1.0 + (population_density * 0.5)
```

where `region_area = (xmax - xmin) * (ymax - ymin)` derived from `RegionState.bounds`.

### Effect

Multiplied against the base resource pressure intensity whenever a region has harvesting or depletion events:

```
res_intensity = min(1.0, (harv_cnt * 0.05 + dep_cnt * 0.15) * demand_multiplier)
```

### Traceability

The `demand_multiplier` value is recorded in `RegionalPressure.source_aggregates` as `density_mult:<value>` and in `reason` for observability.

### Zero-population behaviour

If a region has no cohorts (empty `population_cohorts` dict), `compute_population_density()` returns `0.0`, and `demand_multiplier` is exactly `1.0` (no amplification). This is backward-compatible with regions that have not yet received demographic data.

### Source

- `src/domains/demographics/cohort.py` — `compute_population_density(region)`
- `src/domains/world_emergence/models.py` — `RegionalPressureModel.evaluate()` resource pressure section
- Parity ledger entry: `WORLD-DEMO-005` in `docs/parity_ledger/world_dynamics.yaml`
- Full contract: `docs/world/demographics_contract.md`

---

## Extension rules

1. To add a new biome type: extend the biome-to-node mapping table in `ecology.py`. Minimum count guarantee must still hold.
2. To add a new environment effect: add the condition check and modifier calculation in `environment.py`. Do not write durable state — effects are per-tick snapshots only.
3. To activate `CALAMITY_RANDOM_CHANCE`: wire the constant into the calamity trigger check. This is currently dead code — enabling it changes calamity frequency significantly; update mechanics/05_world_evolution.md and add a parity ledger entry.
4. Ecology cadence (200 ticks) is configurable in world config — do not hardcode it in new code.
