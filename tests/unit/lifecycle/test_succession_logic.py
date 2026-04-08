import pytest
from unittest.mock import MagicMock
from src.core.models.world_state import WorldState
from src.systems.lifecycle.hero_lifecycle_system import HeroLifecycleSystem
from src.core.entities.entity import Entity
from src.core.models.enums import Faction, ItemType, Rarity
from src.core.models.vectors import Vector2
from src.systems.infrastructure.base import SystemContext
from src.core.gameplay.items.item_registry import ItemTemplate, ITEM_REGISTRY

@pytest.fixture
def mock_world():
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    world = WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=10))
    return world

@pytest.fixture
def lifecycle_system():
    config = MagicMock()
    config.death_tier_max = 3
    config.hero_inventory_slots = 10
    config.hero_inventory_weight = 100
    config.hero_respawn_ticks = 10
    rng = MagicMock()
    rng.next_float.return_value = 0.5
    rng.next_int.return_value = 0
    return HeroLifecycleSystem(config, rng)

def test_permadeath_succession_and_heirlooms(mock_world, lifecycle_system):
    # 1. Setup a hero near permadeath
    hero = Entity(id=1, kind="hero")
    hero.identity.display_name = "Arthas"
    hero.identity.faction = Faction.HERO_GUILD
    hero.identity.death_count = 2 # Next death is permadeath (limit=3)
    hero.spatial.pos = Vector2(5, 5)
    hero.spatial.home_pos = Vector2(0, 0)
    hero.identity.household_id = "house_0_0"
    
    # Add heirlooms
    ITEM_REGISTRY["legendary_sword"] = ItemTemplate(
        item_id="legendary_sword", name="Legendary Sword", 
        rarity=Rarity.RARE, item_type=ItemType.WEAPON,
        atk_bonus=50, luck_bonus=10 # High stats to ensure auto-equip
    )
    ITEM_REGISTRY["common_trash"] = ItemTemplate(
        item_id="common_trash", name="Trash", 
        rarity=Rarity.COMMON, item_type=ItemType.MATERIAL
    )
    
    from src.core.aspects.inventory import InventoryAspect
    hero.inventory = InventoryAspect(max_slots=10, max_weight=100)
    hero.inventory.items = ["common_trash"]
    hero.inventory.add_item("legendary_sword")
    hero.inventory.equip("legendary_sword")
    
    mock_world.add_entity(hero)
    
    ctx = SystemContext(
        config=lifecycle_system.config,
        world=mock_world,
        rng=lifecycle_system.rng,
        generator=MagicMock(),
        faction_reg=MagicMock(),
        emit=MagicMock()
    )
    
    # 2. Trigger Death
    lifecycle_system.process_hero_death(ctx, hero, tick=100)
    
    # 3. Verify Succession Records
    assert "death_1_100" in mock_world.world_history.events
    assert 1 in mock_world.successor_registry
    successor_rec = mock_world.successor_registry[1]
    assert successor_rec.household_id == "house_0_0"
    assert successor_rec.motive_fragments["predecessor_name"] == "Arthas"
    
    # 4. Verify Heirlooms in Household
    assert "house_0_0" in mock_world.household_registry
    household = mock_world.household_registry["house_0_0"]
    assert "legendary_sword" in household.heirloom_ids
    assert "common_trash" not in household.heirloom_ids # Should have been dropped or stayed in inventory
    
    # 5. Verify Successor Arrival
    # Simulation logic for replacement
    mock_world._next_entity_id = 12 # 12 % 4 == 0 -> WARRIOR
    lifecycle_system._process_hero_replacements(ctx, tick=150) # Replacement at tick + config.respawn
    
    # Find the new hero
    new_hero = mock_world.get_entity(12)
    assert new_hero is not None
    assert new_hero.identity.household_id == "house_0_0"
    assert "Heir of Arthas" in new_hero.identity.titles
    assert new_hero.inventory.weapon == "legendary_sword"
    
    # Verify SuccessorRecord cleanup
    assert 1 not in mock_world.successor_registry
