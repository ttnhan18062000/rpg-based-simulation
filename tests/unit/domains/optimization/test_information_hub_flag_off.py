"""
Flag-OFF no-op test for TCK-20260903-INFORMATION-HUB-ACCUMULATION Step 8.

With ENABLE_INFORMATION_HUB_ACCUMULATION left at its default OFF, a quest report-back
scenario that would otherwise trigger accumulation (Step 4) and a critical-severity
WorldEvent that would otherwise trigger propagation (Step 6) must leave
AuthoritativeState.information_providers and AuthoritativeState.recent_world_events
byte-identical across a full AuthoritativeApplyPipeline.refine() + ApplyPath.apply_generation
tick. (See Step 8's AC-wording note: the ticket's own literal wording said "FactionState
unchanged", but propagation never writes FactionState at all -- see the architecture guard in
tests/architecture/test_information_hub_accumulation_guards.py -- so the real target of this
test is information_providers/recent_world_events, per plan.md's correction.)

A second scenario, run with the flag explicitly ON, proves the OFF-path assertions above are
not vacuously true because the scenario itself is a no-op.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.quests import QuestKind, QuestState, QuestStatus, RewardState
from src.core.state import AuthoritativeState, FactionState
from src.core.strategic import ProjectKind
from src.core.updates import EntityUpdate, QuestUpdate, StateUpdate
from src.domains.information.providers import InformationProviderArchetype, InformationProviderState
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline


def _scenario_state(*, flag_on: bool) -> AuthoritativeState:
    provider = InformationProviderState(entity_id=99, archetype=InformationProviderArchetype.ELDER)

    quest = QuestState(
        id="q1", kind=ProjectKind.QUEST, quest_kind=QuestKind.EXPLORE,
        quest_status=QuestStatus.ACTIVE, goal_value=0.0, current_value=0.0,
        reward=RewardState(), source_entity_id=99,
    )
    entity = (
        V2EntityBuilder(2)
        .kind("hero")
        .location(0, 0)
        .strategic(projects={"q1": quest})
        .build()
    )

    country_a = FactionState(faction_id="country_a", territory=("city_1", "city_2"))

    feature_flags = {"ENABLE_INFORMATION_HUB_ACCUMULATION": "ON"} if flag_on else {}

    return AuthoritativeState(
        tick=100, seed=1,
        entities={2: entity},
        information_providers={99: provider},
        factions={"country_a": country_a},
        recent_world_events=[
            WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=99, region_id="city_1", severity=1.0),
        ],
        feature_flags=feature_flags,
    )


def _drive_tick(state: AuthoritativeState) -> AuthoritativeState:
    update = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, quest=QuestUpdate(quest_id="q1"))})
    refined = AuthoritativeApplyPipeline.refine(state, update)
    return ApplyPath.apply_generation(state, refined, next_tick=101)


def test_information_hub_accumulation_flag_off_no_state_change():
    state = _scenario_state(flag_on=False)
    state_v2 = _drive_tick(state)

    assert state_v2.information_providers[99].to_canonical_dict() == state.information_providers[99].to_canonical_dict()
    before_events = [e for e in state.recent_world_events]
    after_events = [e for e in state_v2.recent_world_events]
    assert after_events == before_events


def test_information_hub_accumulation_flag_on_does_change_state():
    state = _scenario_state(flag_on=True)
    state_v2 = _drive_tick(state)

    assert state_v2.information_providers[99].knowledge_accumulated == 1
    assert any(
        e.category == WorldEventCategory.CRITICAL_INFORMATION_PROPAGATED
        for e in state_v2.recent_world_events
    )
