from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.engine.checkpoint import CanonicalStateHasher
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole

def test_reproducibility():
    """Seed 42, 10 ticks, must yield identical final hashes across 10 runs."""
    hashes = []
    
    profile = RuntimeProfile(
        name="det-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )

    for _ in range(10):
        # Initial state with some entities to increase complexity
        e1 = V2EntityBuilder(1).location(0.0, 0.0).identity(role=EntityRole.HERO).build()
        e2 = V2EntityBuilder(2).location(5.0, 5.0).identity(role=EntityRole.MONSTER).build()
        
        state = AuthoritativeState(tick=0, seed=42, world_time=0, entities={
            1: e1,
            2: e2
        })
        rng = DeterministicRNG(42)
        kernel = Kernel(profile, state, rng)
        
        # Run 10 ticks
        for _ in range(10):
            kernel.tick_once()
            
        hashes.append(CanonicalStateHasher.get_hash(kernel._state))
        
    # All hashes must be identical
    assert len(set(hashes)) == 1
    assert hashes[0] is not None


def test_seed_divergence():
    """Different seeds must yield different hashes (unless collision)."""
    state1 = AuthoritativeState(tick=0, seed=1, world_time=0)
    state2 = AuthoritativeState(tick=0, seed=2, world_time=0)
    
    hash1 = CanonicalStateHasher.get_hash(state1)
    hash2 = CanonicalStateHasher.get_hash(state2)
    
    assert hash1 != hash2


def test_canonical_sorting_stability():
    """Verify that dict key order does not affect the hash."""
    e1 = V2EntityBuilder(1).location(0.0, 0.0).identity(role=EntityRole.HERO).build()
    e2 = V2EntityBuilder(2).location(1.0, 1.0).identity(role=EntityRole.MONSTER).build()

    state_a = AuthoritativeState(tick=1, seed=1, entities={
        1: e1,
        2: e2
    })
    
    # Manually swapped order in dictionary construction for state_b
    state_b = AuthoritativeState(tick=1, seed=1, entities={
        2: e2,
        1: e1
    })
    
    hash_a = CanonicalStateHasher.get_hash(state_a)
    hash_b = CanonicalStateHasher.get_hash(state_b)
    
    assert hash_a == hash_b


def test_local_vs_concurrent_equivalence():
    """
    Law: The local baseline and concurrent adapter must yield identical results.
    Proof: Same seed, same state, different executors -> same final hash.
    """
    from src.engine.executor import LocalSequentialExecutor
    
    profile = RuntimeProfile(
        name="equivalence-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=100.0
    )
    
    e1 = V2EntityBuilder(1).location(0.0, 0.0).identity(role=EntityRole.HERO).combat(readiness=100.0).build()
    e2 = V2EntityBuilder(2).location(5.0, 5.0).identity(role=EntityRole.MONSTER).combat(readiness=100.0).build()

    initial_state = AuthoritativeState(tick=0, seed=42, world_time=0, entities={
        1: e1,
        2: e2
    })
    
    # 1. Run with LocalSequentialExecutor
    kernel_local = Kernel(profile, initial_state, DeterministicRNG(42), executor=LocalSequentialExecutor())
    for _ in range(5):
        kernel_local.tick_once()
    hash_local = CanonicalStateHasher.get_hash(kernel_local._state)
    
    # 2. Run with ConcurrentExecutionAdapter (Single worker)
    # Note: ConcurrentExecutionAdapter uses Kernel's worker manager
    kernel_concurrent = Kernel(profile, initial_state, DeterministicRNG(42))
    # By default, kernel with max_worker_count=1 uses ConcurrentExecutionAdapter
    for _ in range(5):
        kernel_concurrent.tick_once()
    hash_concurrent = CanonicalStateHasher.get_hash(kernel_concurrent._state)
    
    assert hash_local == hash_concurrent, "DIVERGENCE: Local and Concurrent paths produced different hashes!"
