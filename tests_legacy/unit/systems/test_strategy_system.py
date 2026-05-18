import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Vector2, Entity
from src_legacy.core.models.enums import Faction, Material, EnemyTier
from src_legacy.systems.world.strategy_system import StrategySystem
from src_legacy.systems.infrastructure.base import SystemContext
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig

@pytest.fixture
def context():
    config = SimulationConfig()
    rng = DeterministicRNG(0)
    class MockSpatialIndex:
        def insert(self, *args): pass
        def remove(self, *args): pass
        def move(self, *args): pass
    
    world = WorldState(seed=0, grid=None, spatial_index=MockSpatialIndex())
    
    # Mock some regions
    from src_legacy.core.world.regions import Region
    r1 = Region(region_id="r1", name="Forest", terrain=Material.FOREST, center=Vector2(10, 10), radius=50, difficulty=1)
    world.regions = [r1]
    
    return SystemContext(
        config=config,
        world=world,
        rng=rng,
        generator=None,
        faction_reg=None,
        emit=lambda *args, **kwargs: None
    )

def test_war_declaration(context):
    system = StrategySystem(context.config, context.rng)
    
    # Set high aggression
    context.world.faction_aggression[int(Faction.GOBLIN_HORDE)] = 85.0
    
    system.on_tick(context, 100)
    
    assert context.world.war_status[int(Faction.GOBLIN_HORDE)] is True

def test_territory_conquest(context):
    system = StrategySystem(context.config, context.rng)
    
    # Mock a faction registry that returns GOBLIN_HORDE for FOREST
    class MockReg:
        def tile_owner(self, tile):
            return Faction.GOBLIN_HORDE
    
    import dataclasses
    context = dataclasses.replace(context, faction_reg=MockReg())
    
    # Set low control (monsters winning)
    context.world.region_control["r1"] = -60.0
    
    system.on_tick(context, 100)
    
    region = context.world.regions[0]
    assert region.owner_faction == Faction.GOBLIN_HORDE
    
    # Verify stronghold spawn
    strongholds = [e for e in context.world.entities.values() if e.kind == "stronghold"]
    assert len(strongholds) == 1
    assert strongholds[0].spatial.pos == region.center

def test_territory_liberation(context):
    system = StrategySystem(context.config, context.rng)
    region = context.world.regions[0]
    region.owner_faction = Faction.GOBLIN_HORDE
    
    # Add a stronghold entity
    from src_legacy.core.entities.entity_builder import EntityBuilder
    builder = EntityBuilder(context.rng, 999, 0)
    stronghold = builder.kind("stronghold").at(region.center).faction(Faction.GOBLIN_HORDE).build()
    context.world.entities[999] = stronghold
    
    # Set high control (heroes winning)
    context.world.region_control["r1"] = 60.0
    
    system.on_tick(context, 100)
    
    assert region.owner_faction is None
    assert 999 not in context.world.entities
