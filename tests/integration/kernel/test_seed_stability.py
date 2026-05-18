# Compliance IDs: INFRA-131
import pytest
from dataclasses import replace
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction

# LAW: INFRA-101 - Same seed and same inputs produce same final authoritative hash.
# LAW: INFRA-102 - Same seed and same inputs produce same replay-visible trajectory.

@pytest.fixture
def test_profile():
    return RuntimeProfile(
        name="STABILITY_TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=0, # Sequential for easiest verification
        max_queue_depth=1000,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0
    )

def make_test_state(seed: int):
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(10.0, 10.0)
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    monster = (
        V2EntityBuilder(2)
        .kind("monster")
        .location(11.0, 11.0)
        .identity(faction=Faction.MONSTER_HORDE)
        .combat(hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    return AuthoritativeState(
        tick=0, 
        seed=seed, 
        entities={1: hero, 2: monster}
    )

def test_simulation_seed_stability(test_profile):
    """
    Proves that two identical kernels with the same seed produce bit-identical
    fingerprints over multiple ticks.
    """
    initial_state = make_test_state(42)
    
    # Run A
    rng_a = DeterministicRNG(42)
    kernel_a = Kernel(test_profile, initial_state, rng_a)
    fingerprints_a = []
    for _ in range(5):
        kernel_a.tick_once()
        fingerprints_a.append(kernel_a.state.fingerprint()["state_hash"])
        
    # Run B
    rng_b = DeterministicRNG(42)
    kernel_b = Kernel(test_profile, initial_state, rng_b)
    fingerprints_b = []
    for _ in range(5):
        kernel_b.tick_once()
        fingerprints_b.append(kernel_b.state.fingerprint()["state_hash"])
        
    assert fingerprints_a == fingerprints_b, "Simulation diverged with identical seeds!"
    assert len(set(fingerprints_a)) == 5, "Simulation did not progress (hashes are identical across ticks)"

def test_simulation_seed_divergence(test_profile):
    """
    Proves that different seeds produce different trajectories (INFRA-103).
    """
    state_a = make_test_state(42)
    state_b = make_test_state(99)
    
    rng_a = DeterministicRNG(42)
    kernel_a = Kernel(test_profile, state_a, rng_a)
    
    rng_b = DeterministicRNG(99)
    kernel_b = Kernel(test_profile, state_b, rng_b)
    
    kernel_a.tick_once()
    kernel_b.tick_once()
    
    hash_a = kernel_a.state.fingerprint()["state_hash"]
    hash_b = kernel_b.state.fingerprint()["state_hash"]
    
    assert hash_a != hash_b, "Different seeds produced identical fingerprints!"

def test_simulation_domain_separation(test_profile):
    """
    Proves that adding an entity does not change the RNG sequence for 
    other entities in the same tick (INFRA-115).
    """
    # 1. Base run with one hero
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(10.0, 10.0)
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    # Give hero a reason to use RNG (e.g. WANDER)
    hero = replace(hero, navigation=replace(hero.navigation, movement_mode=7)) # WANDER
    
    state_a = AuthoritativeState(tick=0, seed=42, entities={1: hero})
    rng_a = DeterministicRNG(42)
    kernel_a = Kernel(test_profile, state_a, rng_a)
    kernel_a.tick_once()
    
    hero_a = kernel_a.state.entities[1]
    
    # 2. Run with same hero + unrelated monster far away
    monster = (
        V2EntityBuilder(2)
        .kind("monster")
        .location(100.0, 100.0) # Far away to avoid interaction
        .identity(faction=Faction.MONSTER_HORDE)
        .combat(hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    
    state_b = AuthoritativeState(tick=0, seed=42, entities={1: hero, 2: monster})
    rng_b = DeterministicRNG(42)
    kernel_b = Kernel(test_profile, state_b, rng_b)
    kernel_b.tick_once()
    
    hero_b = kernel_b.state.entities[1]
    
    # The hero's RNG sequence should be IDENTICAL because we use composite seeds (Domain, Tick, EntityID)
    assert hero_a.navigation.position == hero_b.navigation.position, "Hero movement changed by unrelated entity spawn!"
