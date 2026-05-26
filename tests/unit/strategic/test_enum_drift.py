import pytest
from src.ai.goals.base import GoalRegistry, GoalScorer, GoalScore
from src.core.strategic import GoalKind
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
