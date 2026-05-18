import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from src_legacy.core.models import Vector2
from unittest.mock import MagicMock
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.world.regions import Region
from src_legacy.core.gameplay.faction import Faction
from src_legacy.systems.world.strategy_system import StrategySystem
from src_legacy.systems.infrastructure.base import SystemContext
from src_legacy.config import SimulationConfig
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash

@pytest.fixture
def mock_world():
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # Setup test regions
    r1 = Region(region_id="r1", name="Goblin Camp", terrain=4, center=Vector2(2, 2), radius=5, difficulty=1)
    r2 = Region(region_id="r2", name="Swamp", terrain=8, center=Vector2(7, 7), radius=5, difficulty=2)
    world.regions = [r1, r2]
    
    return world


@pytest.fixture
def mock_context(mock_world):
    from src_legacy.core.gameplay.faction import FactionRegistry
    config = SimulationConfig()
    rng = DeterministicRNG(0)
    generator = MagicMock()
    identity_mock = FactionRegistry.default()
    emit = MagicMock()
    return SystemContext(config, mock_world, rng, generator, identity_mock, emit)


def test_influence_shifts_on_monster_death(mock_context):
    system = StrategySystem(mock_context.config, mock_context.rng)
    world = mock_context.world
    
    # Initial control is 0.0
    world.region_control["r1"] = 0.0
    
    # Record a monster death in r1 (Faction 1 = GOBLIN_HORDE)
    world.faction_deaths_per_region[(int(Faction.GOBLIN_HORDE), "r1")] = 1
    
    system.on_tick(mock_context, 10) # Process every 10 ticks
    
    # Influence should shift towards heroes (positive)
    assert world.region_control["r1"] > 0.0
    # Deaths should be cleared after processing (set to 0)
    assert world.faction_deaths_per_region.get((int(Faction.GOBLIN_HORDE), "r1"), 0) == 0


def test_influence_shifts_on_hero_death(mock_context):
    system = StrategySystem(mock_context.config, mock_context.rng)
    world = mock_context.world
    
    # Initial control is 0.0
    world.region_control["r1"] = 0.0
    
    # Record a hero death in r1 (Faction 0 = HERO_GUILD)
    world.faction_deaths_per_region[(int(Faction.HERO_GUILD), "r1")] = 1
    
    system.on_tick(mock_context, 10)
    
    # Influence should shift towards monsters (negative)
    assert world.region_control["r1"] < 0.0


def test_war_state_transition(mock_context):
    system = StrategySystem(mock_context.config, mock_context.rng)
    world = mock_context.world
    
    # Initial status is peace
    world.war_status[int(Faction.GOBLIN_HORDE)] = False
    world.faction_aggression[int(Faction.GOBLIN_HORDE)] = 50.0
    
    system.on_tick(mock_context, 10)
    assert world.war_status[int(Faction.GOBLIN_HORDE)] is False
    
    # Increase aggression to 90.0
    world.faction_aggression[int(Faction.GOBLIN_HORDE)] = 90.0
    system.on_tick(mock_context, 10)
    
    # Should enter war state
    assert world.war_status[int(Faction.GOBLIN_HORDE)] is True


def test_conquered_region_triggers_stronghold(mock_context):
    system = StrategySystem(mock_context.config, mock_context.rng)
    world = mock_context.world
    
    # Drop influence to -90.0
    world.region_control["r1"] = -90.0
    
    system.on_tick(mock_context, 10)
    
    # Region r1 should be in the set of conquered regions (conceptually)
    assert system.is_conquered(mock_context, "r1") is True
    assert system.is_conquered(mock_context, "r2") is False
    
    # Verify stronghold was spawned
    assert any(e.kind == "stronghold" for e in world.entities.values())


def test_stronghold_debuff_application(mock_context):
    from tests_legacy.helpers.legacy_stats import Stats
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.enums import Faction as FactionEnum
    from src_legacy.core.models.enums import EntityRole
    system = StrategySystem(mock_context.config, mock_context.rng)
    world = mock_context.world
    
    # Create a hero in r1 center
    hero = (
        EntityBuilder(mock_context.rng, 99).kind("hero")
        .at(Vector2(2, 2))
        .faction(FactionEnum.HERO_GUILD)
        .build()
    )
    world.add_entity(hero)
    
    # Region r1 is NOT conquered
    world.region_control["r1"] = 0.0
    system.on_tick(mock_context, 10)
    from src_legacy.core.gameplay.effects import EffectType
    assert not any(e.effect_type == EffectType.CONQUERED_DEBUFF for e in hero.combat.effects)
    
    # Region r1 IS conquered
    world.region_control["r1"] = -90.0
    # Stronghold exists in r1
    stronghold = (
        EntityBuilder(mock_context.rng, 100).kind("stronghold")
        .at(Vector2(3, 3))
        .faction(FactionEnum.GOBLIN_HORDE)
        .role(EntityRole.STRONGHOLD)
        .build()
    )
    world.add_entity(stronghold)
    
    system.on_tick(mock_context, 10)
    
    # Hero should receive a debuff
    assert any(e.effect_type == EffectType.CONQUERED_DEBUFF for e in hero.combat.effects)
