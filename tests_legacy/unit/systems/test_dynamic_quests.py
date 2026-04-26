import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models import Vector2
from src_legacy.core.models.enums import Faction, Material
from src_legacy.core.world.regions import Region
from src_legacy.core.gameplay.quests import generate_quest, QuestType
from src_legacy.systems.world.strategy_system import StrategySystem
from src_legacy.systems.infrastructure.history_system import HistorySystem
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
    # Add a region
    world.regions.append(Region(region_id="forest_1", name="Dark Forest", 
                               center=Vector2(50, 50), radius=10, 
                               terrain=Material.FOREST, difficulty=2))
    
    from src_legacy.systems.infrastructure.event_system import EventBus
    world.event_bus = EventBus()
    
    return SystemContext(
        config=config,
        world=world,
        rng=rng,
        generator=None,
        faction_reg=None,
        emit=lambda *args, **kwargs: None
    )

def test_dynamic_liberate_quest(context):
    world = context.world
    region = world.regions[0]
    
    # 1. Conquer the region
    region.owner_faction = Faction.GOBLIN_HORDE
    world.region_control[region.region_id] = -60.0 # Conquered
    
    # 2. Generate quest
    quest = generate_quest(
        hero_level=10,
        existing_quest_ids=set(),
        rng=context.rng,
        world=world,
        force_template_id="liberate_region"
    )

    
    # 3. Verify it's a liberate quest
    assert quest is not None
    assert quest.quest_type == QuestType.LIBERATE
    assert "Dark Forest" in quest.title
    assert quest.target_pos == region.center

def test_history_logging(context):
    world = context.world
    history_system = HistorySystem(context.config, context.rng)
    strategy_system = StrategySystem(context.config, context.rng)
    
    # 1. Initial on_tick to subscribe
    history_system.on_tick(context, 0)

    assert len(world.event_bus._global_subscribers) > 0
    
    # 2. Simulate a war declaration
    # Set aggression high enough to trigger war (>= 80)
    target_faction = int(Faction.GOBLIN_HORDE)
    world.faction_aggression[target_faction] = 85.0
    world.war_status[target_faction] = False # Ensure it's not already at war
    

    strategy_system.on_tick(context, 100)
    
    # 3. Verify history entry

    assert len(world.history) > 0
    war_entry = next((e for e in world.history if e["type"] == "WarEvent"), None)
    assert war_entry is not None
    assert "DECLARED" in war_entry["desc"]
    assert "GOBLIN_HORDE" in war_entry["desc"] or "Faction 1" in war_entry["desc"]
