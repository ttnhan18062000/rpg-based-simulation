# Compliance IDs: RPG-OPT-PHASE-GRAPH, PERF-016
import pytest
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.core.dirty import DirtySet
from src.engine.cadence import SystemCadence
from src.engine.phase_graph import PhaseDependencyGraph, PhaseMetadata


def test_phase_metadata_definitions():
    """Verify all 17 authoritative phases are correctly registered with expected flags."""
    assert len(PhaseDependencyGraph.PHASES) >= 17
    
    compactor = PhaseDependencyGraph.PHASES["compactor"]
    assert compactor.must_run_every_tick is True
    assert "all" in compactor.input_domains
    
    sabotage = PhaseDependencyGraph.PHASES["building_sabotage"]
    assert sabotage.must_run_every_tick is False
    assert sabotage.cadence_property == "building_sabotage"
    assert "combat" in sabotage.input_domains


def test_should_run_must_run_phases():
    """Verify that unconditional phases always run even on perfectly clean ticks."""
    state = AuthoritativeState(tick=10, seed=123, world_time=1000, entities={})
    clean_dirty = DirtySet()
    update = StateUpdate(dirty_set=clean_dirty)
    cadence = SystemCadence()

    assert PhaseDependencyGraph.should_run_phase("compactor", state, update, cadence) is True
    assert PhaseDependencyGraph.should_run_phase("trust_boundary", state, update, cadence) is True
    assert PhaseDependencyGraph.should_run_phase("actor_validity", state, update, cadence) is True
    assert PhaseDependencyGraph.should_run_phase("lifecycle", state, update, cadence) is True


def test_force_full_scan_overrides_skips():
    """Verify that force_full_scan forces execution of optional phases."""
    state = AuthoritativeState(tick=10, seed=123, world_time=1000, entities={})
    clean_dirty = DirtySet()
    cadence = SystemCadence()

    # With clean dirty set, optional phase position_swaps should skip
    clean_update = StateUpdate(dirty_set=clean_dirty, force_full_scan=False)
    assert PhaseDependencyGraph.should_run_phase("position_swaps", state, clean_update, cadence) is False

    # With force_full_scan=True, it must run
    full_update = StateUpdate(dirty_set=clean_dirty, force_full_scan=True)
    assert PhaseDependencyGraph.should_run_phase("position_swaps", state, full_update, cadence) is True

    # With state._force_full_scan=True, it must run
    class MockState:
        tick = 10
        _force_full_scan = True

    assert PhaseDependencyGraph.should_run_phase("position_swaps", MockState(), clean_update, cadence) is True


def test_cadence_gating_prevention():
    """Verify that cadence gating correctly prevents execution on quiet ticks."""
    # Set building_sabotage cadence to 100
    cadence = SystemCadence(building_sabotage=100)
    dirty = DirtySet(combat_entities={1})
    update = StateUpdate(dirty_set=dirty)

    # Tick 50 is not divisible by 100 -> should skip
    state_quiet = AuthoritativeState(tick=50, seed=123, world_time=5000, entities={})
    assert PhaseDependencyGraph.should_run_phase("building_sabotage", state_quiet, update, cadence) is False

    # Tick 100 is divisible by 100 -> should run
    state_active = AuthoritativeState(tick=100, seed=123, world_time=10000, entities={})
    assert PhaseDependencyGraph.should_run_phase("building_sabotage", state_active, update, cadence) is True


def test_dirty_set_short_circuiting():
    """Verify that optional phases skip when their required dirty domains are empty."""
    state = AuthoritativeState(tick=10, seed=123, world_time=1000, entities={})
    cadence = SystemCadence()

    # Update with only inventory dirty
    dirty_inv = DirtySet(inventory_entities={101})
    update_inv = StateUpdate(dirty_set=dirty_inv)

    # blacksmith requires inventory, movement, or town -> should run
    assert PhaseDependencyGraph.should_run_phase("blacksmith", state, update_inv, cadence) is True

    # position_swaps requires movement -> should skip
    assert PhaseDependencyGraph.should_run_phase("position_swaps", state, update_inv, cadence) is False

    # Update with movement dirty
    dirty_mov = DirtySet(movement_entities={101})
    update_mov = StateUpdate(dirty_set=dirty_mov)

    # position_swaps should now run
    assert PhaseDependencyGraph.should_run_phase("position_swaps", state, update_mov, cadence) is True
