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
from src_v2.engine.worker_logic import default_simulation_worker

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
    Uses REAL domain logic (Movement) and forces non-deterministic completion noise.
    """
    total_entities = 40
    ticks_to_run = 5
    seed = 42
    
    # 1. Setup Initial State
    entities = {
        i: EntityState(id=i, kind="TEST", position=(float(i), 0.0), readiness=1000.0)
        for i in range(1, total_entities + 1)
    }
    state_init = AuthoritativeState(tick=0, seed=seed, entities=entities)
    
    # Target positions for movement: all move towards (100.0, 100.0)
    target = (100.0, 100.0)

    # 2. RUN LOCAL (Control)
    profile_local = get_base_profile(0)
    kernel_local = Kernel(profile_local, state_init, DeterministicRNG(seed))
    
    for t in range(ticks_to_run):
        # Schedule MOVE for even, ACT for odd entities
        work = []
        for i in range(1, total_entities + 1):
            if i % 2 == 0:
                work.append(WorkItem(owner_id=i, work_id=f"t{t}:w{i}", work_class=WorkClass.CRITICAL, 
                                     work_kind="ENTITY_MOVE", payload={"target_position": target}))
            else:
                work.append(WorkItem(owner_id=i, work_id=f"t{t}:w{i}", work_class=WorkClass.CRITICAL, 
                                     work_kind="ENTITY_ACT"))
        
        kernel_local._scheduler.select_work = MagicMock(return_value=(work, 0))
        kernel_local.tick_once()
    
    final_state_local = kernel_local.state

    # 3. RUN CONCURRENT (Chaos)
    kernel_concurrent = Kernel(get_base_profile(4), state_init, DeterministicRNG(seed))
    
    # Patch WorkerManager to inject CHAOS TIMING but keep REAL worker logic
    original_execute = kernel_concurrent._worker_manager.execute_batch
    def chaotic_execute(packets, worker_fn, **kwargs):
        # Injected noise
        def noisy_worker_wrapper(p):
            time.sleep(random.uniform(0.001, 0.01))
            return default_simulation_worker(p)
        return original_execute(packets, noisy_worker_wrapper, **kwargs)
    
    kernel_concurrent._worker_manager.execute_batch = chaotic_execute

    for t in range(ticks_to_run):
        work = []
        for i in range(1, total_entities + 1):
            if i % 2 == 0:
                work.append(WorkItem(owner_id=i, work_id=f"t{t}:w{i}", work_class=WorkClass.CRITICAL, 
                                     work_kind="ENTITY_MOVE", payload={"target_position": target}))
            else:
                work.append(WorkItem(owner_id=i, work_id=f"t{t}:w{i}", work_class=WorkClass.CRITICAL, 
                                     work_kind="ENTITY_ACT"))
        
        kernel_concurrent._scheduler.select_work = MagicMock(return_value=(work, 0))
        kernel_concurrent.tick_once()
        
    final_state_concurrent = kernel_concurrent.state

    # 4. CERTIFICATION: Bit-Identical Verification
    assert final_state_local.tick == final_state_concurrent.tick
    
    for eid in range(1, total_entities + 1):
        loc = final_state_local.entities[eid]
        con = final_state_concurrent.entities[eid]
        
        # Readiness check
        assert loc.readiness == con.readiness, f"Readiness DIVERGENCE at Entity {eid}"
        # Position check (The real domain slice proof)
        assert loc.position == con.position, f"Position DIVERGENCE at Entity {eid}"
        
        if eid % 2 == 0:
            # Should have moved from (eid, 0) towards (100, 100)
            assert loc.position != (float(eid), 0.0)
            assert loc.readiness == 1000.0 - (50.0 * ticks_to_run)
        else:
            # Should have stayed at (eid, 0)
            assert loc.position == (float(eid), 0.0)
            assert loc.readiness == 1000.0 - (100.0 * ticks_to_run)

def test_neighbor_view_bit_identical():
    """Prove that worker input context is identical regardless of engine internal order."""
    profile = get_base_profile(0)
    entities = {
        i: EntityState(id=i, kind="TEST", position=(float(i), 0.0))
        for i in [10, 5, 20, 1, 100]
    }
    state = AuthoritativeState(tick=1, seed=42, entities=entities)
    kernel = Kernel(profile, state, DeterministicRNG(42))
    
    subject = entities[5]
    view = kernel._get_deterministic_neighbor_view(subject, radius=20.0)
    neighbor_ids = [eid for eid, estate in view]
    assert neighbor_ids == [1, 10, 20]
