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
