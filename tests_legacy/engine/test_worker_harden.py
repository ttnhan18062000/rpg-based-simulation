import pytest
from src_legacy.engine.kernel import Kernel
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.core.work import WorkItem, WorkClass
from src_legacy.core.protocol_validator import ProtocolViolationError
from src_legacy.config.profiles import RuntimeProfile
from src_legacy.platform.rng import DeterministicRNG

def test_neighbor_view_sorting():
    """Prove that neighbor views are deterministic and sorted by entity_id."""
    profile = RuntimeProfile(
        name="test", 
        hardware_class="class_a", 
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=10.0
    )
    # 1. Setup entities in 2D space
    entities = {
        10: EntityState(id=10, kind="TEST", position=(1.0, 1.0)),
        50: EntityState(id=50, kind="TEST", position=(50.0, 50.0)), # Out
        5: EntityState(id=5, kind="TEST", position=(0.0, 0.0)),    # In
        20: EntityState(id=20, kind="TEST", position=(5.0, 5.0)), # In
    }
    # Subject is Entity 10
    state = AuthoritativeState(tick=1, seed=42, entities=entities)
    rng = DeterministicRNG(42)
    kernel = Kernel(profile, state, rng)
    
    view = kernel._get_deterministic_neighbor_view(entities[10], radius=10.0)
    
    # Expected: [5, 20] (Sorted by ID)
    assert len(view) == 2
    assert view[0][0] == 5
    assert view[1][0] == 20
    assert view[0][1].id == 5
    assert view[1][1].id == 20

def test_duplicate_entity_update_rejection():
    """Prove that Milestone D prohibits multiple authoritative results for the same entity."""
    profile = RuntimeProfile(
        name="test", 
        hardware_class="class_a", 
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=10.0
    )
    state = AuthoritativeState(tick=1, seed=42, entities={
        1: EntityState(id=1, kind="TEST", position=(0,0))
    })
    rng = DeterministicRNG(42)
    kernel = Kernel(profile, state, rng)
    
    from src_legacy.core.worker_protocol import WorkerResult, ResultStatus
    from src_legacy.core.updates import EntityUpdate
    
    # Simulate two results for Entity 1
    res1 = WorkerResult(
        source_packet_id="1:0", 
        work_id="1:1:ACT", 
        entity_id=1, 
        work_class=WorkClass.CRITICAL,
        update=EntityUpdate(entity_id=1)
    )
    res2 = WorkerResult(
        source_packet_id="1:1", 
        work_id="1:1:ACT2", 
        entity_id=1, 
        work_class=WorkClass.PERIODIC,
        update=EntityUpdate(entity_id=1)
    )
    
    kernel._final_results = [res1, res2]
    
    with pytest.raises(ProtocolViolationError, match="Duplicate authoritative result"):
        kernel._phase_resolution()

def test_priority_sorted_results():
    """Prove that outcomes are sorted by Class > Local > ID before application."""
    profile = RuntimeProfile(
        name="test", 
        hardware_class="class_a", 
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=10.0
    )
    state = AuthoritativeState(tick=1, seed=42, entities={})
    rng = DeterministicRNG(42)
    kernel = Kernel(profile, state, rng)
    
    from src_legacy.core.worker_protocol import WorkerResult
    from src_legacy.core.updates import EntityUpdate
    
    # 1. PERIODIC (10)
    # 2. CRITICAL (0) (Later ID)
    # 3. CRITICAL (0) (Earlier ID)
    res_p = WorkerResult(
        source_packet_id="1:0", work_id="w1", entity_id=10, work_class=WorkClass.PERIODIC,
        class_priority=10, update=EntityUpdate(entity_id=10)
    )
    res_c_later = WorkerResult(
        source_packet_id="1:1", work_id="w2", entity_id=20, work_class=WorkClass.CRITICAL,
        class_priority=0, update=EntityUpdate(entity_id=20)
    )
    res_c_earlier = WorkerResult(
        source_packet_id="1:2", work_id="w3", entity_id=5, work_class=WorkClass.CRITICAL,
        class_priority=0, update=EntityUpdate(entity_id=5)
    )
    
    kernel._final_results = [res_p, res_c_later, res_c_earlier]
    kernel._phase_resolution() # Triggers sort
    
    # Expected order: res_c_earlier, res_c_later, res_p
    assert kernel._final_results[0].entity_id == 5
    assert kernel._final_results[1].entity_id == 20
    assert kernel._final_results[2].entity_id == 10
