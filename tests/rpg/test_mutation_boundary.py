import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, InventoryComponent, CombatComponent, BiologicalComponent, AptitudeComponent, StaminaComponent
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate, RewardUpdate, CombatUpdate, ResourceTransferIntent, ItemStack, QuestUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder

def test_mutation_boundary_strips_unauthorized_gold():
    # Setup
    e_id = 1
    entity = (V2EntityBuilder(e_id)
        .kind("HERO")
        .location(0, 0)
        .inventory(gold=100)
        .combat(hp=100, max_hp=100)
        .identity(evolution_level=1)
        .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    # Unauthorized worker update trying to give self gold
    unauthorized_upd = EntityUpdate(
        entity_id=e_id,
        inventory=InventoryUpdate(gold_delta=999)
    )
    raw_update = StateUpdate(entity_updates={e_id: unauthorized_upd})
    
    # Process through pipeline
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify gold delta is stripped
    ent_ref = refined.entity_updates.get(e_id)
    assert ent_ref is not None
    assert ent_ref.inventory is None
    
def test_mutation_boundary_strips_unauthorized_items():
    e_id = 1
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    unauthorized_upd = EntityUpdate(
        entity_id=e_id,
        inventory=InventoryUpdate(items_add=[ItemStack("legendary_sword", 1)])
    )
    raw_update = StateUpdate(entity_updates={e_id: unauthorized_upd})
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    assert refined.entity_updates[e_id].inventory is None

def test_mutation_boundary_strips_unauthorized_xp():
    e_id = 1
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    unauthorized_upd = EntityUpdate(
        entity_id=e_id,
        reward=RewardUpdate(xp_gain=5000)
    )
    raw_update = StateUpdate(entity_updates={e_id: unauthorized_upd})
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    assert refined.entity_updates[e_id].reward is None

def test_mutation_boundary_strips_combat_rewards():
    e_id = 1
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    # Worker trying to sneak in gold through a combat intent
    # Note: gold_gain/xp_gain moved to ResourceTransferIntent in V2
    unauthorized_upd = EntityUpdate(
        entity_id=e_id,
        combat=CombatUpdate(damage_taken=5),
        resource_transfers=[
            ResourceTransferIntent(
                source_id="KILL_1",
                source_kind="KILL",
                gold_delta=100,
                transfer_kind="KILL_REWARD"
            )
        ]
    )
    raw_update = StateUpdate(entity_updates={e_id: unauthorized_upd})
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify KILL_REWARD is stripped
    assert len(refined.entity_updates[e_id].resource_transfers) == 0
    
    # Verify legitimate field preserved
    combat_ref = refined.entity_updates[e_id].combat
    assert combat_ref is not None
    assert combat_ref.damage_taken == 5

def test_mutation_boundary_allows_intents():
    e_id = 1
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    # Intent should be preserved
    intent = ResourceTransferIntent(
        source_id="NODE_1",
        source_kind="NODE",
        items_add=[ItemStack("wood", 1)],
        transfer_kind="HARVEST"
    )
    upd = EntityUpdate(
        entity_id=e_id,
        resource_transfers=[intent]
    )
    raw_update = StateUpdate(entity_updates={e_id: upd})
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    # Intents are cleared after being resolved in the pipeline, so we check intent_results
    assert len(refined.entity_updates[e_id].intent_results) == 1
    assert refined.entity_updates[e_id].intent_results[0].source_id == "NODE_1"

def test_mutation_boundary_strips_unauthorized_intents():
    e_id = 1
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    # QUEST_REWARD intent should be stripped from worker
    intent = ResourceTransferIntent(
        source_id="QUEST_1",
        source_kind="QUEST",
        items_add=[ItemStack("gold", 1000)],
        transfer_kind="QUEST_REWARD"
    )
    upd = EntityUpdate(
        entity_id=e_id,
        resource_transfers=[intent]
    )
    raw_update = StateUpdate(entity_updates={e_id: upd})
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    assert len(refined.entity_updates[e_id].resource_transfers) == 0

def test_mutation_boundary_strips_quest_status():
    from src.core.quests import QuestStatus
    e_id = 1
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    # Worker trying to skip to COMPLETED
    unauthorized_upd = EntityUpdate(
        entity_id=e_id,
        quest=QuestUpdate(quest_id="Q1", status_set=QuestStatus.COMPLETED)
    )
    raw_update = StateUpdate(entity_updates={e_id: unauthorized_upd})
    
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    quest_ref = refined.entity_updates[e_id].quest
    assert quest_ref is not None
    assert quest_ref.status_set is None
    assert quest_ref.quest_id == "Q1"
