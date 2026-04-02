import pytest
from unittest.mock import MagicMock
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.engine.world_loop import WorldLoop
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver
from src.systems.world.generator import EntityGenerator
from src.config import SimulationConfig
from src.core.entities.entity import Entity, Vector2
from src.core.gameplay.buildings import Building
from src.core.models.enums import ActionType, AIState, EntityRole, HeroClass
from src.actions.base import ActionProposal
from src.platform.rng import DeterministicRNG
from src.core.world.monuments import Monument

from src.ai.brain import AIBrain

@pytest.fixture
def basic_setup():
    config = SimulationConfig()
    grid = Grid(20, 20)
    spatial = SpatialHash(5)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    rng = DeterministicRNG(42)
    
    # Add some buildings
    b1 = Building(building_id="inn_1", name="Inn", pos=Vector2(5, 5), building_type="inn", durability=100.0, max_durability=100.0)
    b2 = Building(building_id="shop_1", name="Shop", pos=Vector2(6, 6), building_type="store", durability=100.0, max_durability=100.0)
    world.buildings = [b1, b2]
    
    brain = AIBrain(config, rng)
    worker_pool = WorkerPool(config, brain, rng)
    conflict_resolver = ConflictResolver(config, rng)
    generator = EntityGenerator(config, rng)
    
    loop = WorldLoop(config, world, worker_pool, conflict_resolver, generator, rng=rng)
    return loop, world, config

def test_building_durability_and_damage(basic_setup):
    loop, world, config = basic_setup
    b = world.buildings[0]
    
    assert b.durability == 100.0
    assert b.is_functional is True
    
    b.take_damage(30.0)
    assert b.durability == 70.0
    
    b.take_damage(80.0)
    assert b.durability == 0.0
    assert b.is_functional is False
    
    b.repair(50.0)
    assert b.durability == 50.0
    assert b.is_functional is True

def test_repair_action(basic_setup):
    loop, world, config = basic_setup
    from src.actions.repair import RepairAction
    
    hero = Entity(1, kind="hero", pos=Vector2(5, 6))
    hero.stats.progression.progression.gold = 20.0
    world.add_entity(hero)
    
    b = world.buildings[0] # at (5,5)
    b.durability = 50.0
    
    proposal = ActionProposal(actor_id=1, verb=ActionType.REPAIR, target="inn_1")
    
    assert RepairAction.validate(proposal, world) is True
    RepairAction.apply(proposal, world)
    
    assert b.durability == 100.0
    assert hero.stats.progression.progression.gold == 10.0

def test_monument_spawning_on_permadeath(basic_setup):
    loop, world, config = basic_setup
    # Mock a hero dying permanently
    hero = Entity(1, kind="hero", pos=Vector2(5, 5))
    hero.identity.display_name = "Legend"
    hero.stats.progression.progression.level = 20
    hero.progression.hero_class = HeroClass.WARRIOR
    hero.identity.death_count = config.death_tier_max - 1
    hero.spatial.home_pos = Vector2(0, 0)
    world.add_entity(hero)
    
    hero.stats.combat.combat.hp = 0 # Die
    loop._phase_cleanup()
    
    assert len(world.monuments) == 1
    assert world.monuments[0].hero_name == "Legend"
    assert world.monuments[0].buff_type == "hp"

def test_monument_buff_application(basic_setup):
    loop, world, config = basic_setup
    m = Monument(monument_id="m1", hero_name="Old", hero_class="WARRIOR", level=20, 
                 pos=Vector2(0,0), buff_type="atk", buff_value=0.1)
    world.monuments.append(m)
    
    # Spawn new hero
    new_hero = Entity(2, kind="hero", pos=Vector2(0,0))
    new_hero.stats.combat.combat.atk_base = 10
    
    loop._apply_monument_buffs(new_hero)
    assert new_hero.stats.combat.combat.atk_base == 11 # 10 * 1.1

def test_victory_condition(basic_setup):
    loop, world, config = basic_setup
    world.world_age = 50001
    for b in world.buildings:
        b.durability = 90.0
        b.is_functional = True
    
    # Should return False (Stop simulation) on Victory
    assert loop._check_endgame_conditions() is False

def test_defeat_condition(basic_setup):
    loop, world, config = basic_setup
    loop, world, config = basic_setup
    world.world_age = 50001
    world.buildings[0].is_functional = False
    world.buildings[1].is_functional = False
    
    # Add a 3rd building and destroy it
    b3 = Building(building_id="b3", name="B3", pos=Vector2(0,0), building_type="store", durability=0.0, max_durability=100.0)
    b3.is_functional = False
    world.buildings.append(b3)
    
    assert loop._check_endgame_conditions() is False
