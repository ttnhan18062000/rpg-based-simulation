# Tests for TCK-20260619-E52A-COHORT-MODEL, TCK-20260619-E52B-MIGRATION, TCK-20260619-E52C-AGE-ADVANCEMENT
# TCK-20260619-E52D-DENSITY-SIGNAL
# Covers: PopulationCohort model, DemographicCycleService birth/death cycle, migration pressure,
#         age bracket classification, elder attribute modifiers, population density signal
import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, AttributeComponent, RegionState, ResourceNodeState
from src.core.updates import AttributeUpdate, EntityUpdate, StateUpdate, WorldUpdate
from src.domains.demographics.cohort import (
    PopulationCohort,
    DemographicCycleService,
    compute_elder_attribute_update,
    compute_population_density,
    compute_regional_scarcity,
    find_adjacent_regions,
    get_age_bracket,
)
from src.domains.world_emergence.schema import WorldEventCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_region(
    region_id: str = "region1",
    cohorts: dict | None = None,
    bounds_: tuple = (0, 0, 100, 100),
) -> RegionState:
    return RegionState(
        id=region_id,
        name=f"Region {region_id}",
        bounds=bounds_,
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


# ---------------------------------------------------------------------------
# E52B: compute_regional_scarcity
# ---------------------------------------------------------------------------

def _make_node(
    node_id: int,
    position: tuple,
    remaining_charges: int,
    max_charges: int = 5,
) -> "ResourceNodeState":
    from src.core.state import ResourceNodeState
    return ResourceNodeState(
        id=node_id,
        kind="WOOD",
        position=position,
        yields_item="wood_log",
        remaining_charges=remaining_charges,
        max_charges=max_charges,
        required_ticks=10,
    )


def _make_state_with_nodes(regions: dict, resource_nodes: dict | None = None) -> AuthoritativeState:
    return AuthoritativeState(
        tick=0,
        seed=42,
        regions=regions,
        resource_nodes=resource_nodes or {},
    )


class TestComputeRegionalScarcity:
    def test_no_nodes_returns_1_0(self):
        """Zero resource nodes in region → scarcity = 1.0."""
        region = _make_region("r1", bounds_=(0, 0, 100, 100))
        state = _make_state_with_nodes({"r1": region})
        assert compute_regional_scarcity("r1", state) == pytest.approx(1.0)

    def test_full_nodes_returns_0_0(self):
        """All nodes at full charges → scarcity = 0.0."""
        region = _make_region("r1", bounds_=(0, 0, 100, 100))
        node = _make_node(1, (50.0, 50.0), remaining_charges=5, max_charges=5)
        state = _make_state_with_nodes({"r1": region}, {1: node})
        assert compute_regional_scarcity("r1", state) == pytest.approx(0.0)

    def test_depleted_node_returns_1_0(self):
        """Single depleted node (remaining=0) → scarcity = 1.0."""
        region = _make_region("r1", bounds_=(0, 0, 100, 100))
        node = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
        state = _make_state_with_nodes({"r1": region}, {1: node})
        assert compute_regional_scarcity("r1", state) == pytest.approx(1.0)

    def test_partial_depletion(self):
        """Node at 2/5 charges → mean ratio = 0.4 → scarcity = 0.6."""
        region = _make_region("r1", bounds_=(0, 0, 100, 100))
        node = _make_node(1, (50.0, 50.0), remaining_charges=2, max_charges=5)
        state = _make_state_with_nodes({"r1": region}, {1: node})
        assert compute_regional_scarcity("r1", state) == pytest.approx(0.6)

    def test_node_outside_region_excluded(self):
        """Node outside region bounds is not counted → scarcity = 1.0."""
        region = _make_region("r1", bounds_=(0, 0, 100, 100))
        node = _make_node(1, (200.0, 200.0), remaining_charges=5, max_charges=5)
        state = _make_state_with_nodes({"r1": region}, {1: node})
        assert compute_regional_scarcity("r1", state) == pytest.approx(1.0)

    def test_unknown_region_returns_1_0(self):
        """Non-existent region_id → scarcity = 1.0."""
        state = _make_state_with_nodes({})
        assert compute_regional_scarcity("missing", state) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# E52B: find_adjacent_regions
# ---------------------------------------------------------------------------

class TestFindAdjacentRegions:
    def test_no_regions_returns_empty(self):
        state = _make_state_with_nodes({})
        assert find_adjacent_regions("r1", state) == []

    def test_single_region_no_neighbours(self):
        region = _make_region("r1", bounds_=(0, 0, 100, 100))
        state = _make_state_with_nodes({"r1": region})
        assert find_adjacent_regions("r1", state) == []

    def test_two_adjacent_regions(self):
        """r1 and r2 share a vertical edge at x=100."""
        r1 = _make_region("r1", bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(100, 0, 200, 100))
        state = _make_state_with_nodes({"r1": r1, "r2": r2})
        result = find_adjacent_regions("r1", state)
        assert len(result) == 1
        assert result[0].id == "r2"

    def test_two_non_adjacent_regions(self):
        """r1 and r2 have a gap between them — not adjacent."""
        r1 = _make_region("r1", bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(200, 0, 300, 100))
        state = _make_state_with_nodes({"r1": r1, "r2": r2})
        assert find_adjacent_regions("r1", state) == []

    def test_results_sorted_by_id(self):
        """Multiple adjacent regions are returned sorted by id."""
        r1 = _make_region("r1", bounds_=(100, 0, 200, 100))
        r2 = _make_region("r2", bounds_=(200, 0, 300, 100))  # right of r1
        r3 = _make_region("r3", bounds_=(0, 0, 100, 100))   # left of r1
        state = _make_state_with_nodes({"r1": r1, "r2": r2, "r3": r3})
        result = find_adjacent_regions("r1", state)
        ids = [r.id for r in result]
        assert ids == sorted(ids)
        assert set(ids) == {"r2", "r3"}

    def test_corner_touch_not_adjacent(self):
        """Regions that only touch at a corner are NOT adjacent (no shared edge)."""
        r1 = _make_region("r1", bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(100, 100, 200, 200))
        state = _make_state_with_nodes({"r1": r1, "r2": r2})
        assert find_adjacent_regions("r1", state) == []

    def test_horizontal_adjacency(self):
        """r1 (bottom) and r2 (top) share a horizontal edge at y=100."""
        r1 = _make_region("r1", bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(0, 100, 100, 200))
        state = _make_state_with_nodes({"r1": r1, "r2": r2})
        result = find_adjacent_regions("r1", state)
        assert len(result) == 1
        assert result[0].id == "r2"


# ---------------------------------------------------------------------------
# E52B: Migration pressure — DemographicCycleService integration
# ---------------------------------------------------------------------------

class TestMigrationPressure:
    def test_migration_pressure_triggers_on_scarcity_threshold(self):
        """
        Acceptance criterion: test_migration_pressure_triggers_on_scarcity_threshold.
        r1 has scarcity=1.0 (depleted node), migration_threshold=0.7 → migration fires.
        r2 is adjacent with full node (scarcity=0.0) → receives emigrants.
        young cohort count=100 → 30 emigrate.
        """
        cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.0, mortality_rate=0.0,
                                  migration_threshold=0.7)
        r1 = _make_region("r1", cohorts={"young": cohort}, bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(100, 0, 200, 100))

        depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
        full = _make_node(2, (150.0, 50.0), remaining_charges=5, max_charges=5)
        state = _make_state_with_nodes({"r1": r1, "r2": r2}, {1: depleted, 2: full})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert "r1" in result.world_updates
        assert "r2" in result.world_updates
        assert result.world_updates["r1"].population_cohorts_set["young"].count == 70
        assert result.world_updates["r2"].population_cohorts_set["young"].count == 30

        mig_events = [e for e in result.world_events_add
                      if e.category == WorldEventCategory.POPULATION_MIGRATION]
        assert len(mig_events) == 1
        assert mig_events[0].region_id == "r1"

    def test_no_migration_below_threshold(self):
        """Scarcity below threshold → no migration updates."""
        cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.0, mortality_rate=0.0,
                                  migration_threshold=0.7)
        r1 = _make_region("r1", cohorts={"young": cohort}, bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(100, 0, 200, 100))

        # Full resource node → scarcity 0.0 (below 0.7 threshold)
        full = _make_node(1, (50.0, 50.0), remaining_charges=5, max_charges=5)
        state = _make_state_with_nodes({"r1": r1, "r2": r2}, {1: full})

        result = DemographicCycleService.process_demographics(state, tick=200)

        # No birth/death (rates=0.0), no migration (scarcity=0.0 < 0.7)
        assert result.is_noop()

    def test_no_migration_no_adjacent(self):
        """Scarcity > threshold but no adjacent regions → no migration."""
        cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.0, mortality_rate=0.0,
                                  migration_threshold=0.7)
        r1 = _make_region("r1", cohorts={"young": cohort}, bounds_=(0, 0, 100, 100))
        depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
        state = _make_state_with_nodes({"r1": r1}, {1: depleted})

        result = DemographicCycleService.process_demographics(state, tick=200)

        # No migration (isolated region), no birth/death (rates=0.0)
        assert result.is_noop()

    def test_migration_emigrant_count_30pct(self):
        """count=100 → emigrant_count = int(100 * 0.30) = 30."""
        cohort = PopulationCohort(bracket="adult", count=100, birth_rate=0.0, mortality_rate=0.0,
                                  migration_threshold=0.7)
        r1 = _make_region("r1", cohorts={"adult": cohort}, bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(100, 0, 200, 100))

        depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
        full = _make_node(2, (150.0, 50.0), remaining_charges=5, max_charges=5)
        state = _make_state_with_nodes({"r1": r1, "r2": r2}, {1: depleted, 2: full})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert result.world_updates["r1"].population_cohorts_set["adult"].count == 70
        assert result.world_updates["r2"].population_cohorts_set["adult"].count == 30

    def test_migration_emigrant_count_min_1(self):
        """count=1, 30% → int(0.3)=0 → clamped to max(1, 0)=1."""
        cohort = PopulationCohort(bracket="young", count=1, birth_rate=0.0, mortality_rate=0.0,
                                  migration_threshold=0.7)
        r1 = _make_region("r1", cohorts={"young": cohort}, bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(100, 0, 200, 100))

        depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
        full = _make_node(2, (150.0, 50.0), remaining_charges=5, max_charges=5)
        state = _make_state_with_nodes({"r1": r1, "r2": r2}, {1: depleted, 2: full})

        result = DemographicCycleService.process_demographics(state, tick=200)

        assert result.world_updates["r1"].population_cohorts_set["young"].count == 0
        assert result.world_updates["r2"].population_cohorts_set["young"].count == 1

    def test_migration_picks_lowest_scarcity_target(self):
        """When two adjacent regions have different scarcity, migrants go to lower-scarcity one."""
        cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.0, mortality_rate=0.0,
                                  migration_threshold=0.7)
        r1 = _make_region("r1", cohorts={"young": cohort}, bounds_=(0, 0, 100, 100))
        # r2: partial node (scarcity=0.6)
        r2 = _make_region("r2", bounds_=(100, 0, 200, 100))
        # r3: full node (scarcity=0.0) — adjacent via r1 top
        r3 = _make_region("r3", bounds_=(0, 100, 100, 200))

        depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
        partial = _make_node(2, (150.0, 50.0), remaining_charges=2, max_charges=5)  # 0.6 ratio → scarcity 0.4
        full = _make_node(3, (50.0, 150.0), remaining_charges=5, max_charges=5)     # scarcity 0.0
        state = _make_state_with_nodes(
            {"r1": r1, "r2": r2, "r3": r3},
            {1: depleted, 2: partial, 3: full},
        )

        result = DemographicCycleService.process_demographics(state, tick=200)

        # r3 has lower scarcity (0.0 < 0.4), so migrants go to r3
        assert "r3" in result.world_updates
        assert result.world_updates["r3"].population_cohorts_set["young"].count == 30
        # r2 receives no migrants
        assert "r2" not in result.world_updates

    def test_migration_off_cycle_no_op(self):
        """Migration does not fire on off-cycle ticks."""
        cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.0, mortality_rate=0.0,
                                  migration_threshold=0.7)
        r1 = _make_region("r1", cohorts={"young": cohort}, bounds_=(0, 0, 100, 100))
        r2 = _make_region("r2", bounds_=(100, 0, 200, 100))
        depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
        state = _make_state_with_nodes({"r1": r1, "r2": r2}, {1: depleted})

        result = DemographicCycleService.process_demographics(state, tick=199)

        assert result.is_noop()


# ---------------------------------------------------------------------------
# E52C: Age bracket classification — acceptance criterion
# ---------------------------------------------------------------------------

def test_age_bracket_returns_correct_bracket():
    """
    Acceptance criterion: test_age_bracket_returns_correct_bracket
    Boundary conditions for get_age_bracket:
      age_ticks < 3000  → "young"
      3000 ≤ age_ticks < 7000 → "adult"
      age_ticks ≥ 7000 → "elder"
    """
    # Young bracket
    assert get_age_bracket(0) == "young"
    assert get_age_bracket(1) == "young"
    assert get_age_bracket(2999) == "young"

    # Adult bracket
    assert get_age_bracket(3000) == "adult"
    assert get_age_bracket(5000) == "adult"
    assert get_age_bracket(6999) == "adult"

    # Elder bracket
    assert get_age_bracket(7000) == "elder"
    assert get_age_bracket(10000) == "elder"
    assert get_age_bracket(99999) == "elder"


# ---------------------------------------------------------------------------
# E52C: Elder modifier via AttributeUpdate — acceptance criterion
# ---------------------------------------------------------------------------

def test_elder_modifier_reduces_combat_effectiveness():
    """
    Acceptance criterion: test_elder_modifier_reduces_combat_effectiveness
    An elder entity (age_ticks=7000) with strength=10, agility=10 receives
    negative strength_delta and agility_delta in the returned EntityUpdate.
    Modifiers are applied via AttributeUpdate — no direct mutation of frozen state.
    """
    attrs = AttributeComponent(strength=10, agility=10)
    result = compute_elder_attribute_update(entity_id=42, attrs=attrs, age_ticks=7000)

    assert result is not None
    assert isinstance(result, EntityUpdate)
    assert result.entity_id == 42
    assert result.attributes is not None
    assert isinstance(result.attributes, AttributeUpdate)
    # combat_effectiveness *= 0.7 → STR and AGI reduced by 30%
    assert result.attributes.strength_delta < 0
    assert result.attributes.agility_delta < 0
    # Expected: -int(10 * 0.3) = -3
    assert result.attributes.strength_delta == -3
    assert result.attributes.agility_delta == -3


def test_non_elder_returns_none():
    """Non-elder entities (age_ticks < 7000) produce no modifier."""
    attrs = AttributeComponent(strength=10, agility=10)
    assert compute_elder_attribute_update(entity_id=1, attrs=attrs, age_ticks=0) is None
    assert compute_elder_attribute_update(entity_id=1, attrs=attrs, age_ticks=2999) is None
    assert compute_elder_attribute_update(entity_id=1, attrs=attrs, age_ticks=6999) is None


def test_elder_knowledge_bonus_positive():
    """Elder entity knowledge bonus: wisdom_delta > 0, charisma_delta > 0."""
    attrs = AttributeComponent(wisdom=10, charisma=10)
    result = compute_elder_attribute_update(entity_id=7, attrs=attrs, age_ticks=7000)

    assert result is not None
    # knowledge_reputation_weight *= 1.3 → WIS and CHA +30%
    assert result.attributes.wisdom_delta > 0
    assert result.attributes.charisma_delta > 0
    # Expected: int(10 * 0.3) = 3
    assert result.attributes.wisdom_delta == 3
    assert result.attributes.charisma_delta == 3


def test_elder_mortality_modifier_reduces_vitality_endurance():
    """Elder mortality_rate *= 2.0 → vitality and endurance reduced by 50%."""
    attrs = AttributeComponent(vitality=10, endurance=10)
    result = compute_elder_attribute_update(entity_id=5, attrs=attrs, age_ticks=9000)

    assert result is not None
    assert result.attributes.vitality_delta < 0
    assert result.attributes.endurance_delta < 0
    # Expected: -int(10 * 0.5) = -5
    assert result.attributes.vitality_delta == -5
    assert result.attributes.endurance_delta == -5


def test_elder_modifier_entity_id_preserved():
    """The EntityUpdate carries the correct entity_id."""
    attrs = AttributeComponent()
    result = compute_elder_attribute_update(entity_id=999, attrs=attrs, age_ticks=7000)
    assert result is not None
    assert result.entity_id == 999


# ---------------------------------------------------------------------------
# E52D: compute_population_density — TC-D5-01 through TC-D5-04
# ---------------------------------------------------------------------------

class TestComputePopulationDensity:
    """Tests for compute_population_density() pure function.

    Spec ref: TCK-20260619-E52D-DENSITY-SIGNAL §Scope
    """

    def _make_region(self, cohorts: dict | None = None, bounds: tuple = (0, 0, 100, 100)) -> RegionState:
        return RegionState(
            id="r1",
            name="Region r1",
            bounds=bounds,
            population_cohorts=cohorts or {},
        )

    def test_no_cohorts_returns_zero(self):
        """TC-D5-01: region with no cohorts → density = 0.0"""
        region = self._make_region(cohorts={})
        assert compute_population_density(region) == 0.0

    def test_single_bracket_density(self):
        """TC-D5-02: single bracket count=100, area=100×100=10000 → density=0.01"""
        cohort = PopulationCohort(bracket="adult", count=100)
        region = self._make_region(cohorts={"adult": cohort}, bounds=(0, 0, 100, 100))
        result = compute_population_density(region)
        assert result == pytest.approx(0.01)

    def test_all_brackets_summed(self):
        """TC-D5-03: young=50 + adult=100 + elder=25 = 175 total; area=100×100=10000 → density=0.0175"""
        cohorts = {
            "young": PopulationCohort(bracket="young", count=50),
            "adult": PopulationCohort(bracket="adult", count=100),
            "elder": PopulationCohort(bracket="elder", count=25),
        }
        region = self._make_region(cohorts=cohorts, bounds=(0, 0, 100, 100))
        result = compute_population_density(region)
        assert result == pytest.approx(0.0175)

    def test_degenerate_zero_area_no_division_error(self):
        """TC-D5-04: bounds=(0,0,0,0) → area=0 → clamped to max(1,0)=1 → no ZeroDivisionError"""
        cohort = PopulationCohort(bracket="young", count=10)
        region = self._make_region(cohorts={"young": cohort}, bounds=(0, 0, 0, 0))
        result = compute_population_density(region)
        # area=0 → max(1,0)=1 → density = 10 / 1 = 10.0
        assert result == pytest.approx(10.0)

    def test_high_pop_higher_density_than_low_pop(self):
        """Higher population count → higher density (same area)."""
        high_cohort = PopulationCohort(bracket="adult", count=500)
        low_cohort = PopulationCohort(bracket="adult", count=10)
        high_region = self._make_region(cohorts={"adult": high_cohort}, bounds=(0, 0, 100, 100))
        low_region = self._make_region(cohorts={"adult": low_cohort}, bounds=(0, 0, 100, 100))
        assert compute_population_density(high_region) > compute_population_density(low_region)

    def test_demand_multiplier_formula(self):
        """demand_multiplier = 1.0 + (density * 0.5); zero pop → multiplier = 1.0."""
        zero_cohort = PopulationCohort(bracket="adult", count=0)
        region_zero = self._make_region(cohorts={"adult": zero_cohort})
        density_zero = compute_population_density(region_zero)
        assert density_zero == 0.0
        multiplier_zero = 1.0 + (density_zero * 0.5)
        assert multiplier_zero == pytest.approx(1.0)

        # non-zero pop → multiplier > 1.0
        pop_cohort = PopulationCohort(bracket="adult", count=200)
        region_pop = self._make_region(cohorts={"adult": pop_cohort}, bounds=(0, 0, 100, 100))
        density_pop = compute_population_density(region_pop)
        multiplier_pop = 1.0 + (density_pop * 0.5)
        assert multiplier_pop > 1.0
