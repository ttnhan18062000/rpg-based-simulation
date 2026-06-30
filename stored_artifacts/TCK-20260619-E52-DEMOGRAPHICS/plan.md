# Plan — TCK-20260619-E52-DEMOGRAPHICS

## Approach

Add `PopulationCohort` to `RegionState`. Wire birth/death cycle into `ResourceEcologyService` at 200-tick cadence. Wire migration pressure from scarcity signals. Age bracket advancement uses existing `age_ticks` field.

## Sequence

**E52A → E52B → E52C → E52D** (strictly sequential)

---

## E52A · PopulationCohort Model + Birth/Death Cycle

**Extend `RegionState`** (`src/core/state.py:L204`):
```python
population_cohorts: Dict[str, PopulationCohort] = field(default_factory=dict)
# key: "young" | "adult" | "elder"
```

New file `src/domains/demographics/cohort.py`:
```python
@dataclass(frozen=True, slots=True)
class PopulationCohort:
    bracket: str   # "young" | "adult" | "elder"
    count: int = 0
    birth_rate: float = 0.02   # per 200 ticks
    mortality_rate: float = 0.01
    migration_threshold: float = 0.7   # scarcity above this → emigrate

class DemographicCycleService:
    COHORT_INTERVAL = 200  # same cadence as ecology

    @staticmethod
    def tick(state: AuthoritativeState, tick: int) -> list[StateUpdate]:
        if tick % DemographicCycleService.COHORT_INTERVAL != 0:
            return []
        updates = []
        for region_id, region in state.regions.items():
            updates.extend(DemographicCycleService._apply_birth_death(region, region_id, tick))
        return updates
```

Birth: when `young_count * birth_rate > 1.0`, emit spawn event (→ `SpawnService.request_spawn()`).
Death: decrement count by `count * mortality_rate`.

---

## E52B · Migration Pressure + Cohort Movement

In `DemographicCycleService.tick()`:
```python
if region_scarcity > cohort.migration_threshold:
    # emigrate fraction to lowest-scarcity adjacent region
    emigrant_count = int(cohort.count * 0.3)  # 30% emigrate
    adjacent = find_adjacent_regions(region_id, state)
    target = min(adjacent, key=lambda r: r.scarcity)
    updates.append(CohortTransferUpdate(source=region_id, target=target.id, count=emigrant_count))
```

Read scarcity from `ResourceEcologyService` output (confirm field name before implementing — likely `remaining_charges / max_charges` aggregate per region).

---

## E52C · Entity Age Advancement

`age_ticks` already exists on `BiologicalComponent` at `src/core/state.py:L143`. What's missing is bracket advancement effects.

Wire in biological update phase:
```python
def get_age_bracket(age_ticks: int) -> str:
    if age_ticks < 3000: return "young"
    if age_ticks < 7000: return "adult"
    return "elder"

def apply_age_bracket_modifiers(entity: EntityState) -> EntityUpdate:
    bracket = get_age_bracket(entity.biological.age_ticks)
    if bracket == "elder":
        # mortality_rate × 2.0, combat_effectiveness × 0.7, knowledge_rep_weight × 1.3
        return EntityUpdate(entity_id=entity.id, age_bracket=bracket, ...)
```

---

## E52D · Density Signals to RegionalPressureModel

Wire `PopulationCohort.count` sum per region into `RegionalPressureModel` as `population_density` demand signal.

Find `RegionalPressureModel` location before implementing (likely in `src/systems/world_systems/` or `src/engine/`).

Population density signal: `density = (young.count + adult.count + elder.count) / region_area`. Feed into existing pressure model as a resource demand multiplier.

After E52D: create `docs/world/demographics_contract.md`. Update `docs/mechanics/05_world_evolution.md`. Run `make knowledge-index-update`.
