import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.logic.combat_interaction_service import CombatInteractionService
from src.core.gameplay.faction import FactionRegistry
from src.config import SimulationConfig

@pytest.fixture
def world():
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    config = SimulationConfig()
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    w = WorldState(seed=42, grid=grid, spatial_index=spatial)
    from src.core.entities.entity_builder import EntityBuilder
    from src.platform.rng import DeterministicRNG
    from src.core.gameplay.faction import Faction
    rng = DeterministicRNG(42)
    
    # Add a hero and a monster
    hero = EntityBuilder(rng, 1).kind("hero").faction(Faction.HERO_GUILD).at(Vector2(10, 10)).build()
    monster = EntityBuilder(rng, 2).kind("monster").faction(Faction.GOBLIN_HORDE).at(Vector2(11, 10)).build()
    w.add_entity(hero)
    w.add_entity(monster)
    return w

def test_engagement_detection(world):
    hero = world.entities[1]
    monster = world.entities[2]
    
    # Orthogonally adjacent = engaged
    assert CombatInteractionService.is_engaged(hero, world) is True
    assert CombatInteractionService.is_engaged(monster, world) is True

def test_engagement_clears_on_separation(world):
    hero = world.entities[1]
    monster = world.entities[2]
    
    # Move monster away
    world.move_entity(monster.id, Vector2(12, 10))
    
    assert CombatInteractionService.is_engaged(hero, world) is False
    assert CombatInteractionService.is_engaged(monster, world) is False

def test_engagement_respects_hostility(world):
    from src.core.entities.entity_builder import EntityBuilder
    from src.platform.rng import DeterministicRNG
    from src.core.gameplay.faction import Faction
    rng = DeterministicRNG(42)
    hero1 = world.entities[1]
    # Add an ally
    hero2 = EntityBuilder(rng, 3).kind("hero").faction(Faction.HERO_GUILD).at(Vector2(10, 11)).build()
    world.add_entity(hero2)
    
    # Case 1: Hero1 is engaged with monster
    assert CombatInteractionService.is_engaged(hero1, world) is True
    
    # Case 2: Remove monster, now only hero2 is adjacent
    world.remove_entity(2)
    assert CombatInteractionService.is_engaged(hero1, world) is False # Hero2 is ally
