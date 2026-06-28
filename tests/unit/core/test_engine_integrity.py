import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, RegionState, BuildingState, InventoryComponent
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile
from src.platform.rng import DeterministicRNG
from src.engine.apply import ApplyPath

@pytest.fixture
def base_state():
    # Setup a basic world
    region = RegionState(
        id="r1",
        name="Region 1",
        bounds=(0, 0, 100, 100),
        hazard_level=0.1
    )
    
    return AuthoritativeState(
        tick=1,
        seed=12345,
        world_time=0,
        regions={"r1": region},
        next_entity_id=1,
        next_node_id=1000
    )

from src.config.profiles import RuntimeProfile, HardwareClass

def get_test_profile():
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=512,
        max_cpu_percent=50,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5,
        max_tick_budget_ms=100.0,
        sampling_interval_ticks=1
    )

@pytest.fixture
def base_state():
    # Setup a basic world
    region = RegionState(
        id="r1",
        name="Region 1",
        kind="FOREST", # Required for spawn pool
        bounds=(0, 0, 100, 100),
        hazard_level=0.1
    )
    
    return AuthoritativeState(
        tick=1,
        seed=12345,
        world_time=0,
        regions={"r1": region},
        next_entity_id=1,
        next_node_id=1000,
        terrain={(x,y): "FLOOR" for x in range(0,10) for y in range(0,10)} # Minimal terrain
    )

def test_bit_identical_determinism(base_state):
    """
    Law: Two kernels with same seed/state produce bit-identical results.
    """
    profile = get_test_profile()

    rng1 = DeterministicRNG(base_state.seed)
    kernel1 = Kernel(profile, base_state, rng1, flags={"audit_mode": True})
    rng2 = DeterministicRNG(base_state.seed)
    kernel2 = Kernel(profile, base_state, rng2, flags={"audit_mode": True})
    try:
        for _ in range(5):
            kernel1.tick_once()
        state1 = kernel1.state

        for _ in range(5):
            kernel2.tick_once()
        state2 = kernel2.state

        # Verify bit-identical fingerprints
        from src.engine.checkpoint import CanonicalStateHasher
        hash1 = CanonicalStateHasher.get_hash(state1)
        hash2 = CanonicalStateHasher.get_hash(state2)

        assert hash1 == hash2
        assert state1.tick == 6
        assert state2.tick == 6
    finally:
        kernel1.shutdown()
        kernel2.shutdown()

def test_id_generation_integrity(base_state):
    """
    Verify that next_entity_id and next_node_id increment correctly.
    [RPG-AUTH-005] Every world object is identified by a stable unique ID.
    """
    from src.systems.world_systems.generator import EntityGenerator
    from src.world.spawn import SpawnService
    from src.world.ecology import ResourceEcologyService
    
    generator = EntityGenerator(base_state.seed)
    
    # 1. Spawn some entities
    # Force spawn interval
    state = replace(base_state, tick=50) 
    spawn_upd = SpawnService.process_spawns(state, generator)
    
    assert len(spawn_upd.entities_add) > 0
    assert spawn_upd.next_entity_id_set is not None
    assert spawn_upd.next_entity_id_set > state.next_entity_id
    
    # 2. Apply and check state
    next_state = ApplyPath.apply_generation(state, spawn_upd)
    assert next_state.next_entity_id == spawn_upd.next_entity_id_set
    
    # 3. Spawn nodes
    # We need to make sure ResourceEcologyService will spawn something.
    # ResourceEcologyService probably needs a region with target nodes > current nodes.
    state_eco = replace(next_state, tick=100) # Assuming 100 is interval
    eco_upd = ResourceEcologyService.process_ecology(state_eco, generator)
    
    # Force a spawn if rng was unlucky
    if not eco_upd.nodes_add:
        from src.core.state import ResourceNodeState
        eco_upd = eco_upd.replace(
            nodes_add=[ResourceNodeState(
                id=state_eco.next_node_id, 
                kind="WOOD", 
                position=(0,0),
                yields_item="wood_log",
                remaining_charges=5,
                max_charges=5,
                required_ticks=10
            )],
            next_node_id_set=state_eco.next_node_id + 1
        )

    assert len(eco_upd.nodes_add) > 0
    assert eco_upd.next_node_id_set is not None
    assert eco_upd.next_node_id_set > next_state.next_node_id
    
    # 4. Apply and check state
    final_state = ApplyPath.apply_generation(state_eco, eco_upd)
    assert final_state.next_node_id == eco_upd.next_node_id_set

def test_isolation_guard_trigger(base_state):
    """
    Verify that the Kernel stability guard detects unauthorized mutation.
    """
    profile = get_test_profile()
    rng = DeterministicRNG(base_state.seed)
    kernel = Kernel(profile, base_state, rng, flags={"audit_mode": True})
    try:
        from src.core.protocol_validator import ProtocolViolationError
        prior_fp = kernel._state.fingerprint()
        # Directly mutate the state (violating frozen dataclass via object.__setattr__)
        # movement_count is part of the state_hash, tick is not.
        object.__setattr__(kernel._state, "movement_count", 999)

        with pytest.raises(ProtocolViolationError) as excinfo:
            kernel._guard_stability("MaliciousPhase", prior_fp)

        assert "Isolation Breach" in str(excinfo.value)
    finally:
        kernel.shutdown()


def test_gross_isolation_guard_triggers_on_tick_change(base_state):
    """
    Lightweight gross isolation guard (standard mode) detects tick advancement mid-phase.

    Covers: TCK-20260627-P1G-STABILITY-GUARD acceptance criterion — gross guard raises on
    tick mutation in standard (non-audit) mode.
    """
    profile = get_test_profile()
    rng = DeterministicRNG(base_state.seed)
    # Standard run — no audit_mode
    kernel = Kernel(profile, base_state, rng)
    try:
        from src.core.protocol_validator import ProtocolViolationError
        expected_count = len(kernel._state.entities)
        expected_tick = kernel._state.tick

        # Simulate a phase advancing the tick outside the authoritative pipeline
        object.__setattr__(kernel._state, "tick", expected_tick + 1)

        with pytest.raises(ProtocolViolationError) as excinfo:
            kernel._guard_gross_isolation("TestPhase", expected_count, expected_tick)

        assert "Gross Isolation Breach" in str(excinfo.value)
        assert "tick" in str(excinfo.value)
    finally:
        kernel.shutdown()


def test_gross_isolation_guard_triggers_on_entity_count_change(base_state):
    """
    Lightweight gross isolation guard (standard mode) detects entity creation mid-phase.

    Covers: TCK-20260627-P1G-STABILITY-GUARD acceptance criterion — gross guard raises on
    entity count change in standard (non-audit) mode.
    """
    profile = get_test_profile()
    rng = DeterministicRNG(base_state.seed)
    kernel = Kernel(profile, base_state, rng)
    try:
        from src.core.protocol_validator import ProtocolViolationError
        original_entities = dict(kernel._state.entities)
        expected_count = len(original_entities)
        expected_tick = kernel._state.tick

        # Simulate an entity being added outside the authoritative pipeline
        mutated_entities = dict(original_entities)
        mutated_entities[9999] = None  # sentinel — only count matters for this guard
        object.__setattr__(kernel._state, "entities", mutated_entities)

        try:
            with pytest.raises(ProtocolViolationError) as excinfo:
                kernel._guard_gross_isolation("TestPhase", expected_count, expected_tick)

            assert "Gross Isolation Breach" in str(excinfo.value)
            assert "entity count" in str(excinfo.value)
        finally:
            # Restore valid entities so shutdown's CanonicalStateHasher does not fail
            object.__setattr__(kernel._state, "entities", original_entities)
    finally:
        kernel.shutdown()


def test_gross_isolation_guard_silent_on_clean_state(base_state):
    """
    Gross isolation guard does not fire when state is clean (no mid-phase mutation).
    """
    profile = get_test_profile()
    rng = DeterministicRNG(base_state.seed)
    kernel = Kernel(profile, base_state, rng)
    try:
        expected_count = len(kernel._state.entities)
        expected_tick = kernel._state.tick
        # Should not raise — state is unchanged
        kernel._guard_gross_isolation("CleanPhase", expected_count, expected_tick)
    finally:
        kernel.shutdown()
