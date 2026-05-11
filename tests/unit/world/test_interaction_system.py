"""
Interaction system and harvesting tests.
- RPG-0027: harvesting_channeling_success
- RPG-0028: interaction_interrupted_by_movement
- RPG-0029: interaction_inventory_pressure
- RPG-0030: interaction_resource_exhaustion
- RPG-0032: interaction_range_enforcement
- RPG-1678: interaction_determinism_contract
"""
import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityState, InteractionComponent, InventoryComponent, ResourceNodeState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate, NavigationUpdate
from src.engine.interaction import InteractionSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_interaction_channeling_success():
    # Setup state: Entity at progress 2/3 for node 1
    node = ResourceNodeState(id=1, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=3)
    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .interaction(target_node_id=1, progress=2)
        .build()
    )
    state = AuthoritativeState(tick=10, seed=42, 
                               entities={10: entity}, 
                               resource_nodes={1: node})
    
    # Proposal: Advance progress by 1
    update = StateUpdate(entity_updates={
        10: EntityUpdate(entity_id=10, interaction=InteractionUpdate(target_node_id=1, progress_delta=1))
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Verify: Successful harvest
    ent_upd = refined.entity_updates[10]
    assert ent_upd.interaction.reset == True
    assert any(stack.item_id == "herb" for stack in ent_upd.inventory.items_add)
    
    node_upd = refined.node_updates[1]
    assert node_upd.charges_delta == -1

def test_interaction_interrupted_by_movement():
    # Setup state: Progress 1/3
    node = ResourceNodeState(id=1, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=3)
    entity = (
        V2EntityBuilder(10)
        .kind("hero")
        .location(0.0, 0.0)
        .interaction(target_node_id=1, progress=1)
        .combat(readiness=100.0)
        .build()
    )
    state = AuthoritativeState(tick=10, seed=42, 
                               entities={10: entity}, 
                               resource_nodes={1: node})
    
    # Proposal: Move and try to advance progress
    update = StateUpdate(entity_updates={
        10: EntityUpdate(entity_id=10, 
                         navigation=NavigationUpdate(target_set=(1.0, 1.0)),
                         interaction=InteractionUpdate(target_node_id=1, progress_delta=1))
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Verify: Progress reset due to movement
    ent_upd = refined.entity_updates[10]
    assert ent_upd.interaction.reset == True
    assert ent_upd.inventory is None  # No item awarded

def test_interaction_inventory_pressure():
    # Setup state: Entity inventory full
    node = ResourceNodeState(id=1, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=1)
    entity = (
        V2EntityBuilder(10)
        .kind("hero")
        .location(0.0, 0.0)
        .inventory(max_slots=1, items=[ItemStack("iron_ore", 1)])
        .build()
    )
    state = AuthoritativeState(tick=10, seed=42, 
                               entities={10: entity}, 
                               resource_nodes={1: node})
    
    # Proposal: Finish harvest
    update = StateUpdate(entity_updates={
        10: EntityUpdate(entity_id=10, interaction=InteractionUpdate(target_node_id=1, progress_delta=1))
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Verify: Reset but no item (inventory pressure)
    ent_upd = refined.entity_updates[10]
    assert ent_upd.interaction.reset == True
    assert ent_upd.inventory is None
