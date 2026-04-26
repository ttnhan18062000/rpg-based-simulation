import pytest
from src.core.state import AuthoritativeState, EntityState, InventoryComponent, InteractionComponent, ResourceNodeState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate
from src.engine.interaction import InteractionSystem
from src.engine.town_resolution import TownResolutionSystem

def test_weight_pressure_enforcement():
    # Setup state: Entity with limited weight capacity
    inv = InventoryComponent(items=[ItemStack("wood", 2)], max_weight=5.0)
    entity = EntityState(id=1, kind="HERO", position=(0,0), inventory=inv)
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={10: ResourceNodeState(id=10, kind="ORE", position=(0,0), yields_item="ore", remaining_charges=1, max_charges=1, required_ticks=1)}
    )
    
    # Interaction: Finish harvest of ORE (Weight 5.0)
    # Total weight would be 4.0 + 5.0 = 9.0 > 5.0
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0, target_node_id=10))}
    )
    
    refined = InteractionSystem.enforce(state, upd)
    ent_upd = refined.entity_updates[1]
    
    # Should have been reset due to weight pressure
    assert ent_upd.interaction.reset is True
    assert ent_upd.inventory is None

def test_channeled_looting_one_shot():
    # Setup state: LOOT node
    inv = InventoryComponent(items=[], max_weight=100.0)
    entity = EntityState(id=1, kind="HERO", position=(0,0), inventory=inv, interaction=InteractionComponent(progress=9, target_node_id=10))
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={10: ResourceNodeState(id=10, kind="LOOT", position=(0,0), yields_item="gold", remaining_charges=10, max_charges=10, required_ticks=10)}
    )
    
    # Interaction: Finish looting
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))}
    )
    
    refined = InteractionSystem.enforce(state, upd)
    
    # Node update should have charges_delta = -10 (ALL charges consumed for LOOT)
    node_upd = refined.node_updates[10]
    assert node_upd.charges_delta == -10
    
    # Entity should get the item
    actual_added = [i.item_id if hasattr(i, "item_id") else i for i in refined.entity_updates[1].inventory.items_add]
    assert "gold" in actual_added

def test_town_resolution_sell_on_entry():
    # Setup state: Entity with materials entering town
    inv = InventoryComponent(items=["wood", "ore"], max_weight=100.0)
    # Target position is (5,5) which we will mark as town
    entity = EntityState(id=1, kind="HERO", position=(0,0), inventory=inv)
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        town_tiles={(5,5)},
        building_tiles={(5,5): "shop"}
    )
    
    # Update: Move to (5,5)
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, new_position=(5,5), moved_this_tick=True)}
    )
    
    # Resolve
    from src.engine.pipeline import AuthoritativeApplyPipeline
    refined = AuthoritativeApplyPipeline.refine(state, upd)
    
    ent_upd = refined.entity_updates[1]
    actual_removed = [i.item_id if hasattr(i, "item_id") else i for i in ent_upd.inventory.items_remove]
    assert "wood" in actual_removed
    assert "ore" in actual_removed
    
    # Value: WOOD(5) + ORE(5) = 10 GOLD
    assert ent_upd.inventory.gold_delta == 10

def test_movement_interruption():
    # Setup state: Channelling interaction
    entity = EntityState(id=1, kind="HERO", position=(0,0), interaction=InteractionComponent(progress=5, target_node_id=10))
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # Update: Move while channelling
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, moved_this_tick=True, interaction=InteractionUpdate(progress_delta=1.0))}
    )
    
    refined = InteractionSystem.enforce(state, upd)
    assert refined.entity_updates[1].interaction.reset is True
