import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))



import pytest
from src.config import SimulationConfig
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.enums import ActionType
from src.actions.base import ActionProposal
from src.engine.conflict_resolver import ConflictResolver
from src.systems.gameplay.action_system import ActionSystem
from src.systems.infrastructure.base import SystemContext
from src.platform.rng import DeterministicRNG

def test_loot_recovery_consistency():
    """Verify that a LOOT action produces the same world state in live vs. manual replay."""
    config = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(42)
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # 1. Setup Entity and Ground Item
    from src.core.aspects.inventory import InventoryAspect
    from src.core.gameplay.attributes import Attributes, AttributeCaps
    from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate
    from src.core.models.enums import ItemType, Rarity
    
    ITEM_REGISTRY["potion_health"] = ItemTemplate(
        item_id="potion_health", name="Health Potion", 
        item_type=ItemType.CONSUMABLE, rarity=Rarity.COMMON, heal_amount=20, weight=0.1
    )
    
    entity = Entity(id=1, kind="hero")
    entity.inventory = InventoryAspect()
    entity.progression.attributes = Attributes() 
    entity.progression.attribute_caps = AttributeCaps()
    entity.spatial.pos = Vector2(5, 5)
    world.add_entity(entity)
    
    item_id = "potion_health"
    world.drop_items(Vector2(5, 5), [item_id])
    
    # 2. Create LOOT Proposal
    proposal = ActionProposal(actor_id=1, verb=ActionType.LOOT, target=Vector2(5, 5))
    
    # --- LIVE SIMULATION PATH ---
    resolver = ConflictResolver(config, rng)
    action_system = ActionSystem(config, rng)
    
    # Mock emit
    emitted = []
    def mock_emit(*args, **kwargs): emitted.append(args)
    
    context = SystemContext(config, world, rng, None, None, mock_emit)
    
    # Resolve
    applied = resolver.resolve([proposal], world)
    assert len(applied) == 1
    
    # Apply via ActionSystem (Live Path)
    action_system.process_applied_actions(context, applied)
    
    # Verify Live Result: Entity should have the item, ground should be empty
    assert item_id in entity.inventory.items
    assert not world.ground_items.get((5, 5))
    
    # --- RECOVERY PATH (The manual way EngineManager does it currently) ---
    # Reset world
    grid_rec = Grid(10, 10)
    spatial_rec = SpatialHash(cell_size=2)
    world_recovery = WorldState(seed=42, grid=grid_rec, spatial_index=spatial_rec)
    entity_rec = Entity(id=1, kind="hero")
    entity_rec.inventory = InventoryAspect()
    entity_rec.progression.attributes = Attributes()
    entity_rec.progression.attribute_caps = AttributeCaps()
    entity_rec.spatial.pos = Vector2(5, 5)
    world_recovery.add_entity(entity_rec)
    world_recovery.drop_items(Vector2(5, 5), [item_id])
    
    # Replay using resolver + NEW unified application logic
    resolver_rec = ConflictResolver(config, rng)
    applied_rec = resolver_rec.resolve([proposal], world_recovery)
    
    ActionSystem.apply_action_state_transitions(
        world_recovery, 
        config, 
        applied_rec,
        rng=rng
    )
    
    # ASSERTION: In recovery, the item should now be looted!
    assert item_id in entity_rec.inventory.items, "Item was NOT looted during recovery even with new logic!"
    assert not world_recovery.ground_items.get((5, 5)), "Ground item was not removed during recovery!"

