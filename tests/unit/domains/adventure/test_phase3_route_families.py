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
