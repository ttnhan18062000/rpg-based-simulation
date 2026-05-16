import pytest
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL as SimulationProfile
from src.platform.rng import DeterministicRNG
from src.replay.fingerprint import StateFingerprinter
from src.engine.executor import LocalSequentialExecutor, ConcurrentExecutionAdapter
from src.engine.worker_manager import WorkerManager
from src.perf.scenarios import (
    build_idle_state, build_movement_state, build_resource_state,
    build_combat_arena_state, build_strategic_state
)

@pytest.fixture
def rng():
    return DeterministicRNG(42)

def run_parity_check(initial_state, seed=42, ticks=100, workers=4):
    """Helper to run both local and concurrent simulations and compare hashes."""
    # 1. Run Local Sequential
    local_executor = LocalSequentialExecutor()
    kernel_loc = Kernel(
        SimulationProfile, 
        initial_state, 
        DeterministicRNG(seed), 
        executor=local_executor,
        flags={"audit_mode": True, "no_frame_pacing": True, "no_replay": True}
    )
    for _ in range(ticks):
        kernel_loc.tick_once()
    
    hash_loc = StateFingerprinter.get_fingerprint(kernel_loc._state)['state_hash']
    
    # 2. Run Concurrent
    worker_manager = WorkerManager(max_workers=workers)
    concurrent_executor = ConcurrentExecutionAdapter(worker_manager)
    kernel_con = Kernel(
        SimulationProfile, 
        initial_state, 
        DeterministicRNG(seed), 
        executor=concurrent_executor,
        flags={"audit_mode": True, "no_frame_pacing": True, "no_replay": True}
    )
    for _ in range(ticks):
        kernel_con.tick_once()
        
    hash_con = StateFingerprinter.get_fingerprint(kernel_con._state)['state_hash']
    worker_manager.shutdown()
    
    return hash_loc, hash_con

@pytest.mark.perf
def test_local_vs_concurrent_idle_parity_100_ticks():
    state = build_idle_state(entity_count=50)
    h_loc, h_con = run_parity_check(state, ticks=100)
    assert h_loc == h_con, "Idle scenario parity failed"

@pytest.mark.perf
def test_local_vs_concurrent_movement_parity_100_ticks():
    state = build_movement_state(entity_count=20)
    h_loc, h_con = run_parity_check(state, ticks=100)
    assert h_loc == h_con, "Movement scenario parity failed"

@pytest.mark.perf
def test_local_vs_concurrent_resource_parity_100_ticks():
    state = build_resource_state(entity_count=20, node_count=5)
    h_loc, h_con = run_parity_check(state, ticks=100)
    assert h_loc == h_con, "Resource scenario parity failed"

@pytest.mark.perf
def test_local_vs_concurrent_combat_parity_100_ticks():
    state = build_combat_arena_state(team_a_count=5, team_b_count=5)
    h_loc, h_con = run_parity_check(state, ticks=100)
    assert h_loc == h_con, "Combat scenario parity failed"

@pytest.mark.perf
def test_local_vs_concurrent_strategic_parity_100_ticks():
    state = build_strategic_state(entity_count=10)
    h_loc, h_con = run_parity_check(state, ticks=100)
    assert h_loc == h_con, "Strategic scenario parity failed"

@pytest.mark.parametrize("entity_count", [49, 50, 51, 99, 100, 101])
def test_worker_chunk_boundary_determinism(entity_count, rng):
    """
    Verifies that chunk-size boundaries in WorkerManager don't affect results.
    """
    state = build_idle_state(entity_count=entity_count)
    h_loc, h_con = run_parity_check(state, ticks=10, workers=4)
    assert h_loc == h_con, f"Chunk boundary parity failed for {entity_count} entities"
