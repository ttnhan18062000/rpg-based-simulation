import pytest
import copy
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL as SimulationProfile
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.core.strategic import ProjectStatus, ObjectiveStatus
from src.replay.fingerprint import StateFingerprinter

@pytest.fixture
def rng():
    return DeterministicRNG(42)

def add_entity(state, entity):
    new_ents = dict(state.entities)
    new_ents[entity.id] = entity
    from dataclasses import replace
    return replace(state, entities=new_ents)

def setup_complex_world(rng):
    """Set up a world with multiple entities and some initial state."""
    state = AuthoritativeState(tick=0, seed=42)
    
    # 1. Add some entities with projects and needs
    builder = V2EntityBuilder(1).navigation(position=(10.0, 10.0)).lifecycle(active=True).combat(alive=True)
    builder.cognition(interruption_resistance=0.5)
    # Add a project
    from src.core.strategic import ProjectState, ObjectiveState, ObjectiveKind, ProjectKind
    obj = ObjectiveState(id="obj1", kind=ObjectiveKind.REACH_LOCATION, target="20.0,20.0", status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(id="proj1", kind=ProjectKind.QUEST, status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id="obj1", score=100.0)
    builder.strategic(
        projects={proj.id: proj}, 
        current_project_id=proj.id, 
        current_objective_id=proj.active_objective_id
    )
    state = add_entity(state, builder.build())
    
    # 2. Add another entity for grouping
    builder2 = V2EntityBuilder(2).navigation(position=(11.0, 11.0)).lifecycle(active=True).combat(alive=True)
    state = add_entity(state, builder2.build())
    
    # 3. Add a resource node
    from src.core.state import ResourceNodeState
    node = ResourceNodeState(
        id=1, kind="WOOD", position=(5, 5), 
        yields_item="wood_log", remaining_charges=10, 
        max_charges=10, required_ticks=5
    )
    new_nodes = dict(state.resource_nodes)
    new_nodes[node.id] = node
    state = copy.copy(state)
    object.__setattr__(state, "resource_nodes", new_nodes)
    
    return state

@pytest.mark.perf
@pytest.mark.slow
def test_dirty_set_vs_full_scan_parity(rng):
    """
    Milestone 3: O(Dirty) vs O(N) Reference Parity.
    Verifies that the optimized DirtySet-based path produce bit-identical results
    compared to the full-scan reference path.
    """
    initial_state = setup_complex_world(rng)
    ticks_to_run = 100
    
    # 1. Run Optimized (Default)
    kernel_opt = Kernel(SimulationProfile, initial_state, DeterministicRNG(42))
    # 2. Run Full Scan (Reference) — created early so both are shut down together
    kernel_ref = Kernel(SimulationProfile, initial_state, DeterministicRNG(42), flags={"force_full_scan": True})
    try:
        for _ in range(ticks_to_run):
            kernel_opt.tick_once()

        final_state_opt = kernel_opt._state
        fingerprint_opt = StateFingerprinter.get_fingerprint(final_state_opt)

        # We use a fresh RNG with the SAME seed to ensure determinism
        for _ in range(ticks_to_run):
            kernel_ref.tick_once()

        final_state_ref = kernel_ref._state
        fingerprint_ref = StateFingerprinter.get_fingerprint(final_state_ref)

        # 3. Compare
        print(f"Optimized Hash: {fingerprint_opt['state_hash']}")
        print(f"Reference Hash: {fingerprint_ref['state_hash']}")

        # If hashes differ, we need to find out why
        if fingerprint_opt['state_hash'] != fingerprint_ref['state_hash']:
            # Check some basic fields first
            assert final_state_opt.tick == final_state_ref.tick
            assert len(final_state_opt.entities) == len(final_state_ref.entities)

            # Check entities one by one
            for eid in sorted(final_state_opt.entities.keys()):
                e_opt = final_state_opt.entities[eid]
                e_ref = final_state_ref.entities[eid]

                if e_opt.navigation.position != e_ref.navigation.position:
                    pytest.fail(f"Entity {eid} position mismatch: {e_opt.navigation.position} vs {e_ref.navigation.position}")

                if e_opt.strategic.current_project_id != e_ref.strategic.current_project_id:
                    pytest.fail(f"Entity {eid} project mismatch: {e_opt.strategic.current_project_id} vs {e_ref.strategic.current_project_id}")

        assert fingerprint_opt['state_hash'] == fingerprint_ref['state_hash'], "Optimized vs Full Scan parity failed!"
    finally:
        kernel_opt.shutdown()
        kernel_ref.shutdown()
