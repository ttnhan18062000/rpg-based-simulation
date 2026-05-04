import pytest
from src.core.state import AuthoritativeState, EntityState, StrategicComponent
from src.core.quests import QuestState, QuestKind, QuestStatus, RewardState
from src.systems.quest_system import QuestSystem

def test_explore_quest_progress():
    # Setup quest
    quest = QuestState(
        id="q1", kind="quest", quest_kind=QuestKind.EXPLORE,
        goal_value=10.0, current_value=5.0,
        reward=RewardState(xp=100)
    )
    # Add metadata for target pos
    quest = quest.replace(metadata={"target_position": (100, 100)})
    
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .at((101, 101))
              .strategic_project(quest)
              .build())
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity}
    )
    
    update = QuestSystem.update(state)
    
    # Verify progress delta
    ent_upd = update.entity_updates[1]
    assert ent_upd.quest.progress_delta == 1.0

def test_bounty_quest_completion():
    quest = QuestState(
        id="q2", kind="quest", quest_kind=QuestKind.BOUNTY,
        goal_value=1.0, current_value=0.0,
        reward=RewardState(gold=500)
    )
    quest = quest.replace(metadata={"target_region_id": "forest"})
    
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .at((0, 0))
              .strategic_project(quest)
              .build())
    
    # Forest is now owned by Neutral (0) or Hero (2), not Monster (1)
    from src.core.state import RegionState
    forest = RegionState(id="forest", name="Forest", bounds=(0,0,10,10), owner_faction_id=2)
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        regions={"forest": forest}
    )
    
    update = QuestSystem.update(state)
    
    # Authoritative refinement handles reward generation and status transition
    from src.engine.pipeline import AuthoritativeApplyPipeline
    update = AuthoritativeApplyPipeline.refine(state, update)
    
    ent_upd = update.entity_updates[1]
    # QuestResolutionSystem + _resolve_resource_transactions will result in REWARD_PENDING or REWARDED
    assert ent_upd.quest.status_set == QuestStatus.REWARDED
    # Gold is now in the intent results or resource transfers
    assert any(res.accepted for res in ent_upd.intent_results if res.source_kind == "QUEST")
