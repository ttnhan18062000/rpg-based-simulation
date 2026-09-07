"""Tests for ApplyPath.apply_generation()'s episode-scoped bridge carry-forward
(TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD)."""

from dataclasses import replace as dc_replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.domains.culture.model import CultureState
from src.domains.fame.legend import LegendFact
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
