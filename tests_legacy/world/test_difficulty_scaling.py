from src_legacy.core.state import AuthoritativeState
from src_legacy.systems.generator import EntityGenerator
from src_legacy.world.spawn_config import DIFFICULTY_TIERS

def test_difficulty_tier_1_baseline():
    state = AuthoritativeState(tick=0, seed=42)
    gen = EntityGenerator(seed=42)
    hero = gen.spawn_hero((0, 0), state, difficulty_tier=1)
    
    # Tier 1 baseline: 100 HP, 15 ATK, 5 DEF, 50 Gold
    assert hero.combat.max_hp == 100
    assert hero.combat.atk == 15
    assert hero.combat.def_stat == 5
    assert hero.inventory.gold == 50
    assert 1 <= hero.identity.evolution_level <= 3

def test_difficulty_tier_4_scaling():
    state = AuthoritativeState(tick=0, seed=42)
    gen = EntityGenerator(seed=42)
    hero = gen.spawn_hero((0, 0), state, difficulty_tier=4)
    
    # Tier 4 multipliers: 4.0 HP, 3.0 ATK, 2.5 DEF, 4.0 Gold
    assert hero.combat.max_hp == 400
    assert hero.combat.atk == 45
    assert hero.combat.def_stat == 12 # int(5 * 2.5) = 12
    assert hero.inventory.gold == 200
    assert 8 <= hero.identity.evolution_level <= 15

def test_difficulty_tier_determines_level_range():
    state = AuthoritativeState(tick=0, seed=42)
    gen = EntityGenerator(seed=42)
    
    # Tier 2: Level 3-6
    hero2 = gen.spawn_hero((0, 0), state, difficulty_tier=2)
    assert 3 <= hero2.identity.evolution_level <= 6
    
    # Tier 3: Level 5-10
    hero3 = gen.spawn_hero((0, 0), state, difficulty_tier=3)
    assert 5 <= hero3.identity.evolution_level <= 10

def test_goblin_difficulty_scaling():
    state = AuthoritativeState(tick=0, seed=42)
    gen = EntityGenerator(seed=42)
    goblin = gen.spawn_goblin((0, 0), state, difficulty_tier=3)
    
    # Tier 3 multipliers: 2.5 HP, 2.0 ATK, 1.8 DEF, 2.5 Gold
    # Goblin base: 30 HP, 8 ATK, 2 DEF, 5 Gold
    assert goblin.combat.max_hp == int(30 * 2.5)
    assert goblin.combat.atk == int(8 * 2.0)
    assert goblin.combat.def_stat == int(2 * 1.8)
    assert goblin.inventory.gold == int(5 * 2.5)
    assert 5 <= goblin.identity.evolution_level <= 10
