from src.core.state import AuthoritativeState
from src.systems.generator import EntityGenerator
from src.world.spawn_config import DIFFICULTY_TIERS

# V2 Builder adds derived bonuses from default attributes (str=5, agi=5, vit=5, end=5)
# max_hp += vit*2 + end*0.5 = 10 + 2 = 12
# atk += str*0.5 = 2
# def += vit*0.3 = 1
ATTR_HP_BONUS = 12
ATTR_ATK_BONUS = 2
ATTR_DEF_BONUS = 1

def test_difficulty_tier_1_baseline():
    state = AuthoritativeState(tick=0, seed=42)
    gen = EntityGenerator(seed=42)
    hero = gen.spawn_hero((0, 0), state, difficulty_tier=1)
    
    # Tier 1 baseline: 100 HP, 15 ATK, 5 DEF, 50 Gold
    assert hero.combat.max_hp == 100 + ATTR_HP_BONUS
    assert hero.combat.atk == 15 + ATTR_ATK_BONUS
    assert hero.combat.def_stat == 5 + ATTR_DEF_BONUS
    assert hero.inventory.gold == 50
    assert 1 <= hero.identity.evolution_level <= 3

def test_difficulty_tier_4_scaling():
    state = AuthoritativeState(tick=0, seed=42)
    gen = EntityGenerator(seed=42)
    hero = gen.spawn_hero((0, 0), state, difficulty_tier=4)
    
    # Tier 4 multipliers: 4.0 HP, 3.0 ATK, 2.5 DEF, 4.0 Gold
    assert hero.combat.max_hp == 400 + ATTR_HP_BONUS
    assert hero.combat.atk == 45 + ATTR_ATK_BONUS
    assert hero.combat.def_stat == 12 + ATTR_DEF_BONUS # int(5 * 2.5) = 12
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
    assert goblin.combat.max_hp == int(30 * 2.5) + ATTR_HP_BONUS
    assert goblin.combat.atk == int(8 * 2.0) + ATTR_ATK_BONUS
    assert goblin.combat.def_stat == int(2 * 1.8) + ATTR_DEF_BONUS
    assert goblin.inventory.gold == int(5 * 2.5)
    assert 5 <= goblin.identity.evolution_level <= 10
