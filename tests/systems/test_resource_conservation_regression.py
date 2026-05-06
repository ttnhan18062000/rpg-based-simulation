import pytest
from src.core.state import (
    AuthoritativeState, EntityState, ResourceNodeState, 
    InteractionComponent, InventoryComponent, ItemStack,
    GroundItemState, CorpseState, NavigationComponent, LifecycleComponent,
    IdentityComponent, CombatComponent, BiologicalComponent,
    StrategicComponent
)
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate
from src.engine.interaction import InteractionSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

def make_actor(eid: int, pos=(1.0, 1.0), interaction=None, inventory=None):
    from src.core.builder import V2EntityBuilder
    from dataclasses import replace
    builder = (V2EntityBuilder(eid)
        .kind("hero")
        .location(pos[0], pos[1])
        .combat(alive=True)
        .combat(readiness=100.0))
    
    if interaction:
        # Manually set interaction since builder might not support all fields
        pass
        
    if inventory:
        builder.max_slots(inventory.max_slots)
        builder.gold(inventory.gold)
        for item in inventory.items:
            builder.item(item.item_id, item.quantity)
            
    entity = builder.build()
    
    if interaction:
        entity = replace(entity, interaction=interaction)
        
    return entity

def test_harvest_conservation_full_inventory():
    """Law of Capacity: Progress reset and NO node depletion if inventory is full."""
    # Setup: Entity with full inventory (max 1 slot, 1 item)
    actor = make_actor(1, pos=(1.0, 1.0),
        interaction=InteractionComponent(target_node_id=500, progress=9), # 1 tick left
        inventory=InventoryComponent(max_slots=1, items=[ItemStack("stone", 1)])
    )
    node = ResourceNodeState(
        id=500, kind="WOOD", position=(1.0, 1.0), yields_item="wood",
        remaining_charges=5, max_charges=5, required_ticks=10
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, resource_nodes={500: node})
    
    # Propose finishing the harvest
    # We use the pipeline refinement to simulate real engine behavior
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    # Assertions
    assert e_upd.interaction.reset == True
    assert e_upd.inventory is None  # No items added
    assert 500 not in refined.node_updates  # NO node depletion proposed or refined
    
    # Verify atomicity: if a system proposed depletion, it should be stripped
    from src.core.updates import ResourceNodeUpdate
    update_with_depletion = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
        },
        node_updates={
            500: ResourceNodeUpdate(node_id=500, charges_delta=-1)
        }
    )
    
    refined_2 = AuthoritativeApplyPipeline.refine(state, update_with_depletion)
    assert 500 not in refined_2.node_updates # MUST BE STRIPPED

def test_loot_conservation_full_inventory():
    """Law of Capacity: Ground item remains if inventory is full."""
    actor = make_actor(1, pos=(1.0, 1.0),
        interaction=InteractionComponent(target_node_id=600, progress=9),
        inventory=InventoryComponent(max_slots=1, items=[ItemStack("stone", 1)])
    )
    ground_item = GroundItemState(
        id=600, item_id="iron_ore", quantity=1, position=(1.0, 1.0)
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, ground_items={600: ground_item})
    
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    assert refined.entity_updates[1].interaction.reset == True
    assert 600 not in refined.ground_items_remove # MUST NOT BE REMOVED

def test_corpse_conservation_full_inventory():
    """Law of Capacity: Corpse remains if inventory is full."""
    actor = make_actor(1, pos=(1.0, 1.0),
        interaction=InteractionComponent(target_node_id=700, progress=9),
        inventory=InventoryComponent(max_slots=1, items=[ItemStack("stone", 1)])
    )
    corpse = CorpseState(
        id=700, original_entity_id=99, position=(1.0, 1.0), 
        items=[ItemStack("gold_coin", 10)], decay_tick=100
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, corpses={700: corpse})
    
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    assert refined.entity_updates[1].interaction.reset == True
    assert 700 not in refined.corpses_remove # MUST NOT BE REMOVED

def test_explicit_intent_resolution():
    """Verify that explicit ResourceTransferIntent is correctly resolved."""
    actor = make_actor(1, pos=(1.0, 1.0),
        interaction=InteractionComponent(target_node_id=500, progress=10),
        inventory=InventoryComponent(max_slots=10, items=[])
    )
    node = ResourceNodeState(
        id=500, kind="WOOD", position=(1.0, 1.0), yields_item="wood",
        remaining_charges=5, max_charges=5, required_ticks=10
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor}, resource_nodes={500: node})
    
    from src.core.updates import ResourceTransferIntent
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1, 
                interaction=InteractionUpdate(reset=True),
                resource_transfers=[ResourceTransferIntent(
                    source_id=500,
                    source_kind="NODE",
                    items_add=[ItemStack("wood", 1)],
                    transfer_kind="HARVEST"
                )]
            )
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    assert refined.entity_updates[1].inventory.items_add[0].item_id == "wood"
    assert refined.node_updates[500].charges_delta == -1

def test_crafting_conservation_no_materials():
    """Law of Materials: Crafting fails if materials are missing."""
    actor = make_actor(1, pos=(1.0, 1.0),
        inventory=InventoryComponent(gold=100, items=[]) # Missing materials
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor})
    
    from src.core.updates import ResourceTransferIntent
    intent = ResourceTransferIntent(
        source_id="steel_sword",
        source_kind="CRAFTING",
        items_add=[ItemStack("steel_sword", 1)],
        items_remove=[ItemStack("iron_ore", 2)],
        gold_cost=50,
        transfer_kind="CRAFT"
    )
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    assert e_upd.inventory is None
    assert not e_upd.resource_transfers # Cleared

def test_shop_buy_conservation_insufficient_gold():
    """Law of Value: Shop buy fails if gold is insufficient."""
    actor = make_actor(1, pos=(1.0, 1.0),
        inventory=InventoryComponent(gold=10, items=[])
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor})
    
    from src.core.updates import ResourceTransferIntent
    intent = ResourceTransferIntent(
        source_id="iron_sword",
        source_kind="SHOP_BUY",
        items_add=[ItemStack("iron_sword", 1)],
        gold_cost=50,
        transfer_kind="BUY"
    )
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    assert e_upd.inventory is None
    assert not e_upd.resource_transfers

def test_shop_sell_conservation_missing_items():
    """Law of Property: Shop sell fails if items are missing."""
    actor = make_actor(1, pos=(1.0, 1.0),
        inventory=InventoryComponent(gold=0, items=[])
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor})
    
    from src.core.updates import ResourceTransferIntent
    intent = ResourceTransferIntent(
        source_id="wood",
        source_kind="SHOP_SELL",
        items_remove=[ItemStack("wood", 10)],
        gold_delta=50,
        transfer_kind="SELL"
    )
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    e_upd = refined.entity_updates[1]
    
    assert e_upd.inventory is None
