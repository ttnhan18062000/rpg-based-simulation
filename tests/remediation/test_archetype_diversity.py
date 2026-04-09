
import pytest
from src.systems.world.generator import EntityGenerator
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.models.world_state import WorldState
from src.platform.spatial_hash import SpatialHash
from src.core.world.grid import Grid
from src.core.models.enums import Archetype, Faction
from src.core.models.vectors import Vector2

def test_archetype_diversity():
    rng = DeterministicRNG(123)
    config = SimulationConfig()
    world = WorldState(seed=123, grid=Grid(100, 100), spatial_index=SpatialHash(10))
    # Corrected constructor order: EntityGenerator(config, rng)
    gen = EntityGenerator(config, rng)
    
    # Spawn 100 entities
    archetypes = []
    for i in range(100):
        eid = world.allocate_entity_id()
        # Use a real faction from enums
        entity = gen.spawn_race(world, "goblin", tier=0, near_pos=Vector2(10, 10))
        archetypes.append(entity.identity.archetype)
    
    # Verify diversity
    archetype_counts = {}
    for arch in archetypes:
        archetype_counts[arch] = archetype_counts.get(arch, 0) + 1
    
    print(f"Archetype counts: {archetype_counts}")
    
    # We expect more than just BALANCED
    assert len(archetype_counts) > 1
    assert Archetype.BALANCED in archetype_counts
    assert any(arch != Archetype.BALANCED for arch in archetype_counts.keys())

def test_hero_archetype_diversity():
    from src.core.world.world_generator import WorldGenerator
    rng = DeterministicRNG(456)
    config = SimulationConfig()
    
    world = WorldState(seed=456, grid=Grid(100, 100), spatial_index=SpatialHash(10))
    world_gen = WorldGenerator(rng, config)
    
    # Mock town center
    from src.core.gameplay.buildings import Building
    town_center = Building(building_id="town_center", name="Town Center", pos=Vector2(50, 50), building_type="town_center")
    world.buildings.append(town_center)
    
    # Initialize EntityGenerator correctly
    gen = EntityGenerator(config, rng)
    
    # Run hero spawn logic
    world_gen._spawn_initial_entities(world, gen, config, rng, town_center.pos)
    
    heroes = [e for e in world.entities.values() if e.kind == "hero"]
    hero_archs = [e.identity.archetype for e in heroes]
    
    print(f"Hero archetypes: {hero_archs}")
    if len(heroes) >= 4:
        # Check for at least 4 different archetypes in first 4 heroes (due to cycling)
        unique_archs = set(hero_archs[:4])
        assert len(unique_archs) >= 4 # BALANCED, GLORY_SEEKER, HONORABLE_DEFENDER, CAUTIOUS_OPPORTUNIST
