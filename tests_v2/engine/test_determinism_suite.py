from src_v2.engine.kernel import Kernel
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.platform.rng import DeterministicRNG
from src_v2.engine.checkpoint import CanonicalStateHasher


def test_reproducibility():
    """Seed 42, 10 ticks, must yield identical final hashes across 10 runs."""
    hashes = []
    
    for _ in range(10):
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
        # Initial state with some entities to increase complexity
        state = AuthoritativeState(tick=0, seed=42, world_time=0, entities={
            1: EntityState(id=1, kind="hero", position=(0,0)),
            2: EntityState(id=2, kind="mob", position=(5,5))
        })
        rng = DeterministicRNG(42)
        kernel = Kernel(profile, state, rng)
        
        # Run 10 ticks
        for _ in range(10):
            kernel.tick_once()
            
        hashes.append(CanonicalStateHasher.get_hash(kernel.state))
        
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
    state_a = AuthoritativeState(tick=1, seed=1, entities={
        1: EntityState(id=1, kind="a", position=(0,0)),
        2: EntityState(id=2, kind="b", position=(1,1))
    })
    
    # Manually swapped order in dictionary construction for state_b
    state_b = AuthoritativeState(tick=1, seed=1, entities={
        2: EntityState(id=2, kind="b", position=(1,1)),
        1: EntityState(id=1, kind="a", position=(0,0))
    })
    
    hash_a = CanonicalStateHasher.get_hash(state_a)
    hash_b = CanonicalStateHasher.get_hash(state_b)
    
    assert hash_a == hash_b
