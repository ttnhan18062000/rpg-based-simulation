import pytest
import time
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.checkpoint import CanonicalStateHasher
from src.core.builder import V2EntityBuilder

@pytest.fixture
def base_profile():
    return RuntimeProfile(
        name="equivalence_test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=512,
        max_cpu_percent=80,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10,
        max_tick_budget_ms=16.6
    )

@pytest.fixture
def dual_kernel_setup(base_profile):
    """Create two identical kernels to prove local vs concurrent equivalence."""
    # Kernel 1: Local Mode (0 workers)
    state1 = AuthoritativeState(tick=0, seed=42)
    rng1 = DeterministicRNG(42)
    k_local = Kernel(profile=base_profile.model_copy(update={"max_worker_count": 0}), state=state1, rng=rng1)
    
    # Kernel 2: Concurrent Mode (4 workers)
    state2 = AuthoritativeState(tick=0, seed=42)
    rng2 = DeterministicRNG(42)
    k_concurrent = Kernel(profile=base_profile, state=state2, rng=rng2)
    
    return k_local, k_concurrent

def test_authoritative_equivalence(dual_kernel_setup):
    """M8 Law: Local and Concurrent execution produce identical authoritative hashes."""
    k_local, k_concurrent = dual_kernel_setup
    
    # Setup some initial entities to generate work
    for i in range(1, 11):
        ent = V2EntityBuilder(i).at((float(i), 0.0)).active(True).build()
        k_local._state.entities[i] = ent
        k_concurrent._state.entities[i] = ent
        
    # Run 10 ticks and compare hashes
    for tick in range(10):
        k_local.tick_once()
        k_concurrent.tick_once()
        
        hash_l = CanonicalStateHasher.get_hash(k_local._state)
        hash_c = CanonicalStateHasher.get_hash(k_concurrent._state)
        
        assert hash_l == hash_c, f"Divergence at tick {tick}"

def test_zero_worker_fallback_equivalence(base_profile):
    """M8 Law: max_workers=0 behaves exactly like local execution."""
    profile_zero = base_profile.model_copy(update={"max_worker_count": 0})
    
    state1 = AuthoritativeState(tick=0, seed=42)
    rng1 = DeterministicRNG(42)
    k1 = Kernel(profile=profile_zero, state=state1, rng=rng1)
    
    state2 = AuthoritativeState(tick=0, seed=42)
    rng2 = DeterministicRNG(42)
    k2 = Kernel(profile=profile_zero, state=state2, rng=rng2)
    
    # Add an entity to both
    ent = V2EntityBuilder(1).location(0.0, 0.0).active(True).build()
    k1._state.entities[1] = ent
    k2._state.entities[1] = ent
    
    k1.tick_once()
    k2.tick_once()
    assert CanonicalStateHasher.get_hash(k1._state) == CanonicalStateHasher.get_hash(k2._state)
