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
        .at((1.0, 1.0))
        .with_interaction(target_id=500, progress=1.0)
        .with_inventory_component(InventoryComponent(max_slots=1, items=[ItemStack("stone", 1)]))
        .readiness(100.0)
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
        .at((1.0, 1.0))
        .with_interaction(target_id=500, progress=1.0)
        .with_inventory_component(InventoryComponent(max_weight=1.5, items=[ItemStack("wood", 1)])) # WOOD weight is 1.0
        .readiness(100.0)
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
        .at((1.0, 1.0))
        .with_interaction(target_id=500, progress=1.0)
        .readiness(100.0)
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
        .at((1.0, 1.0))
        .with_interaction(target_id=500, progress=1.0)
        .readiness(100.0)
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
