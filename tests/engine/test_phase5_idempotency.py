import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, ResourceNodeState, IdentityComponent, InventoryComponent
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder

def create_mock_entity(id, pos=(0.0, 0.0)):
    return (V2EntityBuilder(id)
            .kind("hero")
            .location(*pos)
            .active(True)
            .combat(readiness=100.0)
            .build())

def test_resource_node_race():
    # Node with only 1 charge
    node = ResourceNodeState(
        id=100, kind="MINE", position=(0,0), 
        yields_item="iron_ore", remaining_charges=1, max_charges=1,
        required_ticks=1
    )
    e1 = create_mock_entity(1)
    e2 = create_mock_entity(2)
    
    state = AuthoritativeState(
        entities={1: e1, 2: e2},
        resource_nodes={100: node},
        tick=0, seed=1
    )
    
    from src.core.state import ItemStack
    intent1 = ResourceTransferIntent(
        transfer_kind="HARVEST", source_kind="NODE", source_id=100,
        items_add=[ItemStack(item_id="iron_ore", quantity=1)]
    )
    intent2 = replace(intent1)
    
    upd1 = EntityUpdate(entity_id=1, resource_transfers=[intent1])
    upd2 = EntityUpdate(entity_id=2, resource_transfers=[intent2])
    
    raw_update = StateUpdate(entity_updates={1: upd1, 2: upd2})
    
    # Process through pipeline
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Check transaction trace for failures
    trace = [t for t in refined.transaction_trace if "NODE" in t]
    print("\nTransaction Trace:")
    for t in trace:
        print(f"  {t}")
        
    accepted_count = sum(1 for t in trace if "ACCEPT" in t)
    assert accepted_count == 1, f"Expected exactly 1 entity to successfully harvest, but got {accepted_count}"

def test_quest_reward_idempotency():
    e1 = create_mock_entity(1)
    state = AuthoritativeState(entities={1: e1}, tick=0, seed=1)
    
    # Using 'HARVEST' with 'NODE' source twice to test internal group idempotency
    from src.core.state import ItemStack
    node = ResourceNodeState(
        id=100, kind="MINE", position=(0,0), 
        yields_item="iron_ore", remaining_charges=1, max_charges=1,
        required_ticks=1
    )
    state = replace(state, resource_nodes={100: node})

    intent = ResourceTransferIntent(
        transfer_kind="HARVEST", source_kind="NODE", source_id=100,
        items_add=[ItemStack(item_id="iron_ore", quantity=1)]
    )
    
    # Two identical intents for the same entity in one tick
    upd = EntityUpdate(entity_id=1, resource_transfers=[intent, intent])
    raw_update = StateUpdate(entity_updates={1: upd})
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    trace = [t for t in refined.transaction_trace if "NODE" in t]
    accepted_count = sum(1 for t in trace if "ACCEPT" in t)
    
    # Should only accept ONE, because the first one depletes the node
    assert accepted_count == 1, f"Expected 1 acceptance, got {accepted_count}"
