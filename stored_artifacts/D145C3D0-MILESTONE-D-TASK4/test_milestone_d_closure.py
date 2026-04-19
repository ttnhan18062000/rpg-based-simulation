import pytest
import time
import random
import threading
from typing import Dict, List
from unittest.mock import MagicMock

from src_v2.engine.kernel import Kernel
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.core.work import WorkItem, WorkClass
from src_v2.platform.rng import DeterministicRNG
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.core.worker_protocol import WorkerPacket, WorkerResult

def get_base_profile(workers: int) -> RuntimeProfile:
    return RuntimeProfile(
        name=f"PROFILE_{workers}",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=workers,
        max_queue_depth=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0,
        max_work_debt=1000
    )

def test_high_pressure_determinism_equivalence():
    """
    Final Certification: Bit-identical state after multi-tick high-pressure run.
    Forces non-deterministic completion noise via randomized delays.
    """
    total_entities = 50
    ticks_to_run = 10
    seed = 42
    
    # 1. Setup Initial State
    entities = {
        i: EntityState(id=i, kind="TEST", position=(i*0.1, i*0.1), readiness=1000.0)
        for i in range(total_entities)
    }
    state_init = AuthoritativeState(tick=0, seed=seed, entities=entities)
    
    # 2. RUN LOCAL (Control)
    profile_local = get_base_profile(0)
    kernel_local = Kernel(profile_local, state_init, DeterministicRNG(seed))
    
    # Custom worker for determinism check
    def deterministic_worker(packet: WorkerPacket) -> WorkerResult:
        from src_v2.core.updates import EntityUpdate
        from src_v2.core.worker_protocol import WorkerResult
        return WorkerResult(
            source_packet_id=packet.packet_id,
            work_id=packet.work_id,
            entity_id=packet.subject.id,
            work_class=packet.work_class,
            update=EntityUpdate(entity_id=packet.subject.id, readiness_delta=-float(packet.subject.id))
        )

    # Patch local manager
    original_execute_local = kernel_local._worker_manager.execute_batch
    kernel_local._worker_manager.execute_batch = lambda p, f, **k: original_execute_local(p, deterministic_worker, **k)

    for t in range(ticks_to_run):
        kernel_local._scheduler.select_work = MagicMock(return_value=([
            WorkItem(owner_id=i, work_id=f"tick{t}:w{i}", work_class=WorkClass.CRITICAL, work_kind="ENTITY_ACT")
            for i in range(total_entities)
        ], 0))
        kernel_local.tick_once()
    
    final_state_local = kernel_local.state

    # 3. RUN CONCURRENT (Chaos)
    kernel_concurrent = Kernel(get_base_profile(4), state_init, DeterministicRNG(seed))
    
    # Chaos Jumble wrapper
    def chaotic_worker(packet: WorkerPacket) -> WorkerResult:
        # Chaos noise
        delay = random.uniform(0.001, 0.02) # 1-20ms
        time.sleep(delay)
        return deterministic_worker(packet)

    # Patch concurrent manager
    original_execute_concurrent = kernel_concurrent._worker_manager.execute_batch
    kernel_concurrent._worker_manager.execute_batch = lambda p, f, **k: original_execute_concurrent(p, chaotic_worker, **k)

    for t in range(ticks_to_run):
        kernel_concurrent._scheduler.select_work = MagicMock(return_value=([
            WorkItem(owner_id=i, work_id=f"tick{t}:w{i}", work_class=WorkClass.CRITICAL, work_kind="ENTITY_ACT")
            for i in range(total_entities)
        ], 0))
        
        kernel_concurrent.tick_once()
        
    final_state_concurrent = kernel_concurrent.state

    # 4. CERTIFICATION: Bit-Identical Verification
    assert final_state_local.tick == final_state_concurrent.tick
    assert final_state_local.seed == final_state_concurrent.seed
    
    for eid in range(total_entities):
        loc = final_state_local.entities[eid]
        con = final_state_concurrent.entities[eid]
        assert loc.readiness == con.readiness, f"DIVERGENCE found at Entity {eid}"
        # Expected value: 1000 - (eid * ticks_to_run)
        assert loc.readiness == 1000.0 - (eid * ticks_to_run)

def test_neighbor_view_bit_identical():
    """Prove that worker input is identical regardless of execution mode."""
    profile = get_base_profile(0)
    entities = {
        i: EntityState(id=i, kind="TEST", position=(i*1.0, 0)) # Spread out
        for range_idx, i in enumerate([10, 5, 20, 1, 100])
    }
    state = AuthoritativeState(tick=1, seed=42, entities=entities)
    kernel = Kernel(profile, state, DeterministicRNG(42))
    
    # Subject is Entity 5. Radius 20.0 should see 1, 5, 10, 20.
    # But 5 is the subject, so neighbors are 1, 10, 20.
    subject = entities[5]
    view = kernel._get_deterministic_neighbor_view(subject, radius=20.0)
    
    # IDs should be [1, 10, 20]
    neighbor_ids = [eid for eid, estate in view]
    assert neighbor_ids == [1, 10, 20]
    
    # Now verify it's the same if we jumble the input dict (it shouldn't matter as it's sorted)
    shuffled_entities = dict(random.sample(list(entities.items()), len(entities)))
    kernel._state = AuthoritativeState(tick=1, seed=42, entities=shuffled_entities)
    view2 = kernel._get_deterministic_neighbor_view(subject, radius=20.0)
    assert [eid for eid, estate in view2] == [1, 10, 20]
