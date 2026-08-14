import pytest
from src.ai.goals.base import GoalRegistry, GoalScorer, GoalScore
from src.core.strategic import GoalKind, ProjectKind
from src.core.state import EntityState, AuthoritativeState
from src.ai.goals.scorers import HarvestScorer, SleepScorer

def test_goal_registry_strict_validation():
    """Verify that GoalRegistry enforces that keys must be valid GoalKind members or values."""
    
    # 1. Registering the correct scorer for GoalKind should be a no-op and succeed
    GoalRegistry.register(GoalKind.HARVESTING, HarvestScorer())
    
    # 2. Registering with valid GoalKind string value for correct scorer should succeed
    GoalRegistry.register("fatigue", SleepScorer())

    # 3. Registering with an invalid string should fail with ValueError
    with pytest.raises(ValueError) as excinfo:
        GoalRegistry.register("invalid_goal_type", HarvestScorer())
    assert "Invalid goal kind" in str(excinfo.value)
    
    # 4. Registering with invalid types should fail with ValueError
    with pytest.raises(ValueError):
        GoalRegistry.register(12345, HarvestScorer())

def test_all_registered_scorers_are_canonical():
    """Verify that all currently registered scorers in GoalRegistry use valid GoalKind enums."""
    for kind in GoalRegistry._scorers.keys():
        assert isinstance(kind, GoalKind)
        # Ensure it maps perfectly to a defined value
        assert kind in GoalKind


# --- TCK-20260811-REGION-STABILIZATION-GOAL-SCORER: AC1 enum-drift guards --------------------


def test_project_kind_stabilize_is_registered_member():
    assert ProjectKind("stabilize") == ProjectKind.STABILIZE


def test_stabilize_kind_value_does_not_collide_with_existing_project_kind_or_goal_kind():
    for pk in ProjectKind:
        if pk == ProjectKind.STABILIZE:
            continue
        assert ProjectKind.STABILIZE.value != pk.value
    for gk in GoalKind:
        assert ProjectKind.STABILIZE.value != gk.value, (
            f"ProjectKind.STABILIZE.value must not collide with GoalKind.{gk.name} "
            f"({gk.value!r})."
        )


def test_region_stabilization_kind_value_does_not_collide_with_project_kind_or_existing_goal_kind():
    for pk in ProjectKind:
        assert GoalKind.REGION_STABILIZATION.value != pk.value, (
            f"GoalKind.REGION_STABILIZATION.value must not collide with ProjectKind.{pk.name} "
            f"({pk.value!r}) -- a collision would make intelligence.py's resume/dedup lookup "
            f"(`p.kind == best_candidate.kind`) accidentally match (Design Decision #4)."
        )
    for gk in GoalKind:
        if gk == GoalKind.REGION_STABILIZATION:
            continue
        assert GoalKind.REGION_STABILIZATION.value != gk.value


def test_region_stabilization_goal_kind_value_does_not_break_existing_tie_break_ordering():
    """Design Decision #3: GoalKind.REGION_STABILIZATION ("region_stabilization") must not
    change ADVENTURE_ROUTE's ("z_adventure_route") or SOCIAL_CONTRACT's ("social_contract")
    existing relative sort position against the 10 original members under
    intelligence.py's `sort(key=lambda x: (-x.utility, x.kind))` tie-break."""
    # Direct value-ordering assertions (the actual regression guard):
    assert GoalKind.REGION_STABILIZATION.value > GoalKind.RECOVER.value
    assert GoalKind.REGION_STABILIZATION.value < GoalKind.RESOLVE_BLOCKER.value
    assert GoalKind.REGION_STABILIZATION.value < GoalKind.SOCIAL.value
    assert GoalKind.REGION_STABILIZATION.value < GoalKind.SOCIAL_CONTRACT.value
    assert GoalKind.REGION_STABILIZATION.value < GoalKind.TOWN_RETURN.value
    assert GoalKind.REGION_STABILIZATION.value < GoalKind.ADVENTURE_ROUTE.value
