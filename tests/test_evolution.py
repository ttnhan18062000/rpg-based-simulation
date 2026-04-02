from __future__ import annotations
import pytest
from src.config import SimulationConfig
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.gameplay.attributes import Attributes, AttributeCaps
from src.core.models.enums import AIState, ActionType, Domain, EnemyTier, RACE_PROFILES
from src.core.models.world_state import WorldState
from src.systems.rng import DeterministicRNG
from src.engine.world_loop import WorldLoop
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.world.generator import EntityGenerator
from src.core.world.grid import Grid
from src.systems.spatial_hash import SpatialHash
from src.core.gameplay.items.items import ItemTemplate, ItemType, ITEM_REGISTRY

# Register some dummy items for testing
ITEM_REGISTRY["lucky_charm"] = ItemTemplate(
    item_id="lucky_charm", name="Lucky Charm", 
    item_type=ItemType.ACCESSORY, rarity=0, luck_bonus=5
)
ITEM_REGISTRY["iron_sword"] = ItemTemplate(
    item_id="iron_sword", name="Iron Sword", 
    item_type=ItemType.WEAPON, rarity=0, atk_bonus=10
)
ITEM_REGISTRY["chainmail"] = ItemTemplate(
    item_id="chainmail", name="Chainmail", 
    item_type=ItemType.ARMOR, rarity=0, def_bonus=5
)

def test_entity_evolution_transformation():
    """Verify that a goblin evolves into a warrior/scout when hitting level cap."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    
    # Goblin tier BASIC, level 11 (next level is cap 12)
    actor = Entity(id=1, kind="goblin", pos=Vector2(10, 10))
    actor.tier = EnemyTier.BASIC
    actor.stats = Stats(level=11, hp=50, max_hp=50, xp=999, xp_to_next=100)
    actor.attributes = Attributes()
    actor.attribute_caps = AttributeCaps()
    
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.add_entity(actor)
    
    from unittest.mock import MagicMock
    worker_pool = MagicMock(spec=WorkerPool)
    conflict_resolver = MagicMock(spec=ConflictResolver)
    generator = MagicMock(spec=EntityGenerator)
    
    loop = WorldLoop(cfg, world, worker_pool, conflict_resolver, generator, rng=rng)
    
    # Level it up to 12
    loop._check_level_ups()
    
    # Should have triggered evolution
    # Goblin cap is 12. Level 11 -> 12 -> Evolve
    # Note: _check_level_ups loop runs while xp >= xp_to_next. 
    # 999 >= 100 -> level becomes 12. Then loop ends. Then evolution check happens.
    
    assert actor.stats.progression.level == 1
    assert actor.tier > EnemyTier.BASIC
    assert actor.kind != "goblin"
    assert "goblin" in actor.kind
    assert actor.stats.combat.max_hp > 50

def test_evolution_equipment_refresh():
    """Verify that evolution provides new equipment."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    
    from src.core.gameplay.items.items import Inventory
    actor = Entity(id=1, kind="goblin", pos=Vector2(10, 10))
    actor.tier = EnemyTier.BASIC
    actor.stats = Stats(level=12, hp=50, max_hp=50, xp=0, xp_to_next=1000)
    actor.inventory = Inventory()
    
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.add_entity(actor)
    
    from unittest.mock import MagicMock
    loop = WorldLoop(cfg, world, MagicMock(), MagicMock(), MagicMock(), rng=rng)
    
    # Manually trigger evolution
    profile = RACE_PROFILES["goblin"]
    loop._evolve_entity(actor, profile)
    
    # Goblin Warrior (Tier 2) often has chainmail or better weapon
    # Basic goblin had wooden_club.
    assert actor.tier == EnemyTier.WARRIOR or actor.tier == EnemyTier.SCOUT
    assert actor.inventory.get_all_item_ids(), f"Tier {actor.tier} should have gear"
