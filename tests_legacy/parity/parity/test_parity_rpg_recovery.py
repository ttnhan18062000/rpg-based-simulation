import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG

def create_test_profile():
    return RuntimeProfile(
        name="test_profile",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=100.0
    )

@pytest.mark.v2_contract
def test_rpg_combat_recovery_loop():
    """
    Verifies that the RPG interaction loop (Brain -> Proposal -> Refinement -> Apply)
    is functional in Phase 2.
    """
    hero = (V2EntityBuilder(1)
            .kind("HERO")
            .role(EntityRole.HERO)
            .faction(Faction.HERO_GUILD)
            .at((5, 5))
            .with_base_stats(hp=100, atk=20, def_stat=10)
            .build())
    
    goblin = (V2EntityBuilder(2)
              .kind("GOBLIN")
              .role(EntityRole.MONSTER)
              .faction(Faction.MONSTER_HORDE)
              .at((6, 5))
              .with_base_stats(hp=30, atk=5, def_stat=2)
              .build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    
    # Correct order: profile, state, rng
    kernel = Kernel(profile, state, rng)
    
    for _ in range(10): kernel.tick_once()
        
    kernel.tick_once() # Tick 11: The first exchange
    
    state_t11 = kernel.state
    h1 = state_t11.entities[1]
    g2 = state_t11.entities[2]
    
    # Readiness Law: 100 -> 0 (cost) -> 10 (passive gain in same tick)
    assert h1.readiness == 10.0
    assert g2.readiness == 10.0
    assert g2.combat.hp < 30
    assert h1.combat.hp < h1.combat.max_hp

@pytest.mark.v2_contract
def test_rpg_pursuit_recovery():
    """
    Verifies that entities move toward hostiles when out of range.
    """
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    goblin = (V2EntityBuilder(2).at((10, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    
    kernel = Kernel(profile, state, rng)
    
    for _ in range(10): kernel.tick_once()
    kernel.tick_once()
    
    h_t11 = kernel.state.entities[1]
    assert h_t11.position == (6.0, 5.0)
    assert h_t11.readiness == 10.0

@pytest.mark.v2_contract
def test_rpg_progression_recovery():
    """
    Verifies that killing an entity awards XP and triggers evolution.
    """
    hero = (V2EntityBuilder(1).kind("HERO").at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).with_base_stats(atk=100).build())
    goblin = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).with_base_stats(hp=5).build())
    
    hero = replace(hero, identity=replace(hero.identity, evolution_points=990))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    
    kernel = Kernel(profile, state, rng)
    
    for _ in range(10): kernel.tick_once()
    kernel.tick_once()
    
    state_final = kernel.state
    h_final = state_final.entities[1]
    g_final = state_final.entities[2]
    
    assert g_final.combat.alive == False
    assert h_final.identity.evolution_level == 2
    assert h_final.identity.evolution_points == 10
    assert h_final.kind == "LEGEND_HERO"
