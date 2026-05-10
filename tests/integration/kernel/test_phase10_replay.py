# tests/engine/test_phase10_replay.py
import pytest
from src.core.state import AuthoritativeState, EntityState, ResourceNodeState
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent, ItemStack
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.systems.generator import EntityGenerator

def test_transaction_tracing_and_replay():
    """
    Verifies that:
    1. Rejected transaction reasons are recorded in EntityState.
    2. Successful transactions update global conservation metrics.
    3. The trace is reproducible in a replay scenario.
    """
    generator = EntityGenerator(seed=42)
    
    # 1. Setup world with a full-inventory entity and a node
    node = ResourceNodeState(
        id=500, kind="WOOD", position=(10, 10), yields_item="wood_log",
        remaining_charges=5, max_charges=5, required_ticks=10
    )
    
    # Hero with full inventory (max_slots=1)
    hero = generator.spawn_hero((10, 10))
    from dataclasses import replace
    hero = replace(hero, inventory=replace(hero.inventory, max_slots=1, items=[ItemStack("herb", 1)]))
    
    state = AuthoritativeState(tick=0, seed=42, entities={hero.id: hero}, resource_nodes={node.id: node})
    
    # 2. Intent: Harvest the node (Should fail due to INVENTORY_FULL)
    intent = ResourceTransferIntent(
        source_id=node.id,
        source_kind="NODE",
        items_add=[ItemStack("wood", 1)],
        transfer_kind="HARVEST",
        transaction_id="TX_FAIL_1"
    )
    
    update = StateUpdate(entity_updates={
        hero.id: EntityUpdate(entity_id=hero.id, resource_transfers=[intent])
    })
    
    # 3. Resolve and Apply
    # Pipeline handles transaction resolution
    resolved_update = AuthoritativeApplyPipeline._resolve_resource_transactions(state, update)
    new_state = ApplyPath.apply_generation(state, resolved_update, next_tick=1)
    
    # 4. Verify Tracing
    hero_post = new_state.entities[hero.id]
    assert len(hero_post.identity.latest_intent_results) == 1
    res = hero_post.identity.latest_intent_results[0]
    assert res.transaction_id == "TX_FAIL_1"
    assert res.accepted is False
    assert res.reason == "INVENTORY_FULL"
    
    # 5. Success Case & Metrics
    # Free a slot
    hero_ready = replace(hero_post, inventory=replace(hero_post.inventory, items=[]))
    state_v2 = replace(new_state, entities={hero_ready.id: hero_ready}, tick=1)
    
    intent_v2 = ResourceTransferIntent(
        source_id=node.id,
        source_kind="NODE",
        items_add=[ItemStack("wood", 1)],
        transfer_kind="HARVEST",
        transaction_id="TX_SUCCESS_1"
    )
    
    update_v2 = StateUpdate(entity_updates={
        hero_ready.id: EntityUpdate(entity_id=hero_ready.id, resource_transfers=[intent_v2])
    })
    
    resolved_update_v2 = AuthoritativeApplyPipeline._resolve_resource_transactions(state_v2, update_v2)
    state_v3 = ApplyPath.apply_generation(state_v2, resolved_update_v2, next_tick=2)
    
    # Verify Metrics
    assert state_v3.global_resources.get("metric_total_wood") == 1
    
    # 6. Replay Verification
    # If we apply the SAME resolved_update_v2 to the SAME state_v2, we should get bit-identical state_v3
    state_replay = ApplyPath.apply_generation(state_v2, resolved_update_v2, next_tick=2)
    assert state_replay == state_v3
    assert state_replay.entities[hero_ready.id].identity.latest_intent_results[0].accepted is True
