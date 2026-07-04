---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-06-06
---

# Chapter 5: World Evolution

This chapter describes the "Macro Laws" that govern the state of the world environment, regional safety, and the passage of time.

---

## 1. The Passage of Time
The simulation operates on a fixed-rate tick system. Every action and biological process is synced to this clock.

| Unit | Tick Count | Real-Time Approx (Simulated) |
| :--- | :--- | :--- |
| **1 Tick** | 1 | ~36 Seconds |
| **1 Hour** | 100 | 1 Hour |
| **1 Day** | 2400 | 24 Hours |

---

## 2. Regional Trauma & Hazards
Regions are not static. They react to the violence and activity within their borders through the **Trauma Score**.

### The Trauma Cycle
1.  **Event**: Every entity death in a region adds **+1.0** to the regional `Trauma Score`.
2.  **Threshold**: If `Trauma Score > 50.0`, the region enters an unstable state.
3.  **Hazard Scaling**: Unstable regions gain **+0.01** `Hazard Level` per world cycle.

> For how per-entity Hazard Level drain is actually resolved against an entity standing in
> the region (including faction-based endurance to a region's hazard kind), see
> [§3 Regional Sovereignty — Hazard Impacts](#hazard-impacts) below.

---

## 3. Regional Sovereignty
Regions can be claimed and controlled by specific factions based on their active **Influence**.

### Influence Shifts
Every death in a region shifts the balance of power:
*   **Monster Death**: Increases Hero Influence by **+1.0**.
*   **Hero Death**: Decreases Hero Influence by **-1.0** (shifts towards Monster Horde).

### Ownership Thresholds
A region is officially "Owned" when influence reaches significant levels:
*   **Hero Controlled**: Influence ≥ **+100.0**.
*   **Monster Controlled**: Influence ≤ **-100.0**.

**Impact of Ownership**: Faction-owned regions may provide safe zones for allies, trigger reinforcement spawns, or apply special economic modifiers to local trade.

### Hazard Impacts
As `Hazard Level` (0.0 to 1.0) increases, entities within the region suffer:
*   **Passive HP Drain**: Health is lost every tick based on the hazard's intensity.
*   **Environmental Fatigue**: Sleep Debt increases by **+1.0** (extra exhaustion) due to extreme conditions.
*   **Suppression**: If a region is "Suppressed," entities lose **-5.0 Readiness** per tick, significantly slowing down their action frequency.

#### Native Endurance to a Region's Hazard Kind
Every region carries a `hazard_kind` tag (e.g. `"PHYSICAL"` — the default, `"NATURAL_TERRAIN"`,
`"TOXIC_GAS"`, `"UNDEAD_CORRUPTION"`) describing *what kind* of hazard its passive drain
represents. Separately, a faction's catalog definition may declare `hazard_immunities` — the set
of `hazard_kind` values its members endure without harm (e.g. `wild_beast_pack` and
`goblin_warband` both declare `hazard_immunities: ["NATURAL_TERRAIN"]`, since wolves and goblins
are native to their own forest habitats; `undead_remnants` declares
`hazard_immunities: ["UNDEAD_CORRUPTION"]`, since undead endure the corruption of their own
battlefield for a distinct in-fiction reason from ordinary wilderness endurance). `"TOXIC_GAS"`
remains synthetic/test-only (used only in unit tests, `tests/unit/world/test_regional_consequences.py`);
`"UNDEAD_CORRUPTION"` is an authored production value as of
TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS (`data/content/world_modules/undead_battlefield.yaml`).

When computing Passive HP Drain for an entity, `EnvironmentService.calculate_hazard_drain`
resolves the entity's catalog faction id and checks it against the region's `hazard_kind`:
if the entity's faction endures that hazard kind, drain is **zero**; otherwise the drain
formula above applies unchanged. This endurance check is **unconditional** — it applies before
and independent of `calamity_intensity` scaling or the `MIASMA` modifier, and it does not
consult hostility relationships between factions.

This means endurance is strictly a property a faction declares for itself, never an inference
from being hostile (or not) to another faction. A hazard kind that no faction present has
declared endurance for hurts **every** faction standing in it equally — for example, if a hero
party and a wolf pack fight each other inside a `"TOXIC_GAS"` region, both sides take full,
unmitigated drain, because neither faction lists `"TOXIC_GAS"` in its `hazard_immunities`. A
faction being bucketed as hostile-to-heroes (e.g. `legacy_engine_bucket: "MONSTER_HORDE"`)
confers no hazard endurance by itself.

`RegionState.hazard_kind` defaults to `"PHYSICAL"` and `FactionDefinition.hazard_immunities`
defaults to an empty list, so this mechanism is fully opt-in per content: existing regions and
factions with neither field authored behave exactly as before (full, unmitigated drain for
every entity). Content must explicitly author both a region's `hazard_kind` and a faction's
matching `hazard_immunities` entry for the exemption to take effect.

> **Compiled-instance staleness note**: `data/worlds/sandbox_world/`'s compiled/resolved
> artifacts are generated ahead-of-time from the source catalog and do not pick up this
> mechanism's effect until they are recompiled — that recompile is the responsibility of
> `TCK-20260701-SANDBOX-MONSTER-BALANCE`, not this chapter's authoring change.
>
> `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` extended this mechanism corpus-wide: 7 modules
> (`orc_clan_territory`, `bandit_road_trade_pressure`, `old_mine_resource_loop`,
> `forest_warden_grove`, `undead_battlefield`, `nomadic_herd`, `sunken_swamp_border`) gained
> `hazard_kind` + matching native-faction `hazard_immunities`, and the 8 worlds whose compiled
> state predated these fixes (`simq_routing_test`, `dungeon_crawl`, `generated_frontier_3_42`,
> `frontier_extended`, `frontier_living_world`, `swamp_border_world`, `highland_traverse`,
> `wilderness_survival`) were recompiled to pick them up.

---

## 3. Ecology & Replenishment
The world automatically replenishes consumed resources and removes "Simulation Trash" (decay).

### Respawn Laws
*   **Resource Nodes**: Once depleted (0 charges), nodes enter a cooldown. They respawn after **100 ticks** by default.
*   **Monsters**: Replenished periodically based on the region's `Influence` and `Trauma`. High Hero influence reduces monster spawn rates.
*   **Chests**: Once looted, chests enter a long cooldown before they can be searched again.

### Decay Laws
*   **Corpses**: Entities that are killed remain in the world as `Corpse` objects for a fixed duration (`decay_tick`) before being permanently removed.
*   **Ground Items**: Items dropped on the floor also decay over time to prevent simulation clutter.

---

## 4. Regional Transformation
Regions can physically transform their "Kind" over long periods.
*   **Stability**: High stability regions resist change. Low stability (caused by high trauma) allows for transformations.
*   **Shifting**: A `PLAIN` region might shift to a `FOREST` or `SWAMP` depending on the environmental "Pressure" and duration of trauma.

---

## 5. Demographic Cohort Cycle

Each region tracks an abstract population divided into three age brackets: `young`, `adult`, and `elder`. The demographic cycle runs every **200 ticks** (`DemographicCycleService.COHORT_INTERVAL`).

### Birth/Death Law
```
net_change = int(cohort.count * birth_rate) - int(cohort.count * mortality_rate)
new_count  = max(0, cohort.count + net_change)
```
Default rates: `birth_rate = 0.02`, `mortality_rate = 0.01` → net +1% per 200 ticks.

### Migration Law
When `scarcity(region) > cohort.migration_threshold` (default 0.7), **30%** of that cohort (min 1) emigrates to the lowest-scarcity adjacent region. Adjacency requires a shared boundary edge with non-degenerate overlap on the other axis.

### Age Bracket Thresholds (Entity-Level)
| `age_ticks` range | Bracket | Modifier |
|---|---|---|
| < 3000 | young | none |
| 3000–6999 | adult | none |
| ≥ 7000 | elder | STR/AGI −30%, VIT/END −50%, WIS/CHA +30% |

### Population Density Demand Signal (E52D)
High-population regions amplify resource demand pressure in `RegionalPressureModel`:

```
population_density = total_cohort_count / max(1, region_area)
demand_multiplier  = 1.0 + (population_density * 0.5)
resource_pressure_intensity = min(1.0, base_intensity * demand_multiplier)
```

This closes the demographic feedback loop: population growth → density increase → resource pressure increase → scarcity increase → migration or constraint.

**Source:** `src/domains/demographics/cohort.py`, `src/domains/world_emergence/models.py`
**Contract:** `docs/world/demographics_contract.md`

---

## 6. Calamities & World Threats
When the global `Maturity` and regional `Trauma` scores are sufficiently high, the simulation triggers "Macro Events."
*   **Boss Spawns**: Unique, high-threat entities appear in traumatized regions.
*   **Raids**: Faction-based attacks on town centers or resource hubs.
*   **Threat Evolution**: Monsters in high-hazard regions evolve to higher `Evolution Levels`, becoming deadlier and granting better rewards.

---

## 7. Cultural Drift (E62)

Over long campaigns, regional cultures develop distinct values driven by their accumulated
narrative history. Culture drift is a **long-horizon** mechanism — it operates at episode
boundaries, not per tick.

### Axis Definitions

| Axis | Derivation source | Motivation effect |
|---|---|---|
| `fatalism` | `calamity` events + entity_death with cause="calamity" | +caution, −pride |
| `hero_veneration` | entity_death where entity_role="HERO" | +loyalty, +pride |
| `resource_scarcity_memory` | `INFLATION_SPIRAL` events | +survival |
| `faction_conflict_exposure` | `war_declared`, `territory_transferred`, `faction_destroyed` | +caution, −loyalty |

All axes are floats in [0.0, 1.0]. Normalisation: `axis = min(1.0, raw_sum / 3.0)`.
Three high-significance events saturate an axis.

### Derivation Trigger

`CultureDriftExporter.export()` is called from `CampaignOrchestrator._advance_state()`
at every episode boundary, after the narrative ledger has been updated for that episode.
It calls `ChronicleGrouper().group(narrative_ledger)` to group all accumulated entries,
then `CultureDeriver.derive(hierarchy)` to produce `Dict[str, CultureState]`.

### Persistence

`CultureState` per region is stored as `CultureCarryForward` in
`CampaignState.region_cultures: Dict[str, CultureCarryForward]`. Regions without events
in a given episode keep their prior culture snapshot unchanged until the next derivation.

### Motivation Overlay

`CulturalBiasApplicator.compute_culture_delta(culture, tags) -> float` returns an
additive delta layered onto `MotivationBiasService.compute_bias_multiplier()` result.

- Axes below `CULTURE_ACTIVATION_THRESHOLD = 0.3` produce no effect.
- Final delta is bounded: `max(-0.5, min(1.0, delta))`.
- The overlay is **transient** — it never modifies the entity's durable `MotivationModel`.

### Acceptance Signal

> In a 5-episode campaign, the `caution` tag motivation delta for a region with 3 calamity
> events exceeds that of a region with 3 hero deaths by at least 0.1.

**Sources:** `src/domains/culture/`
**Contract:** `docs/world/culture_drift_contract.md`
**Parity:** WORLD-CULT-001, WORLD-CULT-002, WORLD-CULT-003
