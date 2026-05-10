import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState, EntityState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.engine.checkpoint import CanonicalStateHasher

@pytest.mark.slow
def test_1000_tick_determinism():
    """
    Pillar 1: Long-Run Stability
    Verify that 1,000 ticks with a complex start state yields identical final hashes.
    """
    profile = RuntimeProfile(
        name="long-run-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1, # Single worker to prove logic first
        max_queue_depth=1000,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=100.0
    )
    
    from src.core.builder import V2EntityBuilder
    # Complex initial state
    entities = {}
    for i in range(1, 11):
        entities[i] = (V2EntityBuilder(i)
                       .kind("hero" if i <= 5 else "mob")
                       .location(float(i), float(i))
                       .combat(readiness=100.0)
                       .build())
    
    initial_state = AuthoritativeState(
        tick=0, 
        seed=12345, 
        world_time=0, 
        entities=entities
    )
    
    # Run 1
    rng1 = DeterministicRNG(12345)
    kernel1 = Kernel(profile, initial_state, rng1)
    for _ in range(1000):
        kernel1.tick_once()
    hash1 = CanonicalStateHasher.get_hash(kernel1.state)
    
    # Run 2
    rng2 = DeterministicRNG(12345)
    kernel2 = Kernel(profile, initial_state, rng2)
    for _ in range(1000):
        kernel2.tick_once()
    hash2 = CanonicalStateHasher.get_hash(kernel2.state)
    
    assert hash1 == hash2, "DIVERGENCE: Long-run hashes did not match!"
    print(f"Final Hash (1000 ticks): {hash1}")
