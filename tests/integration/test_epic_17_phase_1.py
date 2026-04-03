import pytest
import logging
from src.core.models.world_state import WorldState
from src.engine.world_loop import WorldLoop
from src.config import SimulationConfig
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver
from src.systems.world.generator import EntityGenerator
from src.platform.rng import DeterministicRNG
from src.core.models.enums import Domain, AIState
from src.core.models import Vector2
from src.core.gameplay.faction import Faction
from src.core.entities.entity_builder import EntityBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def basic_setup():
    config = SimulationConfig(
        hero_count=3,
        death_tier_max=4,
        hero_respawn_ticks=10
    )
    
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    
    grid = Grid(config.grid_width, config.grid_height)
    spatial = SpatialHash(config.spatial_cell_size)
    world = WorldState(config.world_seed, grid, spatial)
    from src.ai.brain import AIBrain
    
    rng = DeterministicRNG(seed=42)
    brain = AIBrain(config, rng)
    pool = WorkerPool(config, brain, rng)
    resolver = ConflictResolver(config, rng)
    gen = EntityGenerator(config, rng)
    
    loop = WorldLoop(config, world, pool, resolver, gen, rng=rng)
    return loop, config, rng

def test_multi_hero_spawning(basic_setup):
    loop, config, rng = basic_setup
    world = loop.world
    
    # Simulate the spawning logic from __main__.py
    from src.core.gameplay.classes import HeroClass
    from src.core.data.hero_names import generate_hero_name
    
    town_center = Vector2(config.town_center_x, config.town_center_y)
    class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]
    
    for h_idx in range(config.hero_count):
        eid = world.allocate_entity_id()
        h_class = class_choices[h_idx % len(class_choices)]
        
        builder = EntityBuilder(rng, eid, tick=0).kind("hero").at(town_center).home(town_center)
        builder.with_traits(race_prefix="hero")
        name = generate_hero_name(rng, eid, 0, builder._traits)
        
        hero = builder.with_identity(display_name=name, generation=1).with_hero_class(h_class).build()
        world.add_entity(hero)
        
    heroes = [e for e in world.entities.values() if e.kind == "hero"]
    assert len(heroes) == 3
    names = [h.identity.display_name for h in heroes]
    assert len(set(names)) == 3 # Unique names
    for h in heroes:
        assert h.identity.generation == 1
        assert h.identity.death_count == 0

def test_death_escalation_and_replacement(basic_setup):
    loop, config, rng = basic_setup
    world = loop.world
    
    # Add a hero
    eid = world.allocate_entity_id()
    home = Vector2(config.town_center_x, config.town_center_y)
    hero = (
        EntityBuilder(rng, eid, tick=0)
        .kind("hero")
        .at(Vector2(5, 5))
        .home(home)
        .with_identity(display_name="TestHero", generation=1)
        .with_inventory(weapon="iron_sword", armor="leather_vest", accessory="luck_charm")
        .with_starting_items(["potion"])
        .build()
    )
    world.add_entity(hero)
    
    # 1st death: should drop bag items, keep equipment
    hero.combat.hp = 0
    loop._phase_cleanup()
    
    assert hero.combat.alive == True # Respawned
    assert hero.identity.death_count == 1
    assert hero.spatial.pos == home
    assert "potion" not in hero.inventory.items
    assert hero.inventory.weapon == "iron_sword"
    assert hero.inventory.armor == "leather_vest"
    assert hero.inventory.accessory == "luck_charm"
    
    # 2nd death: should drop accessory
    hero.combat.hp = 0
    hero.spatial.pos = Vector2(10, 10)
    loop._phase_cleanup()
    
    assert hero.identity.death_count == 2
    assert hero.inventory.accessory is None
    assert hero.inventory.armor == "leather_vest"
    
    # 3rd death: should drop armor
    hero.combat.hp = 0
    loop._phase_cleanup()
    
    assert hero.identity.death_count == 3
    assert hero.inventory.armor is None
    assert hero.inventory.weapon == "iron_sword"
    
    # 4th death: Permadeath!
    hero.combat.hp = 0
    loop._phase_cleanup()
    
    assert eid not in world.entities
    assert len(loop._hero_lifecycle._pending_hero_replacements) == 1
    assert loop._hero_lifecycle._pending_hero_replacements[0]["generation"] == 2
    
    # Progress time to replacement
    world.tick = 60
    from src.systems.infrastructure.base import SystemContext
    ctx = SystemContext(config, world, rng, loop._generator, loop._faction_reg, loop._emit)
    loop._hero_lifecycle._process_hero_replacements(ctx, 60)
    
    new_heroes = [e for e in world.entities.values() if e.kind == "hero"]
    assert len(new_heroes) == 1
    new_hero = new_heroes[0]
    assert new_hero.id != eid
    assert new_hero.identity.generation == 2
    assert new_hero.identity.display_name != "TestHero"

def test_hero_familiarity(basic_setup):
    loop, config, rng = basic_setup
    world = loop.world
    
    h1 = EntityBuilder(rng, 101, tick=0).kind("hero").at(Vector2(5, 5)).with_identity(display_name="H1").build()
    h2 = EntityBuilder(rng, 102, tick=0).kind("hero").at(Vector2(6, 6)).with_identity(display_name="H2").build()
    h3 = EntityBuilder(rng, 103, tick=0).kind("hero").at(Vector2(20, 20)).with_identity(display_name="H3").build()
    
    world.add_entity(h1)
    world.add_entity(h2)
    world.add_entity(h3)
    
    # H1 and H2 are near, H3 is far
    from src.systems.infrastructure.base import SystemContext
    ctx = SystemContext(config, world, rng, loop._generator, loop._faction_reg, loop._emit)
    loop._hero_lifecycle._tick_proximity_familiarity(ctx, 0)
    
    assert h1.identity.hero_familiarity[h2.id] == pytest.approx(0.002, abs=0.001)
    assert h2.identity.hero_familiarity[h1.id] == pytest.approx(0.002, abs=0.001)
    assert h1.identity.hero_familiarity.get(h3.id, 0) == 0
    
    # Simulate many ticks
    for i in range(250):
        loop._hero_lifecycle._tick_proximity_familiarity(ctx, i)
        
    assert h1.identity.hero_familiarity[h2.id] > 0.5
    # Should have emitted alliance event (we can check logs or just assume it reached the threshold)

    h1.spatial.pos = Vector2(0, 0)
    loop._hero_lifecycle._tick_proximity_familiarity(ctx, 251)
    assert h1.identity.hero_familiarity[h2.id] < 0.53 # Decayed from > 0.5 + small change
