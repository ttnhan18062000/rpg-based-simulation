"""Integration tests for Epic 5.2B — Migration Pressure + Cohort Movement.

Ticket: TCK-20260619-E52B-MIGRATION
AC: test_cohort_migrates_on_scarcity
"""
from __future__ import annotations

import pytest

from src.core.state import AuthoritativeState, RegionState, ResourceNodeState
from src.domains.demographics.cohort import PopulationCohort, DemographicCycleService
from src.domains.world_emergence.schema import WorldEventCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_region(region_id: str, cohorts: dict | None = None, bounds_: tuple = (0, 0, 100, 100)) -> RegionState:
    return RegionState(
        id=region_id,
        name=f"Region {region_id}",
        bounds=bounds_,
        population_cohorts=cohorts or {},
    )


def _make_node(node_id: int, position: tuple, remaining_charges: int, max_charges: int = 5) -> ResourceNodeState:
    return ResourceNodeState(
        id=node_id,
        kind="WOOD",
        position=position,
        yields_item="wood_log",
        remaining_charges=remaining_charges,
        max_charges=max_charges,
        required_ticks=10,
    )


def _make_state(regions: dict, resource_nodes: dict | None = None) -> AuthoritativeState:
    return AuthoritativeState(
        tick=0,
        seed=42,
        regions=regions,
        resource_nodes=resource_nodes or {},
    )


# ---------------------------------------------------------------------------
# Integration: test_cohort_migrates_on_scarcity
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_cohort_migrates_on_scarcity():
    """
    Acceptance criterion: test_cohort_migrates_on_scarcity

    Two adjacent regions:
      r1: depleted resource (scarcity=1.0) → young cohort count=100, threshold=0.7 → migration fires
      r2: full resource (scarcity=0.0) → receives emigrants

    After process_demographics at tick=200:
      r1 young count = 70 (100 - 30)
      r2 young count = 30 (0 + 30)
      One POPULATION_MIGRATION event with region_id="r1"
    """
    cohort = PopulationCohort(bracket="young", count=100, birth_rate=0.0, mortality_rate=0.0,
                              migration_threshold=0.7)
    r1 = _make_region("r1", cohorts={"young": cohort}, bounds_=(0, 0, 100, 100))
    r2 = _make_region("r2", bounds_=(100, 0, 200, 100))

    depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
    full = _make_node(2, (150.0, 50.0), remaining_charges=5, max_charges=5)
    state = _make_state({"r1": r1, "r2": r2}, {1: depleted, 2: full})

    result = DemographicCycleService.process_demographics(state, tick=200)

    # Source region: cohort reduced by 30%
    assert "r1" in result.world_updates, "r1 must have a WorldUpdate with reduced cohort"
    r1_cohorts = result.world_updates["r1"].population_cohorts_set
    assert r1_cohorts is not None
    assert "young" in r1_cohorts
    assert r1_cohorts["young"].count == 70, f"Expected 70, got {r1_cohorts['young'].count}"

    # Target region: cohort increased by 30
    assert "r2" in result.world_updates, "r2 must have a WorldUpdate with absorbed emigrants"
    r2_cohorts = result.world_updates["r2"].population_cohorts_set
    assert r2_cohorts is not None
    assert "young" in r2_cohorts
    assert r2_cohorts["young"].count == 30, f"Expected 30, got {r2_cohorts['young'].count}"

    # Migration event emitted
    mig_events = [e for e in result.world_events_add
                  if e.category == WorldEventCategory.POPULATION_MIGRATION]
    assert len(mig_events) == 1, f"Expected 1 migration event, got {len(mig_events)}"
    assert mig_events[0].region_id == "r1"
    assert "young" in mig_events[0].subject


@pytest.mark.slow
def test_cohort_migrates_picks_lower_scarcity_target():
    """
    With two adjacent regions at different scarcity levels, migrants go to the
    region with lower scarcity (deterministic: ties broken by region id).

    r1: depleted → scarcity=1.0  (source, has cohort)
    r2: partial (2/5) → scarcity=0.6 (adjacent)
    r3: full (5/5) → scarcity=0.0 (adjacent, lower scarcity → receives migrants)
    """
    cohort = PopulationCohort(bracket="adult", count=100, birth_rate=0.0, mortality_rate=0.0,
                              migration_threshold=0.7)
    r1 = _make_region("r1", cohorts={"adult": cohort}, bounds_=(0, 0, 100, 100))
    r2 = _make_region("r2", bounds_=(100, 0, 200, 100))   # right of r1
    r3 = _make_region("r3", bounds_=(0, 100, 100, 200))   # above r1

    depleted = _make_node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)    # r1 scarcity=1.0
    partial = _make_node(2, (150.0, 50.0), remaining_charges=2, max_charges=5)    # r2 scarcity=0.6
    full = _make_node(3, (50.0, 150.0), remaining_charges=5, max_charges=5)       # r3 scarcity=0.0

    state = _make_state(
        {"r1": r1, "r2": r2, "r3": r3},
        {1: depleted, 2: partial, 3: full},
    )

    result = DemographicCycleService.process_demographics(state, tick=200)

    # r3 gets migrants (lower scarcity)
    assert "r3" in result.world_updates
    assert result.world_updates["r3"].population_cohorts_set["adult"].count == 30

    # r2 gets no migrants
    assert "r2" not in result.world_updates
