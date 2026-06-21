"""Integration tests for Epic 5.2B–E52D — Migration Pressure + Cohort Movement + Density Signal.

Tickets: TCK-20260619-E52B-MIGRATION, TCK-20260619-E52D-DENSITY-SIGNAL
AC: test_cohort_migrates_on_scarcity, test_2000_tick_run_produces_cohort_demographic_change
"""
from __future__ import annotations

import pytest

from src.core.state import AuthoritativeState, RegionState, ResourceNodeState
from src.domains.demographics.cohort import (
    PopulationCohort,
    DemographicCycleService,
    compute_population_density,
)
from src.domains.world_emergence.schema import WorldEventCategory, WorldEventAggregate
from src.domains.world_emergence.models import RegionalPressureModel


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


# ---------------------------------------------------------------------------
# E52D: Density signal integration tests
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_2000_tick_run_produces_cohort_demographic_change():
    """
    AC test: TCK-20260619-E52D-DENSITY-SIGNAL

    Runs DemographicCycleService for 2000 ticks (10 cycles at COHORT_INTERVAL=200).
    Region has birth_rate > mortality_rate so population grows each cycle.

    Verifies:
    1. Cohort count changes over 2000 ticks (demographic cycle is active).
    2. A high-population region produces demand_multiplier > 1.0 via
       compute_population_density() → reflecting density signal is wired.
    3. A zero-population region produces demand_multiplier == 1.0.
    """
    from dataclasses import replace as dc_replace

    # Set up region with growing population
    cohort = PopulationCohort(
        bracket="adult",
        count=1000,
        birth_rate=0.05,    # 5% births per cycle
        mortality_rate=0.01, # 1% deaths per cycle → net +4% per cycle
        migration_threshold=1.1,  # above 1.0 — no migration fires
    )
    r_growing = _make_region("r_growing", cohorts={"adult": cohort}, bounds_=(0, 0, 100, 100))
    r_empty = _make_region("r_empty", cohorts={}, bounds_=(200, 0, 300, 100))

    state = _make_state({"r_growing": r_growing, "r_empty": r_empty})

    # Advance 2000 ticks (10 full COHORT_INTERVAL cycles)
    current_state = state
    for tick in range(1, 2001):
        result = DemographicCycleService.process_demographics(current_state, tick=tick)
        if not result.is_noop():
            # Apply cohort updates to state so next cycle sees updated counts
            new_regions = dict(current_state.regions)
            for rid, wu in result.world_updates.items():
                if wu.population_cohorts_set is not None and rid in new_regions:
                    new_regions[rid] = dc_replace(
                        new_regions[rid],
                        population_cohorts=wu.population_cohorts_set,
                    )
            current_state = dc_replace(current_state, tick=tick, regions=new_regions)

    # 1. Growing cohort has changed count (grown over 10 cycles)
    final_count = current_state.regions["r_growing"].population_cohorts["adult"].count
    assert final_count > 1000, f"Expected growth beyond 1000, got {final_count}"

    # 2. High-population region density > 0 → demand_multiplier > 1.0
    density_growing = compute_population_density(current_state.regions["r_growing"])
    assert density_growing > 0.0, "Growing region must have positive density"
    demand_multiplier_growing = 1.0 + (density_growing * 0.5)
    assert demand_multiplier_growing > 1.0, (
        f"High-population region demand_multiplier must exceed 1.0, got {demand_multiplier_growing}"
    )

    # 3. Empty region density == 0 → demand_multiplier == 1.0
    density_empty = compute_population_density(current_state.regions["r_empty"])
    assert density_empty == 0.0
    demand_multiplier_empty = 1.0 + (density_empty * 0.5)
    assert demand_multiplier_empty == pytest.approx(1.0)


@pytest.mark.slow
def test_high_population_region_higher_resource_demand():
    """
    AC test: high-population region generates measurably higher resource pressure
    than zero-population region via RegionalPressureModel.

    Both regions have identical harvesting activity.
    High-pop region → demand_multiplier > 1.0 → higher resource pressure intensity.
    Zero-pop region → demand_multiplier == 1.0 → baseline resource pressure intensity.
    """
    from src.domains.world_emergence.schema import WorldEventAggregate, WorldEventCategory

    cohort = PopulationCohort(bracket="adult", count=2000)
    r_high_pop = _make_region("r_high", cohorts={"adult": cohort}, bounds_=(0, 0, 100, 100))
    r_zero_pop = _make_region("r_zero", cohorts={}, bounds_=(200, 0, 300, 100))

    state = _make_state({"r_high": r_high_pop, "r_zero": r_zero_pop})

    # Both regions have identical harvesting activity (5 harvests, 1 depletion)
    aggregates = (
        WorldEventAggregate(
            region_id="r_high",
            category=WorldEventCategory.RESOURCE_HARVESTED,
            subject="wood",
            count=5,
            severity_sum=1.0,
            first_tick=1,
            last_tick=100,
        ),
        WorldEventAggregate(
            region_id="r_high",
            category=WorldEventCategory.RESOURCE_DEPLETED,
            subject="wood",
            count=1,
            severity_sum=1.0,
            first_tick=50,
            last_tick=100,
        ),
        WorldEventAggregate(
            region_id="r_zero",
            category=WorldEventCategory.RESOURCE_HARVESTED,
            subject="wood",
            count=5,
            severity_sum=1.0,
            first_tick=1,
            last_tick=100,
        ),
        WorldEventAggregate(
            region_id="r_zero",
            category=WorldEventCategory.RESOURCE_DEPLETED,
            subject="wood",
            count=1,
            severity_sum=1.0,
            first_tick=50,
            last_tick=100,
        ),
    )

    pressures = RegionalPressureModel.evaluate(state, aggregates)

    high_resource = next(
        (p for p in pressures if p.region_id == "r_high" and p.pressure_kind == "resource"),
        None,
    )
    zero_resource = next(
        (p for p in pressures if p.region_id == "r_zero" and p.pressure_kind == "resource"),
        None,
    )

    assert high_resource is not None, "r_high must have a resource pressure"
    assert zero_resource is not None, "r_zero must have a resource pressure"

    assert high_resource.intensity > zero_resource.intensity, (
        f"High-pop region resource intensity ({high_resource.intensity:.4f}) must exceed "
        f"zero-pop region ({zero_resource.intensity:.4f})"
    )
    # Verify density_mult is recorded in source_aggregates
    assert any("density_mult" in s for s in high_resource.source_aggregates), (
        "density_mult must appear in source_aggregates for traceability"
    )
