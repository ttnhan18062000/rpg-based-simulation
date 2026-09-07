"""Tests for ApplyPath.apply_generation()'s episode-scoped bridge carry-forward
(TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD) and the persistent
information_source_profiles catalog reclassification
(TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION)."""

from dataclasses import replace as dc_replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.domains.culture.model import CultureState
from src.domains.fame.legend import LegendFact
from src.domains.information.schema import InformationSourceProfile
from src.engine.apply import ApplyPath


def _state_with_bridges() -> AuthoritativeState:
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})
    return dc_replace(
        state,
        region_loyalty_pressure={"r1": 0.5},
        region_culture_states={"r1": CultureState(fatalism=0.8)},
        entity_legend_facts={"1": LegendFact(subject_id="1", fame=0.9)},
    )


_PROFILE = InformationSourceProfile(
    source_id="town_notice_board",
    source_kind="guide",
    knowledge_scopes=("common_resource_sources",),
    accuracy=0.4,
    freshness=0.6,
)


def _state_with_source_profiles() -> AuthoritativeState:
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})
    return dc_replace(state, information_source_profiles=[_PROFILE])


def test_region_loyalty_pressure_survives_apply_generation():
    state = _state_with_bridges()
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.region_loyalty_pressure == {"r1": 0.5}


def test_region_culture_states_survives_apply_generation():
    state = _state_with_bridges()
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.region_culture_states == {"r1": CultureState(fatalism=0.8)}


def test_entity_legend_facts_survives_apply_generation():
    state = _state_with_bridges()
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.entity_legend_facts == {"1": LegendFact(subject_id="1", fame=0.9)}


def test_bridges_survive_multiple_generations():
    state = _state_with_bridges()
    for _ in range(3):
        state = ApplyPath.apply_generation(state, StateUpdate())
    assert state.region_loyalty_pressure == {"r1": 0.5}
    assert state.region_culture_states == {"r1": CultureState(fatalism=0.8)}
    assert state.entity_legend_facts == {"1": LegendFact(subject_id="1", fame=0.9)}


def test_default_empty_bridges_stay_empty_no_regression():
    """A state with no bridge content (the common case for most worlds/scenarios) must not
    spontaneously gain bridge content from this carry-forward change."""
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.region_loyalty_pressure == {}
    assert new_state.region_culture_states == {}
    assert new_state.entity_legend_facts == {}


def test_information_source_profiles_survives_apply_generation():
    state = _state_with_source_profiles()
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.information_source_profiles == [_PROFILE]


def test_information_source_profiles_survives_multiple_generations():
    state = _state_with_source_profiles()
    for _ in range(3):
        state = ApplyPath.apply_generation(state, StateUpdate())
    assert state.information_source_profiles == [_PROFILE]


def test_pending_information_responses_still_not_carried_forward():
    """Sibling field must stay Bounded/single-fire — this ticket only reclassifies
    information_source_profiles, not pending_information_responses (see
    docs/guidelines/intentional_divergences.md §2.23 and INFRA-257)."""
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})
    state = dc_replace(state, pending_information_responses=[{"actor_id": 1, "subject": "x"}])
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.pending_information_responses == []


def test_default_empty_source_profiles_stay_empty_no_regression():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.information_source_profiles == []
