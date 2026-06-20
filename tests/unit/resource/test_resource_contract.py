import pytest
from typing import Dict, Any

from src.core.state import AuthoritativeState, ResourceNodeState, InteractionComponent, InventoryComponent, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder

def test_law_of_capacity_enforcement():
    """Law of Capacity: Progress reset if slots are full."""
    # Entity with full inventory
    actor = (V2EntityBuilder(1)
        .kind("hero")
        .location(1.0, 1.0)
        .interaction(target_node_id=500, progress=1.0)
        .replace_inventory(InventoryComponent(max_slots=1, items=[ItemStack("stone", 1)]))
        .combat(readiness=100.0)
        .build())
    
    node = ResourceNodeState(
        id=500, kind="WOOD", position=(1.0, 1.0), yields_item="wood",
        remaining_charges=5, max_charges=5, required_ticks=2
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, resource_nodes={500: node})
    
    # Propose finishing the harvest
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    assert e_upd.interaction.reset == True
    assert e_upd.inventory is None  # Should NOT have InventoryUpdate for success

def test_law_of_weight_enforcement():
    """Law of Weight: Progress reset if weight is exceeded."""
    # Entity with near-limit weight
    actor = (V2EntityBuilder(1)
        .kind("hero")
        .location(1.0, 1.0)
        .interaction(target_node_id=500, progress=1.0)
        .replace_inventory(InventoryComponent(max_weight=1.5, items=[ItemStack("wood", 1)])) # WOOD weight is 1.0
        .combat(readiness=100.0)
        .build())
        
    node = ResourceNodeState(
        id=500, kind="WOOD", position=(1.0, 1.0), yields_item="wood",
        remaining_charges=5, max_charges=5, required_ticks=2
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, resource_nodes={500: node})
    
    # Propose finishing the harvest
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    assert e_upd.interaction.reset == True
    assert e_upd.inventory is None

def test_law_of_proximity_reset_on_move():
    """Law of Proximity: Progress reset if entity moves."""
    actor = (V2EntityBuilder(1)
        .kind("hero")
        .location(1.0, 1.0)
        .interaction(target_node_id=500, progress=1.0)
        .combat(readiness=100.0)
        .build())
        
    node = ResourceNodeState(
        id=500, kind="WOOD", position=(1.0, 1.0), yields_item="wood",
        remaining_charges=5, max_charges=5, required_ticks=2
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, resource_nodes={500: node})
    
    # Propose movement while harvesting
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0), moved_this_tick=True)
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    assert e_upd.interaction.reset == True

def test_law_of_availability_node_depleted():
    """Law of Availability: Progress reset if node is depleted."""
    actor = (V2EntityBuilder(1)
        .kind("hero")
        .location(1.0, 1.0)
        .interaction(target_node_id=500, progress=1.0)
        .combat(readiness=100.0)
        .build())
        
    # Node with 0 charges
    node = ResourceNodeState(
        id=500, kind="WOOD", position=(1.0, 1.0), yields_item="wood",
        remaining_charges=0, max_charges=5, required_ticks=2
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, resource_nodes={500: node})
    
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    assert e_upd.interaction.reset == True


# ─── TCK-20260619-E21A-NODE-SCHEMA: Schema extension tests ───────────────────

def test_resource_node_regen_rate_field_exists():
    """AC1: ResourceNodeState accepts regen_rate_per_tick kwarg."""
    node = ResourceNodeState(
        id=1, kind="IRON", position=(0, 0), yields_item="iron_ore",
        remaining_charges=3, max_charges=5, required_ticks=10,
        regen_rate_per_tick=2,
    )
    assert node.regen_rate_per_tick == 2


def test_resource_node_regen_rate_in_canonical_dict():
    """AC2: to_canonical_dict() includes regen_rate_per_tick with correct value."""
    node = ResourceNodeState(
        id=1, kind="IRON", position=(0, 0), yields_item="iron_ore",
        remaining_charges=3, max_charges=5, required_ticks=10,
        regen_rate_per_tick=2,
    )
    d = node.to_canonical_dict()
    assert "regen_rate_per_tick" in d
    assert d["regen_rate_per_tick"] == 2


def test_resource_node_regen_rate_default_zero():
    """AC3: regen_rate_per_tick defaults to 0 — no behavior change for existing callers."""
    node = ResourceNodeState(
        id=2, kind="WOOD", position=(1, 1), yields_item="wood",
        remaining_charges=5, max_charges=5, required_ticks=5,
    )
    assert node.regen_rate_per_tick == 0
    d = node.to_canonical_dict()
    assert d["regen_rate_per_tick"] == 0


def test_world_event_category_resource_recovered():
    """AC4: WorldEventCategory.RESOURCE_RECOVERED is accessible and equals its string value."""
    from src.domains.world_emergence.schema import WorldEventCategory
    assert WorldEventCategory.RESOURCE_RECOVERED == "RESOURCE_RECOVERED"
