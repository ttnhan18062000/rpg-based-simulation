import pytest
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.platform.rng import DeterministicRNG
from src_v2.engine.kernel import Kernel
from src_v2.core.work import WorkItem, WorkClass
from unittest.mock import MagicMock


def test_concurrency_determinism_equivalence():
    """
    M8 Law: Local Execution == Concurrent Execution.
    Verifies that bit-identical authoritative state is produced regardless 
    of worker count, given the same seed and inputs.
    """
    profile_local = RuntimeProfile(
        name="LOCAL", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=0, # SEQUENTIAL
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )
    
    profile_concurrent = RuntimeProfile(
        name="CONCURRENT", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=4, # PARALLEL
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )
    
    # Setup identical initial state
    entities = {
        i: EntityState(id=i, kind="TEST", position=(0,0), readiness=100.0)
        for i in range(10)
    }
    state_start = AuthoritativeState(tick=0, seed=42, entities=entities)
    
    # 1. Run Locally
    kernel_local = Kernel(profile_local, state_start, DeterministicRNG(42))
    # Mock scheduler to return 10 items
    kernel_local._scheduler.select_work = MagicMock(return_value=[
        WorkItem(owner_id=i, work_class=WorkClass.CRITICAL, action_type="ENTITY_ACT")
        for i in range(10)
    ])
    kernel_local.tick_once()
    final_state_local = kernel_local.state
    
    # 2. Run Concurrently
    kernel_concurrent = Kernel(profile_concurrent, state_start, DeterministicRNG(42))
    kernel_concurrent._scheduler.select_work = MagicMock(return_value=[
        WorkItem(owner_id=i, work_class=WorkClass.CRITICAL, action_type="ENTITY_ACT")
        for i in range(10)
    ])
    kernel_concurrent.tick_once()
    final_state_concurrent = kernel_concurrent.state
    
    # VERIFY: Bit-identical outcomes
    assert final_state_local.tick == final_state_concurrent.tick
    for eid in range(10):
        assert final_state_local.entities[eid].readiness == final_state_concurrent.entities[eid].readiness
        assert final_state_local.entities[eid].readiness == 0.0 # Standard -100 delta


def test_race_resistance_via_sorting():
    """
    Verify that results are sorted by ID so that application order 
    is independent of thread completion noise.
    """
    from src_v2.engine.worker_manager import WorkerManager
    from src_v2.core.worker_protocol import WorkerPacket, WorkerResult
    from src_v2.core.updates import EntityUpdate
    import time
    import random
    
    manager = WorkerManager(max_workers=4)
    
    def slow_worker(packet: WorkerPacket) -> WorkerResult:
        # Artificial delay based on ID to jumble completion order
        # Lower IDs sleep longer so they should finish LATER
        delay = (10 - packet.subject.id) * 0.01 
        time.sleep(delay)
        return WorkerResult(entity_id=packet.subject.id, update=EntityUpdate(entity_id=packet.subject.id, readiness_delta=packet.subject.id))

    packets = [
        WorkerPacket(tick=0, world_time=0, seed=i, subject=MagicMock(id=i), neighbor_view={}, action_type="ACT", payload={})
        for i in range(1, 6) # IDs 1 to 5
    ]
    
    results = manager.execute_batch(packets, slow_worker)
    
    # VERIFY: Results are sorted by ID 1, 2, 3, 4, 5
    # Even though ID 5 finished much earlier than ID 1.
    result_ids = [r.entity_id for r in results]
    assert result_ids == [1, 2, 3, 4, 5]
