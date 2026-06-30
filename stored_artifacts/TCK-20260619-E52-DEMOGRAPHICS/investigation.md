# Investigation — TCK-20260619-E52-DEMOGRAPHICS

## Summary

`SpawnService` and `ResourceEcologyService` are density/spawn-rate driven (spawn every 50 ticks). No age-structured cohort model exists. Critical finding: **`age_ticks` already exists** in entity biological state at `src/core/state.py:L143` — so E52 does NOT need to add it to EntityState. The age field is there; what's missing is the advancement logic and cohort model.

## Key Findings

### What Already Exists

**Entity age fields** (`src/core/state.py:L143`):
```python
age_ticks: int = 0
max_age_ticks: int = 10000
```
Already serialized in `to_canonical_dict()`. **No new EntityState field needed.**

**RegionState** (`src/core/state.py:L204`):
```python
class RegionState:
    bounds: tuple[int, int, int, int]   # x_min, y_min, x_max, y_max
    hazard_level: float = 0.0
    # ... no population_cohorts field
```
Missing: `population_cohorts` field.

**SpawnService** (in `src/systems/world_systems/`): runs every 50 ticks; density formula: `density = max(2, int((region.area / 10_000) * 2.0 * (1 + region.hazard_level)))`. Spawn from catalog.

**ResourceEcologyService**: ECOLOGY_INTERVAL = 200 ticks. Has scarcity signals. Migration pressure should read from `ResourceEcologyService` scarcity output.

**D01**: [MISSING] — "no age-structured birth/death/migration cohorts."

### What Is Missing

1. `PopulationCohort` durable model added to `RegionState`
2. Birth/death cycle at 200-tick cadence (same as ecology, simpler than 50-tick spawn)
3. Migration pressure: when scarcity exceeds threshold → cohort emigrates to adjacent regions
4. Age advancement: entity `age_ticks` already increments, but no bracket advancement logic
   - Young: 0–3000 ticks; Adult: 3000–7000; Elder: 7000+
   - Elder: mortality_rate × 2.0, combat_effectiveness × 0.7, knowledge_reputation_weight × 1.3
5. PopulationCohort density feed into `RegionalPressureModel`

### Architecture Note

Cohort model is ADDITIVE to existing entities. `PopulationCohort` is an abstract counter (not per-entity). When birth threshold is crossed, SpawnService is triggered to create actual EntityState instances. Do NOT replace SpawnService; extend it to accept cohort-driven spawn requests.

Adjacent regions: defined by shared bounds or explicit adjacency list. Check `docs/mechanics/06_worldbuilding_foundation.md` for topology rules before wiring migration.

**Birth/death interval**: 200 ticks (same as ecology) — avoids tick-per-entity cost.

### Docs to Update After Implementation
- `docs/mechanics/05_world_evolution.md` — add demographic cycle
- `docs/world/ecology_and_calamity_contract.md` — PopulationCohort as demand signal
- New: `docs/world/demographics_contract.md`
