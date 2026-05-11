# Compliance IDs: INFRA-132
import pytest
from dataclasses import replace
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.engine.executor import LocalSequentialExecutor
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction

@pytest.fixture
def test_profile():
    return RuntimeProfile(
        name="EXECUTOR_TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=1000,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0
    )

def make_test_state(seed: int):
    # Multiple entities to make concurrency meaningful
    entities = {}
    for i in range(1, 6):
        entities[i] = (
            V2EntityBuilder(i)
            .kind("hero")
            .location(float(i*2), float(i*2))
            .identity(faction=Faction.HERO_GUILD)
            .combat(hp=100, alive=True, readiness=100.0)
            .lifecycle(active=True)
            .build()
        )
        # Give them WANDER to use RNG
        entities[i] = replace(entities[i], navigation=replace(entities[i].navigation, movement_mode=7))
        
    return AuthoritativeState(
        tick=0, 
        seed=seed, 
        entities=entities
    )

def test_sequential_vs_concurrent_determinism(test_profile):
    """
    Proves that running the same tick sequentially or concurrently 
    produces bit-identical results (INFRA-104, INFRA-132).
    """
    initial_state = make_test_state(42)
    
    # 1. Sequential Run
    rng_seq = DeterministicRNG(42)
    kernel_seq = Kernel(test_profile, initial_state, rng_seq, executor=LocalSequentialExecutor())
    kernel_seq.tick_once()
    hash_seq = kernel_seq.state.fingerprint()["state_hash"]
    
    # 2. Concurrent Run
    concurrent_profile = test_profile.model_copy(update={"max_worker_count": 4})
    rng_con = DeterministicRNG(42)
    # Kernel automatically creates ConcurrentExecutionAdapter if max_worker_count > 0
    kernel_con = Kernel(concurrent_profile, initial_state, rng_con) 
    kernel_con.tick_once()
    hash_con = kernel_con.state.fingerprint()["state_hash"]
    
    assert hash_seq == hash_con, "Sequential and Concurrent execution diverged!"

def test_concurrency_limit_stability(test_profile):
    """
    Proves that changing the concurrency limit does not change the result (INFRA-105).
    """
    initial_state = make_test_state(42)
    
    # Run 1: 1 worker
    profile1 = test_profile.model_copy(update={"max_worker_count": 1})
    rng1 = DeterministicRNG(42)
    kernel1 = Kernel(profile1, initial_state, rng1)
    kernel1.tick_once()
    hash1 = kernel1.state.fingerprint()["state_hash"]
    
    # Run 2: 4 workers
    profile2 = test_profile.model_copy(update={"max_worker_count": 4})
    rng2 = DeterministicRNG(42)
    kernel2 = Kernel(profile2, initial_state, rng2)
    kernel2.tick_once()
    hash2 = kernel2.state.fingerprint()["state_hash"]
    
    assert hash1 == hash2, "Concurrency level changed the simulation outcome!"
