from __future__ import annotations
import pytest
from src.config import SimulationConfig
from src.core.entities.entity import Entity
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.vectors import Vector2
from src.core.gameplay.attributes import Attributes, AttributeCaps
from src.core.models.enums import AIState, ActionType, Domain, EnemyTier, RACE_PROFILES
from src.core.models.world_state import WorldState
from src.platform.rng import DeterministicRNG
from src.engine.world_loop import WorldLoop
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.world.generator import EntityGenerator
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.gameplay.items.items import ItemTemplate, ItemType

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

from src.systems.lifecycle.progression_system import ProgressionSystem
from src.systems.infrastructure.base import SystemContext

def test_entity_evolution_transformation():
    """Verify that a goblin evolves into a warrior/scout when hitting level cap."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    
    # Goblin tier BASIC, level 11 (next level is cap 12)
    actor = (
        EntityBuilder(rng, 1).kind("goblin")
        .at(Vector2(10, 10))
        .with_inventory()
        .build()
    )
    actor.identity.tier = EnemyTier.BASIC
    actor.progression.level = 11
    actor.progression.xp = 999
    actor.progression.xp_to_next = 100
    
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.add_entity(actor)
    
    from unittest.mock import MagicMock
    generator = MagicMock(spec=EntityGenerator)
    
    system = ProgressionSystem(cfg, rng)
    context = SystemContext(
        config=cfg,
        world=world,
        rng=rng,
        generator=generator,
        identity=None,
        emit=MagicMock()
    )
    
    # Level it up to 12 and trigger evolution
    system._check_level_ups(context)
    
    assert actor.progression.level == 1
    assert actor.identity.tier > EnemyTier.BASIC
    assert actor.kind != "goblin"
    assert "goblin" in actor.kind
    assert actor.combat.max_hp > 50

def test_evolution_equipment_refresh():
    """Verify that evolution provides new equipment."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    
    from src.core.aspects.inventory import InventoryAspect
    actor = (
        EntityBuilder(rng, 1).kind("goblin")
        .at(Vector2(10, 10))
        .with_inventory()
        .build()
    )
    actor.identity.tier = EnemyTier.BASIC
    actor.progression.level = 12
    actor.progression.xp = 0
    actor.progression.xp_to_next = 1000
    
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.add_entity(actor)
    
    from unittest.mock import MagicMock
    generator = MagicMock(spec=EntityGenerator)
    
    system = ProgressionSystem(cfg, rng)
    context = SystemContext(
        config=cfg,
        world=world,
        rng=rng,
        generator=generator,
        identity=None,
        emit=MagicMock()
    )
    
    # Manually trigger evolution
    profile = RACE_PROFILES["goblin"]
    system._evolve_entity(context, actor, profile)
    
    # Verification
    assert actor.identity.tier in (EnemyTier.WARRIOR, EnemyTier.SCOUT)
    assert generator.equip_entity.called
