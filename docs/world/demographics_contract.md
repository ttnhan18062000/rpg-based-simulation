---
status: authoritative
layer: world
authority: P1
audience: developer
last_verified: 2026-09-01
tags: [demographics, cohort, population, density-signal, phase-5]
---

# Demographics Contract

> **Authority:** Certified Level 1 (Authoritative)
> **Tickets:** TCK-20260619-E52A-COHORT-MODEL · TCK-20260619-E52B-MIGRATION · TCK-20260619-E52C-AGE-ADVANCEMENT · TCK-20260619-E52D-DENSITY-SIGNAL · TCK-20260831-POPULATION-COHORT-SEEDING
> **Layer:** world
> **Tags:** demographics, cohort, population, density-signal, phase-5

---

## Overview

The Demographic Cohort Population Model introduces abstract population dynamics to each region. Regions track per-bracket cohort counts (young / adult / elder) that evolve each 200-tick cycle through birth/death rates, migration, and age advancement. High-population regions feed back into the economy by amplifying resource demand pressure.

---

## 1. PopulationCohort Model

Defined in `src/domains/demographics/cohort.py`.

| Field | Type | Default | Description |
|---|---|---|---|
| `bracket` | str | required | Age bracket: `"young"` \| `"adult"` \| `"elder"` |
| `count` | int | 0 | Abstract population count for this bracket |
| `birth_rate` | float | 0.02 | Fraction of count born per 200-tick cycle |
| `mortality_rate` | float | 0.01 | Fraction of count that die per 200-tick cycle |
| `migration_threshold` | float | 0.7 | Regional scarcity above which emigration fires |

Cohorts are stored in `RegionState.population_cohorts: Dict[str, PopulationCohort]` keyed by bracket name.

---

## 1a. Compile-Time Seeding

**Ticket:** `TCK-20260831-POPULATION-COHORT-SEEDING`

`WorldCompiler.compile()` seeds `RegionState.population_cohorts` from `WorldSpec.entities`
(`PopulationSpec.count`, summed by `spawn_region`) at world-assembly time — not via the
tick-time `WorldUpdate.population_cohorts_set` merge path used by `apply_plan.py`. This is
a direct `RegionState(...)` constructor assignment, following the same precedent already
used for `influence` and `owner_faction_id`.

**Distribution ratio.** No prior anchor existed in code or docs for how many entities in a
declared population belong to which age bracket. This ticket authors a fixed
young/adult/elder ratio of **30/50/20**, chosen as a plausible stable/mildly-growing
population pyramid shape — a plurality of working-age adults, a meaningful youth cohort,
and a smaller elder cohort — directionally consistent with `PopulationCohort`'s own default
`birth_rate` (0.02) exceeding `mortality_rate` (0.01), which already implies net growth.
The ratio is intentionally simple/round, not derived from any external demographic dataset
— a fresh design choice, not a parity claim against real-world data.

**Rounding.** Counts are split using largest-remainder (Hamilton apportionment) rounding
with a fixed tie-break priority `["young", "adult", "elder"]`, guaranteeing the three
bracket counts always sum exactly to the declared population, including at small totals
(0, 1, 2) where naive per-bracket floor/truncation can lose 1-2 units. Pure arithmetic, no
RNG draw — this preserves `compile()`'s determinism.

**Rates left untouched.** Seeded `PopulationCohort` instances keep `birth_rate=0.02` /
`mortality_rate=0.01` — the existing dataclass defaults — unchanged. This ticket's job is
to seed the initial `count` values that §2's existing per-`COHORT_INTERVAL`-tick (200-tick)
birth/death cycle then applies going forward; it does not rebalance or reinterpret what
those rates mean. Those rates remain expressed in ticks, not any calendar-independent unit
(e.g. births/year) — recalibrating them to a calendar-independent unit is an
accepted-but-not-yet-implemented future decision owned by
`TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`, not this ticket.

**Zero-`PopulationSpec` regions.** A region with no matching `PopulationSpec` entries gets
`population_cohorts={}` (an empty dict, not three zero-count cohorts), which
`DemographicCycleService`'s guard (`if not region.population_cohorts: continue`,
`cohort.py:349`) no-ops on directly via plain dict-truthiness.

---

## 2. Birth/Death Cycle

`DemographicCycleService.process_demographics(state, tick)` runs every `COHORT_INTERVAL = 200` ticks.

```
births = cohort.count * cohort.birth_rate
deaths = cohort.count * cohort.mortality_rate
net    = int(births - deaths)
new_count = max(0, cohort.count + net)
```

- Net > 0 → emits `WorldEventCategory.POPULATION_BIRTH`
- Net < 0 → emits `WorldEventCategory.POPULATION_DEATH`
- Net == 0 → no update, no event
- Result is returned as a `StateUpdate`; never mutates `AuthoritativeState` directly.

---

## 3. Migration (E52B)

When `compute_regional_scarcity(region_id, state) > cohort.migration_threshold`:

1. Compute emigrant count: `max(1, int(cohort.count * 0.30))`
2. Find lowest-scarcity adjacent region (tiebreak: sorted by region id)
3. Emit two `WorldUpdate` records: source count reduced, target count increased
4. Emit `WorldEventCategory.POPULATION_MIGRATION` event per cohort movement

Adjacency: regions share one boundary edge with non-degenerate overlap on the other axis. Defined in `find_adjacent_regions()`.

---

## 4. Age Bracket Classification (E52C)

`get_age_bracket(age_ticks: int) -> str` — pure deterministic function:

| Condition | Bracket |
|---|---|
| `age_ticks < 3000` | `"young"` |
| `3000 ≤ age_ticks < 7000` | `"adult"` |
| `age_ticks ≥ 7000` | `"elder"` |

Elder modifier (applied via `compute_elder_attribute_update`):

| Attribute | Delta |
|---|---|
| strength, agility | × 0.7 (−30%) |
| vitality, endurance | × 0.5 (−50%) |
| wisdom, charisma | × 1.3 (+30%) |

Returned as `EntityUpdate` with `AttributeUpdate`; never mutates state directly.

---

## 5. Population Density Signal (E52D)

`compute_population_density(region: RegionState) -> float` — pure function:

```python
total_pop = sum(c.count for c in region.population_cohorts.values())
area = (xmax - xmin) * (ymax - ymin)   # derived from region.bounds
density = total_pop / max(1, area)
```

Returns `0.0` when no cohorts are present.

### Demand Multiplier

Used by `RegionalPressureModel.evaluate()` to amplify resource pressure in densely populated regions:

```
demand_multiplier = 1.0 + (population_density * 0.5)
res_intensity = min(1.0, base_resource_intensity * demand_multiplier)
```

- Zero-population region: `demand_multiplier = 1.0` (no amplification)
- Population of 2000 in 100×100 area (density = 0.2): `demand_multiplier = 1.1`

The multiplier is recorded in `RegionalPressure.source_aggregates` as `density_mult:<value>` for observability.

---

## 6. Parity Entries

| ID | Status | Test |
|---|---|---|
| WORLD-DEMO-001 | verified | `test_migration_pressure_triggers_on_scarcity_threshold` |
| WORLD-DEMO-002 | verified | `test_cohort_migrates_on_scarcity` |
| WORLD-DEMO-003 | verified | `test_age_bracket_returns_correct_bracket` |
| WORLD-DEMO-004 | verified | `test_elder_modifier_reduces_combat_effectiveness` |
| WORLD-DEMO-005 | verified | `test_high_population_region_higher_resource_demand` |
| WORLD-DEMO-006 | verified | `test_compiler_seeds_population_cohorts_from_spec` |

---

## 7. Source Files

| File | Role |
|---|---|
| `src/domains/demographics/cohort.py` | PopulationCohort, DemographicCycleService, all pure helpers |
| `src/domains/world_emergence/models.py` | RegionalPressureModel with density demand multiplier |
| `src/core/state.py` | RegionState.population_cohorts field |
| `src/core/updates.py` | WorldUpdate.population_cohorts_set field |
| `src/worldbuilding/compiler.py` | `_seed_population_cohorts()` — compile-time seeding into `RegionState.population_cohorts` (§1a) |
| `tests/unit/world/test_demographics.py` | Unit tests |
| `tests/integration/scenarios/test_demographics.py` | Integration tests |
| `tests/unit/worldbuilding/test_world_compiler.py` | Compile-time seeding unit tests (§1a) |
