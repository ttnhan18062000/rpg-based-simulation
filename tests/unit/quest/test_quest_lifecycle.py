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
    
    from src.engine.pipeline import AuthoritativeApplyPipeline
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    new_state = ApplyPath.apply_generation(state, refined)
    new_entity = new_state.entities[entity.id]
    new_quest = new_entity.strategic.projects["q1"]
    
    # Verify status transition (Auto-Rewarded)
    assert new_quest.quest_status == QuestStatus.REWARDED
    
    # Verify rewards applied
    # XP should be 100 * 1.0 (No bonus) = 100. 
    # Level 1->2 cost is 100. So 0 points remain.
    assert new_entity.identity.evolution_points == 0
    assert new_entity.identity.evolution_level == 2
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
    from src.engine.pipeline import AuthoritativeApplyPipeline
    refined1 = AuthoritativeApplyPipeline.refine(state, state_upd1)
    state1 = ApplyPath.apply_generation(state, refined1)
    entity1 = state1.entities[entity.id]
    xp_after_1 = entity1.identity.evolution_points
    
    # 2. Apply more progress to already REWARDED quest
    update2 = EntityUpdate(
        entity_id=entity.id,
        quest=QuestUpdate(quest_id="q1", progress_delta=5.0)
    )
    state_upd2 = StateUpdate(entity_updates={entity.id: update2})
    refined2 = AuthoritativeApplyPipeline.refine(state1, state_upd2)
    state2 = ApplyPath.apply_generation(state1, refined2)
    entity2 = state2.entities[entity.id]
    
    # Verify no extra XP gained
    assert entity2.identity.evolution_points == xp_after_1
    assert entity2.strategic.projects["q1"].quest_status == QuestStatus.REWARDED


# ─── E23B New Tests ──────────────────────────────────────────────────────────

from src.core.models.quests import QuestOpportunity, QuestOpportunityStatus
from src.domains.world_emergence.services import QuestLifecycleService


def _make_opp(opp_id: str, expiry_ticks: int, status: QuestOpportunityStatus = QuestOpportunityStatus.OFFERED) -> QuestOpportunity:
    return QuestOpportunity(
        id=opp_id,
        kind="resource_crisis",
        trigger_condition="test trigger",
        objective_chain=("fetch:iron_ore:1",),
        reward_spec={"gold": 10, "xp": 50},
        faction_source=None,
        expiry_ticks=expiry_ticks,
        source_event_id="ev_test",
        status=status,
    )


def test_quest_registry_field_on_authoritative_state():
    """AC-1: quest_registry field exists on AuthoritativeState and is immutable."""
    state = AuthoritativeState(tick=0, seed=42)
    assert hasattr(state, "quest_registry")
    assert state.quest_registry == {}

    opp = _make_opp("opp1", expiry_ticks=100)
    new_state = replace(state, quest_registry={"opp1": opp})
    assert new_state.quest_registry["opp1"] == opp
    assert state.quest_registry == {}
    assert state.quest_registry is not new_state.quest_registry


def test_quest_opportunity_status_enum_values():
    """AC-2: QuestOpportunityStatus has all six expected values."""
    assert QuestOpportunityStatus.OFFERED
    assert QuestOpportunityStatus.ACTIVE
    assert QuestOpportunityStatus.PROGRESSED
    assert QuestOpportunityStatus.COMPLETED
    assert QuestOpportunityStatus.FAILED
    assert QuestOpportunityStatus.EXPIRED
    assert isinstance(QuestOpportunityStatus.OFFERED.value, str)


def test_quest_opportunity_defaults_to_offered():
    """AC-3: QuestOpportunity.status defaults to OFFERED when not specified."""
    opp = QuestOpportunity(
        id="rc_ev1_42",
        kind="resource_crisis",
        trigger_condition="iron depleted in north at tick 5",
        objective_chain=("fetch:iron_ore:3",),
        reward_spec={"gold": 10, "xp": 50},
        faction_source=None,
        expiry_ticks=100,
        source_event_id="ev1",
    )
    assert opp.status == QuestOpportunityStatus.OFFERED


def test_quest_expires_after_expiry_ticks():
    """AC-5: OFFERED quest past expiry_ticks is removed and an event is emitted."""
    opp = _make_opp("opp1", expiry_ticks=10)
    state = AuthoritativeState(tick=11, seed=0, quest_registry={"opp1": opp})

    upd = QuestLifecycleService.tick(state)

    assert "opp1" in upd.quest_registry_remove
    assert len(upd.world_events_add) == 1

    new_state = ApplyPath.apply_generation(state, upd, next_tick=11)
    assert new_state.quest_registry == {}


def test_quest_not_expired_before_expiry_ticks():
    """AC-6: Quest still OFFERED before expiry_ticks — lifecycle tick is noop."""
    opp = _make_opp("opp1", expiry_ticks=10)
    state = AuthoritativeState(tick=9, seed=0, quest_registry={"opp1": opp})

    upd = QuestLifecycleService.tick(state)

    assert upd.quest_registry_remove == []
    assert upd.is_noop()


def test_quest_offered_to_active_transition():
    """AC-7: OFFERED → ACTIVE transition is authoritative via StateUpdate."""
    opp = _make_opp("opp1", expiry_ticks=100)
    state = AuthoritativeState(tick=1, seed=0, quest_registry={"opp1": opp})

    upd = StateUpdate(quest_status_updates={"opp1": QuestOpportunityStatus.ACTIVE})
    new_state = ApplyPath.apply_generation(state, upd)

    assert new_state.quest_registry["opp1"].status == QuestOpportunityStatus.ACTIVE


def test_quest_registry_add_is_idempotent():
    """AC-8: Adding an existing quest id is a no-op (idempotent by id)."""
    opp = _make_opp("opp1", expiry_ticks=100)
    state = AuthoritativeState(tick=1, seed=0, quest_registry={"opp1": opp})

    modified_opp = replace(opp, kind="threat_response")
    upd = StateUpdate(quest_registry_add=[modified_opp])
    new_state = ApplyPath.apply_generation(state, upd)

    assert len(new_state.quest_registry) == 1
    assert new_state.quest_registry["opp1"].kind == "resource_crisis"


def test_expiry_sweep_deterministic_order():
    """AC-9: Expiry sweep produces the same removal list in sorted order on repeated calls."""
    registry = {
        "opp_c": _make_opp("opp_c", expiry_ticks=5),
        "opp_a": _make_opp("opp_a", expiry_ticks=3),
        "opp_b": _make_opp("opp_b", expiry_ticks=4),
    }
    state = AuthoritativeState(tick=20, seed=0, quest_registry=registry)

    upd1 = QuestLifecycleService.tick(state)
    upd2 = QuestLifecycleService.tick(state)

    assert upd1.quest_registry_remove == upd2.quest_registry_remove
    assert upd1.quest_registry_remove == sorted(upd1.quest_registry_remove)


def test_entity_quest_status_unaffected_by_e23b():
    """AC-10: Existing QuestStatus enum (REWARDED, REWARD_PENDING) is unchanged."""
    from src.core.models.quests import QuestStatus as QS
    assert QS.REWARDED
    assert QS.REWARD_PENDING
    assert QS.ACTIVE
    assert QS.COMPLETED
    assert QS.REWARDED.value == 3
    assert QS.REWARD_PENDING.value == 4
