"""
tests/unit/domains/adventure/test_phase3_route_families.py

Phase 3 — Route Family Vocabulary unit tests.
Verifies uniqueness, mapping rules, and validation of the route vocabulary.
"""

import pytest
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption
from src.domains.adventure.mapper import RouteToProjectMapper


def test_route_family_definitions_are_unique():
    """Verify all RouteFamily enum values are unique strings."""
    values = [e.value for e in RouteFamily]
    assert len(values) == len(set(values))
    assert len(values) == 16  # updated: PROTECT_TARGET + OWN_SURVIVAL added (E41D)


def test_route_family_has_project_mapping():
    """Verify that every defined RouteFamily successfully maps to project kinds."""
    for family in RouteFamily:
        project_kind, obj_kind = RouteToProjectMapper.get_kinds(family)
        if family == RouteFamily.DEFER_WITH_REASON:
            assert project_kind is None
            assert obj_kind is None
        else:
            assert project_kind is not None
            assert obj_kind is not None


def test_route_family_has_required_trace_metadata():
    """Verify that creating an AdventureRouteOption stores expected metadata."""
    option = AdventureRouteOption(
        family=RouteFamily.CRAFT_UPGRADE,
        score=0.8,
        confidence=0.9,
        expected_benefit=0.95,
        expected_risk=0.1,
        reason="Has recipe and materials"
    )
    assert option.family == RouteFamily.CRAFT_UPGRADE
    assert option.score == 0.8
    assert option.confidence == 0.9
    assert option.expected_benefit == 0.95
    assert option.expected_risk == 0.1
    assert option.reason == "Has recipe and materials"


def test_unknown_route_family_fails_fast():
    """Verify mapping an invalid/unknown route family raises ValueError."""
    with pytest.raises(ValueError):
        RouteToProjectMapper.get_kinds("invalid_family")


def test_map_to_states_carries_real_score_not_hardcoded_placeholder():
    """TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION Step 2: map_to_states() must carry
    the real AdventureRouteOption.score through to ProjectState.score, not the historical
    hardcoded 1.0 placeholder -- a prerequisite for evaluate_project_switch()'s normalized
    lock-bypass comparison (AC2) to mean anything real."""
    project, objective = RouteToProjectMapper.map_to_states(
        family=RouteFamily.TAKE_EASY_QUEST,
        entity_id=1,
        tick=10,
        score=2.3,
    )
    assert project.score == 2.3

    # Other fields must be unaffected by the score fix (anti-drift guard).
    assert project.id == f"proj.{RouteFamily.TAKE_EASY_QUEST.value}.ent1.t10"
    assert project.kind is not None
    assert project.lock_until_tick == min(10 + 10, 10 + 50)
    assert len(project.objectives) == 1
    assert project.active_objective_id == objective.id

    # Default (no score passed) preserves today's 1.0 behavior for any caller that omits it.
    default_project, _ = RouteToProjectMapper.map_to_states(
        family=RouteFamily.TAKE_EASY_QUEST, entity_id=1, tick=10,
    )
    assert default_project.score == 1.0


def test_adventure_decision_service_carries_selected_score_into_proposed_project():
    """End-to-end proof (through the real caller, not just the mapper in isolation) that
    AdventureDecisionService.decide()'s proposed_project.score matches selected.score exactly
    for a scored candidate."""
    from src.core.builder import V2EntityBuilder
    from src.domains.adventure.schema import AdventureRouteOption
    from src.domains.adventure.service import AdventureDecisionService

    hero = V2EntityBuilder(1).kind("hero").build()
    candidate = AdventureRouteOption(
        family=RouteFamily.TAKE_EASY_QUEST,
        score=0.0,
        confidence=1.0,
        expected_benefit=2.0,
        expected_risk=0.0,
    )
    result = AdventureDecisionService.decide(hero, [candidate], tick=5)

    assert result.selected is not None
    assert result.proposed_project is not None
    assert result.proposed_project.score == result.selected.score
