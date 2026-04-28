import pytest
from src.core.state import AuthoritativeState, EntityState, InteractionComponent, InventoryComponent, ResourceNodeState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate
from src.engine.interaction import InteractionSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_interaction_channeling_success():
    # Setup state: Entity at progress 2/3 for node 1
    node = ResourceNodeState(id=1, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=3)
    entity = EntityState(id=10, kind="hero", position=(0,0), 
                         interaction=InteractionComponent(target_node_id=1, progress=2))
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
    entity = EntityState(id=10, kind="hero", position=(0,0), 
                         interaction=InteractionComponent(target_node_id=1, progress=1))
    state = AuthoritativeState(tick=10, seed=42, 
                               entities={10: entity}, 
                               resource_nodes={1: node})
    
    # Proposal: Move and try to advance progress
    update = StateUpdate(entity_updates={
        10: EntityUpdate(entity_id=10, new_position=(1,1), moved_this_tick=True, 
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
    entity = EntityState(id=10, kind="hero", position=(0,0), 
                         inventory=InventoryComponent(max_slots=1, items=[ItemStack("iron_ore", 1)]))
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
