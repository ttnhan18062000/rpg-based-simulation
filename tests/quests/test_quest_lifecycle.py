import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState
from src.core.quests import QuestState, QuestStatus, RewardState, QuestKind
from src.core.strategic import StrategicComponent
from src.core.updates import EntityUpdate, QuestUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole

@pytest.fixture
def base_entity():
    return V2EntityBuilder(entity_id=1).role(EntityRole.HERO).build()

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

def test_quest_initialization(active_quest):
    assert active_quest.quest_status == QuestStatus.ACTIVE
    assert active_quest.current_value == 0.0
    assert active_quest.progress_ratio == 0.0

def test_quest_progress_authoritative(base_entity, active_quest):
    # Setup entity with quest
    strat = StrategicComponent(projects={"q1": active_quest})
    entity = replace(base_entity, strategic=strat)
    
    # Setup state
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # Apply progress update
    update = EntityUpdate(
        entity_id=entity.id,
        quest=QuestUpdate(quest_id="q1", progress_delta=2.0)
    )
    state_upd = StateUpdate(entity_updates={entity.id: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    new_entity = new_state.entities[entity.id]
    new_quest = new_entity.strategic.projects["q1"]
    
    assert new_quest.current_value == 2.0
    assert new_quest.quest_status == QuestStatus.ACTIVE

def test_quest_completion_and_reward_emission(base_entity, active_quest):
    # Setup entity with quest
    strat = StrategicComponent(projects={"q1": active_quest})
    entity = replace(base_entity, strategic=strat)
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # Apply progress update that completes the quest
    update = EntityUpdate(
        entity_id=entity.id,
        quest=QuestUpdate(quest_id="q1", progress_delta=5.0)
    )
    state_upd = StateUpdate(entity_updates={entity.id: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    new_entity = new_state.entities[entity.id]
    new_quest = new_entity.strategic.projects["q1"]
    
    # Verify status transition (Auto-Rewarded)
    assert new_quest.quest_status == QuestStatus.REWARDED
    
    # Verify rewards applied (Note: level up happens if XP >= 100)
    # base_entity is level 1, points 0.
    # After +100 XP, it should be level 2, points 0.
    assert new_entity.identity.evolution_level == 2
    assert new_entity.identity.evolution_points == 0
    assert new_entity.inventory.gold == entity.inventory.gold + 50
    assert any(item.item_id == "iron_sword" for item in new_entity.inventory.items)

def test_no_double_completion(base_entity, active_quest):
    # Setup entity with quest
    strat = StrategicComponent(projects={"q1": active_quest})
    entity = replace(base_entity, strategic=strat)
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # 1. Complete quest
    update1 = EntityUpdate(
        entity_id=entity.id,
        quest=QuestUpdate(quest_id="q1", progress_delta=5.0)
    )
    state_upd1 = StateUpdate(entity_updates={entity.id: update1})
    state1 = ApplyPath.apply_generation(state, state_upd1)
    entity1 = state1.entities[entity.id]
    xp_after_1 = entity1.identity.evolution_points
    
    # 2. Apply more progress to already REWARDED quest
    update2 = EntityUpdate(
        entity_id=entity.id,
        quest=QuestUpdate(quest_id="q1", progress_delta=5.0)
    )
    state_upd2 = StateUpdate(entity_updates={entity.id: update2})
    state2 = ApplyPath.apply_generation(state1, state_upd2)
    entity2 = state2.entities[entity.id]
    
    # Verify no extra XP gained
    assert entity2.identity.evolution_points == xp_after_1
    assert entity2.strategic.projects["q1"].quest_status == QuestStatus.REWARDED
