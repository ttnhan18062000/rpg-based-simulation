"""
Tests for TCK-20260903-INFORMATION-HUB-ACCUMULATION Steps 1, 2 and 4:

  - Step 1: ApplyPath.apply_generation now carries AuthoritativeState.information_providers
    forward and merges StateUpdate.information_providers_update into it (previously a
    silent-reset bug -- see src/engine/apply.py).
  - Step 2: InformationProviderState gains a new knowledge_accumulated field.
  - Step 4: InformationAccumulationService + QuestResolutionSystem.enforce()'s
    is_newly_completed hook increments knowledge_accumulated and resets knowledge_age when a
    quest whose source_entity_id is a provider is reported back (flag-gated).
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.quests import QuestKind, QuestState, QuestStatus, RewardState
from src.core.state import AuthoritativeState
from src.core.strategic import LeadCertainty, LeadKind, LeadState, ProjectKind
from src.core.updates import EntityUpdate, QuestUpdate, StateUpdate
from src.domains.information.accumulation import InformationAccumulationService
from src.domains.information.providers import InformationProviderArchetype, InformationProviderState
from src.engine.apply import ApplyPath
from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
from src.engine.quests import QuestResolutionSystem


def _base_state(**overrides) -> AuthoritativeState:
    defaults = dict(tick=100, seed=1)
    defaults.update(overrides)
    return AuthoritativeState(**defaults)


# ---------------------------------------------------------------------------
# Step 2 -- new field
# ---------------------------------------------------------------------------
def test_information_provider_accumulation_field_default():
    provider = InformationProviderState(entity_id=1, archetype=InformationProviderArchetype.GUILD_MASTER)
    assert provider.knowledge_accumulated == 0
    assert provider.to_canonical_dict()["knowledge_accumulated"] == 0


# ---------------------------------------------------------------------------
# Step 1 -- apply-path wiring fix
# ---------------------------------------------------------------------------
def test_information_providers_update_survives_apply_generation():
    provider = InformationProviderState(entity_id=5, archetype=InformationProviderArchetype.MERCHANT)
    state = _base_state()
    update = StateUpdate(information_providers_update={5: provider})

    state_v2 = ApplyPath.apply_generation(state, update, next_tick=101)

    assert state_v2.information_providers[5] == provider

    # A second tick with no updates must carry the provider forward (not reset to {}).
    state_v3 = ApplyPath.apply_generation(state_v2, StateUpdate(), next_tick=102)
    assert state_v3.information_providers[5] == provider


def test_lead_contradiction_reliability_decrement_survives_apply_generation():
    """Regression proof: LeadContradictionSystem's existing reliability_score decrement
    (STRAT-230) previously never survived a tick boundary because apply.py never wired
    information_providers into the AuthoritativeState constructor call. Step 1 fixes this."""
    provider = InformationProviderState(
        entity_id=99, archetype=InformationProviderArchetype.ELDER, reliability_score=1.0,
    )

    # A "person" lead pointing at a nonexistent entity id is unconditionally contradicted --
    # the simplest branch of _is_lead_contradicted, requiring no extra world scaffolding.
    lead = LeadState(
        id="lead1", kind=LeadKind.PERSON, subject="12345",
        certainty=LeadCertainty.VAGUE, source_entity_id=99,
    )
    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .strategic(leads={"lead1": lead})
        .build()
    )

    state = _base_state(entities={1: entity}, information_providers={99: provider})

    refined_update, events = LeadContradictionSystem.enforce(state, StateUpdate())
    assert refined_update.information_providers_update[99].reliability_score == 0.9
    assert len(events) >= 1

    state_v2 = ApplyPath.apply_generation(state, refined_update, next_tick=101)
    assert state_v2.information_providers[99].reliability_score == 0.9

    # Carries forward across a further tick with no new updates.
    state_v3 = ApplyPath.apply_generation(state_v2, StateUpdate(), next_tick=102)
    assert state_v3.information_providers[99].reliability_score == 0.9


# ---------------------------------------------------------------------------
# Step 4 -- accumulation trigger
# ---------------------------------------------------------------------------
def test_accumulation_service_increments_and_resets_freshness():
    provider = InformationProviderState(
        entity_id=1, archetype=InformationProviderArchetype.GUILD_MASTER,
        knowledge_accumulated=2, knowledge_age=50,
    )
    updated = InformationAccumulationService.record_quest_reported_back(provider)
    assert updated.knowledge_accumulated == 3
    assert updated.knowledge_age == 0
    assert updated.reliability_score == provider.reliability_score


def _entity_with_reported_quest(quest_id: str, provider_id: int):
    quest = QuestState(
        id=quest_id, kind=ProjectKind.QUEST, quest_kind=QuestKind.EXPLORE,
        quest_status=QuestStatus.ACTIVE, goal_value=0.0, current_value=0.0,
        reward=RewardState(), source_entity_id=provider_id,
    )
    return (
        V2EntityBuilder(2)
        .kind("hero")
        .location(0, 0)
        .strategic(projects={quest_id: quest})
        .build()
    )


def test_quest_completion_increments_provider_accumulation_when_flag_on():
    provider = InformationProviderState(entity_id=99, archetype=InformationProviderArchetype.ELDER)
    entity = _entity_with_reported_quest("q1", provider_id=99)
    state = _base_state(
        entities={2: entity},
        information_providers={99: provider},
        feature_flags={"ENABLE_INFORMATION_HUB_ACCUMULATION": "ON"},
    )
    update = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, quest=QuestUpdate(quest_id="q1"))})

    refined_update = QuestResolutionSystem.enforce(state, update)

    assert refined_update.information_providers_update[99].knowledge_accumulated == 1
    assert refined_update.information_providers_update[99].knowledge_age == 0

    state_v2 = ApplyPath.apply_generation(state, refined_update, next_tick=101)
    assert state_v2.information_providers[99].knowledge_accumulated == 1
    assert state_v2.information_providers[99].knowledge_age == 0


def test_quest_completion_does_not_increment_provider_accumulation_when_flag_off():
    provider = InformationProviderState(entity_id=99, archetype=InformationProviderArchetype.ELDER)
    entity = _entity_with_reported_quest("q1", provider_id=99)
    state = _base_state(
        entities={2: entity},
        information_providers={99: provider},
        # ENABLE_INFORMATION_HUB_ACCUMULATION intentionally absent -> defaults OFF.
    )
    update = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, quest=QuestUpdate(quest_id="q1"))})

    refined_update = QuestResolutionSystem.enforce(state, update)

    assert 99 not in refined_update.information_providers_update

    state_v2 = ApplyPath.apply_generation(state, refined_update, next_tick=101)
    assert state_v2.information_providers[99].knowledge_accumulated == 0
