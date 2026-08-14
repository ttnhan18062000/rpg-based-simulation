---
status: authoritative
layer: world
authority: P1
audience: developer
last_verified: 2026-07-02
tags: [demographics, cohort, population, density-signal, phase-5]
---

# Demographics Contract

> **Authority:** Certified Level 1 (Authoritative)
> **Tickets:** TCK-20260619-E52A-COHORT-MODEL · TCK-20260619-E52B-MIGRATION · TCK-20260619-E52C-AGE-ADVANCEMENT · TCK-20260619-E52D-DENSITY-SIGNAL
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

---

## 7. Source Files

| File | Role |
|---|---|
| `src/domains/demographics/cohort.py` | PopulationCohort, DemographicCycleService, all pure helpers |
| `src/domains/world_emergence/models.py` | RegionalPressureModel with density demand multiplier |
| `src/core/state.py` | RegionState.population_cohorts field |
| `src/core/updates.py` | WorldUpdate.population_cohorts_set field |
| `tests/unit/world/test_demographics.py` | Unit tests (57 tests) |
| `tests/integration/scenarios/test_demographics.py` | Integration tests (4 tests) |
