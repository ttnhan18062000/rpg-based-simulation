# Tests for TCK-20260619-E52A-COHORT-MODEL
# Covers: PopulationCohort model, DemographicCycleService birth/death cycle
import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate, WorldUpdate
from src.domains.demographics.cohort import PopulationCohort, DemographicCycleService
from src.domains.world_emergence.schema import WorldEventCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_region(region_id: str = "region1", cohorts: dict | None = None) -> RegionState:
    return RegionState(
        id=region_id,
        name="Test Region",
        bounds=(0, 0, 100, 100),
        population_cohorts=cohorts or {},
    )


def _make_state(regions: dict | None = None) -> AuthoritativeState:
    return AuthoritativeState(
        tick=0,
        seed=42,
        regions=regions or {},
    )


# ---------------------------------------------------------------------------
# PopulationCohort model
# ---------------------------------------------------------------------------

class TestPopulationCohortModel:
    def test_default_values(self):
        cohort = PopulationCohort(bracket="young")
        assert cohort.count == 0
        assert cohort.birth_rate == pytest.approx(0.02)
        assert cohort.mortality_rate == pytest.approx(0.01)
        assert cohort.migration_threshold == pytest.approx(0.7)

    def test_custom_values(self):
        cohort = PopulationCohort(bracket="adult", count=50, birth_rate=0.05, mortality_rate=0.02)
        assert cohort.count == 50
        assert cohort.bracket == "adult"

    def test_frozen(self):
        cohort = PopulationCohort(bracket="elder", count=10)
        with pytest.raises((AttributeError, TypeError)):
            cohort.count = 99  # type: ignore


# ---------------------------------------------------------------------------
# DemographicCycleService — interval gate
# ---------------------------------------------------------------------------

class TestDemographicCycleServiceInterval:
    def test_no_update_between_intervals(self):
        region = _make_region(cohorts={"young": PopulationCohort(bracket="young", count=100, birth_rate=0.05)})
        state = _make_state(regions={"region1": region})
        result = DemographicCycleService.process_demographics(state, tick=199)
        assert result.is_noop()

    def test_no_update_at_tick_zero(self):
        region = _make_region(cohorts={"young": PopulationCohort(bracket="young", count=100, birth_rate=0.05)})
        state = _make_state(regions={"region1": region})
        # tick=0 is 0 % 200 == 0 — still fires on multiples including 0
        # But count=100, birth=5, death=1, net=4 → should produce updates
        result = DemographicCycleService.process_demographics(state, tick=0)
        assert not result.is_noop()

    def test_fires_at_200(self):
        region = _make_region(cohorts={"young": PopulationCohort(bracket="young", count=100, birth_rate=0.05)})
        state = _make_state(regions={"region1": region})
        result = DemographicCycleService.process_demographics(state, tick=200)
        assert not result.is_noop()

    def test_fires_at_400(self):
        region = _make_region(cohorts={"young": PopulationCohort(bracket="young", count=100, birth_rate=0.05)})
        state = _make_state(regions={"region1": region})
        result = DemographicCycleService.process_demographics(state, tick=400)
        assert not result.is_noop()


# ---------------------------------------------------------------------------
# DemographicCycleService — birth generates cohort count increase
# ---------------------------------------------------------------------------

class TestCohortBirth:
    def test_cohort_birth_generates_spawn_event(self):
        """
        Acceptance criterion: test_cohort_birth_generates_spawn_event
        young cohort count=100, birth_rate=0.02, mortality_rate=0.01 → net=+1 at tick=200
        → world_update for region1 has population_cohorts_set["young"].count == 101
        """
        cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.02, mortality_rate=0.01)
        region = _make_region(cohorts={"young": cohort})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert "region1" in result.world_updates
        cohorts_set = result.world_updates["region1"].population_cohorts_set
        assert cohorts_set is not None
        assert "young" in cohorts_set
        assert cohorts_set["young"].count == 101

    def test_birth_event_emitted(self):
        """A POPULATION_BIRTH WorldEvent is emitted for the cohort."""
        cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.02, mortality_rate=0.01)
        region = _make_region(cohorts={"young": cohort})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        birth_events = [e for e in result.world_events_add if e.category == WorldEventCategory.POPULATION_BIRTH]
        assert len(birth_events) == 1
        assert birth_events[0].region_id == "region1"
        assert "young" in birth_events[0].subject

    def test_large_population_birth(self):
        """Larger population produces proportionally larger net birth."""
        cohort = PopulationCohort(bracket="adult", count=1000, birth_rate=0.05, mortality_rate=0.01)
        region = _make_region(cohorts={"adult": cohort})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        cohorts_set = result.world_updates["region1"].population_cohorts_set
        # net = int(1000*0.05 - 1000*0.01) = int(50 - 10) = 40
        assert cohorts_set["adult"].count == 1040


# ---------------------------------------------------------------------------
# DemographicCycleService — death reduces count
# ---------------------------------------------------------------------------

class TestCohortDeath:
    def test_cohort_death_reduces_count(self):
        """
        Acceptance criterion: test_cohort_death_reduces_count
        elder cohort count=100, birth_rate=0.00, mortality_rate=0.05 → net=-5 at tick=200
        → world_update has population_cohorts_set["elder"].count == 95
        """
        cohort = PopulationCohort(bracket="elder", count=100, birth_rate=0.00, mortality_rate=0.05)
        region = _make_region(cohorts={"elder": cohort})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert "region1" in result.world_updates
        cohorts_set = result.world_updates["region1"].population_cohorts_set
        assert cohorts_set is not None
        assert "elder" in cohorts_set
        assert cohorts_set["elder"].count == 95

    def test_death_event_emitted(self):
        """A POPULATION_DEATH WorldEvent is emitted for the cohort."""
        cohort = PopulationCohort(bracket="elder", count=100, birth_rate=0.00, mortality_rate=0.05)
        region = _make_region(cohorts={"elder": cohort})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        death_events = [e for e in result.world_events_add if e.category == WorldEventCategory.POPULATION_DEATH]
        assert len(death_events) == 1
        assert death_events[0].region_id == "region1"

    def test_count_cannot_go_below_zero(self):
        """Population count is floored at 0 — cannot be negative.
        count=2, birth_rate=0.0, mortality_rate=1.0 → net=int(0 - 2.0)=-2 → new_count=max(0, 0)=0
        """
        cohort = PopulationCohort(bracket="elder", count=2, birth_rate=0.0, mortality_rate=1.0)
        region = _make_region(cohorts={"elder": cohort})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        cohorts_set = result.world_updates["region1"].population_cohorts_set
        assert cohorts_set["elder"].count == 0


# ---------------------------------------------------------------------------
# DemographicCycleService — zero net / empty cohorts
# ---------------------------------------------------------------------------

class TestCohortZeroNet:
    def test_zero_net_skips_cohort_update(self):
        """When birth_rate == mortality_rate, net=0 → cohort not included in update."""
        cohort = PopulationCohort(bracket="adult", count=100, birth_rate=0.01, mortality_rate=0.01)
        region = _make_region(cohorts={"adult": cohort})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        # net = int(1 - 1) = 0 → no update for this cohort
        assert result.is_noop()

    def test_region_without_cohorts_skipped(self):
        """Regions with empty population_cohorts produce no update."""
        region = _make_region(cohorts={})
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert result.is_noop()

    def test_no_regions(self):
        """State with no regions produces noop."""
        state = _make_state(regions={})
        result = DemographicCycleService.process_demographics(state, tick=200)
        assert result.is_noop()


# ---------------------------------------------------------------------------
# DemographicCycleService — multiple cohorts / multiple regions
# ---------------------------------------------------------------------------

class TestCohortMultiple:
    def test_multiple_cohorts_in_same_region(self):
        """All cohorts in a region with non-zero net are included in a single WorldUpdate."""
        cohorts = {
            "young": PopulationCohort(bracket="young", count=100, birth_rate=0.05, mortality_rate=0.01),
            "elder": PopulationCohort(bracket="elder", count=50, birth_rate=0.00, mortality_rate=0.04),
        }
        region = _make_region(cohorts=cohorts)
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert "region1" in result.world_updates
        cohorts_set = result.world_updates["region1"].population_cohorts_set
        # young: net = int(5 - 1) = 4 → 104
        assert cohorts_set["young"].count == 104
        # elder: net = int(0 - 2) = -2 → 48
        assert cohorts_set["elder"].count == 48

    def test_multiple_regions_independent(self):
        """Each region gets its own WorldUpdate entry."""
        cohort_a = PopulationCohort(bracket="young", count=100, birth_rate=0.05, mortality_rate=0.01)
        cohort_b = PopulationCohort(bracket="elder", count=80, birth_rate=0.00, mortality_rate=0.05)
        region_a = _make_region("r1", cohorts={"young": cohort_a})
        region_b = _make_region("r2", cohorts={"elder": cohort_b})
        state = _make_state(regions={"r1": region_a, "r2": region_b})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert "r1" in result.world_updates
        assert "r2" in result.world_updates
        assert result.world_updates["r1"].population_cohorts_set["young"].count == 104
        assert result.world_updates["r2"].population_cohorts_set["elder"].count == 76

    def test_mixed_net_regions(self):
        """A region with one zero-net cohort and one non-zero cohort is still included."""
        cohorts = {
            "adult": PopulationCohort(bracket="adult", count=100, birth_rate=0.01, mortality_rate=0.01),  # net=0
            "young": PopulationCohort(bracket="young", count=100, birth_rate=0.05, mortality_rate=0.01),  # net=4
        }
        region = _make_region(cohorts=cohorts)
        state = _make_state(regions={"region1": region})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert "region1" in result.world_updates
        cohorts_set = result.world_updates["region1"].population_cohorts_set
        assert cohorts_set["young"].count == 104
        # adult unchanged — not in the update set (zero net was skipped)
        # The entire dict is set, but adult comes from the original dict copy unchanged
        assert cohorts_set["adult"].count == 100


# ---------------------------------------------------------------------------
# RegionState backward compatibility
# ---------------------------------------------------------------------------

class TestRegionStateBackwardCompatibility:
    def test_region_state_has_default_empty_cohorts(self):
        """Existing RegionState construction still works without population_cohorts."""
        region = RegionState(id="r1", name="Test", bounds=(0, 0, 10, 10))
        assert region.population_cohorts == {}

    def test_region_state_with_cohorts(self):
        cohort = PopulationCohort(bracket="young", count=50)
        region = RegionState(
            id="r1",
            name="Test",
            bounds=(0, 0, 10, 10),
            population_cohorts={"young": cohort},
        )
        assert region.population_cohorts["young"].count == 50

    def test_region_canonical_dict_includes_cohorts(self):
        cohort = PopulationCohort(bracket="adult", count=20)
        region = RegionState(
            id="r1",
            name="Test",
            bounds=(0, 0, 10, 10),
            population_cohorts={"adult": cohort},
        )
        canon = region.to_canonical_dict()
        assert "population_cohorts" in canon
        assert "adult" in canon["population_cohorts"]


# ---------------------------------------------------------------------------
# WorldUpdate — population_cohorts_set field
# ---------------------------------------------------------------------------

class TestWorldUpdateCohorts:
    def test_world_update_default_no_cohorts(self):
        upd = WorldUpdate(region_id="r1")
        assert upd.population_cohorts_set is None

    def test_world_update_merge_cohorts(self):
        """Merge keeps last-write-wins for population_cohorts_set."""
        cohort_a = {"young": PopulationCohort(bracket="young", count=10)}
        cohort_b = {"young": PopulationCohort(bracket="young", count=20)}
        upd_a = WorldUpdate(region_id="r1", population_cohorts_set=cohort_a)
        upd_b = WorldUpdate(region_id="r1", population_cohorts_set=cohort_b)
        merged = upd_a.merge(upd_b)
        assert merged.population_cohorts_set["young"].count == 20

    def test_world_update_merge_none_preserves_existing(self):
        """Merging None population_cohorts_set keeps the existing value."""
        cohort_a = {"young": PopulationCohort(bracket="young", count=10)}
        upd_a = WorldUpdate(region_id="r1", population_cohorts_set=cohort_a)
        upd_b = WorldUpdate(region_id="r1")  # no cohort set
        merged = upd_a.merge(upd_b)
        assert merged.population_cohorts_set["young"].count == 10
