# Test Plan — TCK-20260619-E52-DEMOGRAPHICS

## Unit Tests — `tests/unit/world/test_demographics.py`

```python
def test_cohort_birth_generates_spawn_event():
    # PopulationCohort(bracket="young", count=50, birth_rate=0.02)
    # Run 1 cohort tick (200 ticks) → assert spawn_request event emitted (50*0.02=1.0 → spawn)

def test_cohort_death_reduces_count():
    # PopulationCohort(count=100, mortality_rate=0.01)
    # After 1 cohort tick → count ≈ 99

def test_cohort_does_not_exceed_regional_cap():
    # Region with low area; high birth_rate; assert count bounded by capacity

def test_age_bracket_returns_correct_bracket():
    assert get_age_bracket(0) == "young"
    assert get_age_bracket(3000) == "adult"
    assert get_age_bracket(7001) == "elder"

def test_elder_modifier_reduces_combat_effectiveness():
    # EntityState with age_ticks=8000 (elder)
    # Assert combat_effectiveness multiplier = 0.7

def test_migration_pressure_triggers_on_scarcity_threshold():
    # Region scarcity=0.8 (>migration_threshold=0.7)
    # Assert CohortTransferUpdate emitted with emigrant_count > 0
```

## Integration Tests — `tests/integration/scenarios/test_demographics.py`

```python
@pytest.mark.slow
def test_cohort_migrates_on_scarcity():
    # Deplete regional resources via E21 mechanics
    # Assert emigration event and source region cohort count decreases

@pytest.mark.slow
def test_entity_age_advances_to_elder_across_episodes():
    # Entity starts as YOUNG (age_ticks=0) in ep1
    # After sufficient episodes (age_ticks > 7000): assert age_bracket == "elder"
    # Assert elder entity has combat_effectiveness < 1.0

@pytest.mark.slow
def test_2000_tick_run_produces_cohort_demographic_change():
    # 2000-tick run with scarcity; assert ≥1 region's cohort composition changed
```

## Parity Coverage
- `docs/parity_ledger/world_dynamics.yaml`: add cohort model entries as `verified`
