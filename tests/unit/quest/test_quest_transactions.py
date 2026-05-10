import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, ItemStack
from src.core.quests import QuestState, QuestStatus, RewardState, QuestKind
from src.core.strategic import StrategicComponent
from src.core.updates import EntityUpdate, QuestUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.engine.pipeline import AuthoritativeApplyPipeline

@pytest.fixture
def base_entity():
    return V2EntityBuilder(entity_id=1).identity(role=EntityRole.HERO).build()

@pytest.fixture
def active_quest():
    return QuestState(
        id="q1",
        kind="quest",
        quest_kind=QuestKind.HUNT,
        quest_status=QuestStatus.ACTIVE,
        goal_value=5.0,
        current_value=0.0,
        reward=RewardState(xp=100, gold=50, items=["iron_sword"])
    )

def test_successful_quest_reward_transaction(base_entity, active_quest):
    # Setup entity with quest
    strat = StrategicComponent(projects={"q1": active_quest})
    entity = replace(base_entity, strategic=strat)
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # Complete the quest
    update = EntityUpdate(
        entity_id=entity.id,
        quest=QuestUpdate(quest_id="q1", progress_delta=5.0)
    )
    state_upd = StateUpdate(entity_updates={entity.id: update})
    
    # Refine (should emit intent and mark REWARDED on success)
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    
    # Check that REWARDED status is set in the refined update
    quest_upd = refined.entity_updates[entity.id].quest
    assert quest_upd.status_set == QuestStatus.REWARDED
    
    # Apply
    new_state = ApplyPath.apply_generation(state, refined)
    new_entity = new_state.entities[entity.id]
    new_quest = new_entity.strategic.projects["q1"]
    
    assert new_quest.quest_status == QuestStatus.REWARDED
    assert new_entity.inventory.gold == 50
    assert any(item.item_id == "iron_sword" for item in new_entity.inventory.items)

def test_full_inventory_blocks_quest_reward(base_entity, active_quest):
    # Fill inventory to capacity
    # Default max_slots is 16 for entities built by V2EntityBuilder
    items = [ItemStack(item_id="herb", quantity=1) for i in range(16)]
    entity = replace(base_entity, 
        inventory=replace(base_entity.inventory, items=items),
        strategic=StrategicComponent(projects={"q1": active_quest})
    )
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # Complete the quest
    update = EntityUpdate(
        entity_id=entity.id,
        quest=QuestUpdate(quest_id="q1", progress_delta=5.0)
    )
    state_upd = StateUpdate(entity_updates={entity.id: update})
    
    # Refine
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    
    # Should be REWARD_PENDING because transaction failed
    quest_upd = refined.entity_updates[entity.id].quest
    assert quest_upd.status_set == QuestStatus.REWARD_PENDING
    
    # Apply
    new_state = ApplyPath.apply_generation(state, refined)
    new_quest = new_state.entities[entity.id].strategic.projects["q1"]
    
    assert new_quest.quest_status == QuestStatus.REWARD_PENDING
    assert new_state.entities[entity.id].inventory.gold == 0

def test_recovery_after_freeing_inventory(base_entity, active_quest):
    # Setup quest in REWARD_PENDING
    pending_quest = replace(active_quest, quest_status=QuestStatus.REWARD_PENDING, current_value=5.0)
    
    # Fill inventory
    items = [ItemStack(item_id="herb", quantity=1) for i in range(16)]
    entity = replace(base_entity, 
        inventory=replace(base_entity.inventory, items=items),
        strategic=StrategicComponent(projects={"q1": pending_quest})
    )
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # Tick 1: Try to reward (should fail again)
    state_upd = StateUpdate(entity_updates={entity.id: EntityUpdate(entity_id=entity.id, quest=QuestUpdate(quest_id="q1"))})
    refined1 = AuthoritativeApplyPipeline.refine(state, state_upd)
    assert refined1.entity_updates[entity.id].quest.status_set == QuestStatus.REWARD_PENDING
    
    # Tick 2: Free space and retry
    entity_with_space = replace(entity, 
        inventory=replace(entity.inventory, items=items[:-1]) # Remove one item
    )
    state2 = replace(state, entities={entity.id: entity_with_space})
    
    refined2 = AuthoritativeApplyPipeline.refine(state2, state_upd)
    assert refined2.entity_updates[entity.id].quest.status_set == QuestStatus.REWARDED
    
    # Apply
    final_state = ApplyPath.apply_generation(state2, refined2)
    final_quest = final_state.entities[entity.id].strategic.projects["q1"]
    assert final_quest.quest_status == QuestStatus.REWARDED
    assert any(item.item_id == "iron_sword" for item in final_state.entities[entity.id].inventory.items)

def test_idempotency_rewarded_quest_does_not_retry(base_entity, active_quest):
    # Setup quest already REWARDED
    rewarded_quest = replace(active_quest, quest_status=QuestStatus.REWARDED, current_value=5.0)
    entity = replace(base_entity, strategic=StrategicComponent(projects={"q1": rewarded_quest}))
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # Try to tick
    state_upd = StateUpdate(entity_updates={entity.id: EntityUpdate(entity_id=entity.id, quest=QuestUpdate(quest_id="q1"))})
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    
    # Should NOT emit resource transfers or change status
    if entity.id in refined.entity_updates:
        ent_upd = refined.entity_updates[entity.id]
        assert len(ent_upd.resource_transfers) == 0
        if ent_upd.quest:
            assert ent_upd.quest.status_set is None or ent_upd.quest.status_set == QuestStatus.REWARDED
