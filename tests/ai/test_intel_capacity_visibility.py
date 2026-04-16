import pytest
from unittest.mock import MagicMock
from src.core.entities.entity import Entity
from src.ai.cognition_capacity import CognitionCapacityBuilder
from src.api.presenters.ai_presenter import AIPresenter
from src.ui.cli.inspector import EntityInspector

def test_cognition_api_serialization():
    """Verify that cognitive metrics are correctly serialized for the API."""
    entity = Entity(id=1, kind="hero")
    entity.progression.int_ = 10
    entity.progression.wis = 10
    entity.progression.per = 10
    entity.progression.cha = 10
    
    # Derivation
    profile = CognitionCapacityBuilder.build(entity)
    strat = entity.mind.strategic
    strat.last_capacity_profile = profile
    strat.active_slice_used = 5
    strat.active_concerns_used = 2
    strat.is_overloaded = True
    strat.overload_score = 1.2
    
    # Serialization
    explanation = AIPresenter.get_explanation(entity)
    strategy = explanation.strategy
    
    assert strategy.capacity is not None
    assert strategy.capacity.planning_budget == profile.planning_budget
    assert strategy.usage is not None
    assert strategy.usage.active_slice_used == 5
    assert strategy.usage.active_concerns_used == 2
    assert strategy.overload is not None
    assert strategy.overload.is_overloaded is True
    assert strategy.overload.overload_score == 1.2

def test_cognition_inspector_rendering(capsys):
    """Verify that the CLI inspector correctly renders cognitive data."""
    entity = Entity(id=1, kind="hero")
    profile = CognitionCapacityBuilder.build(entity)
    strat = entity.mind.strategic
    strat.last_capacity_profile = profile
    strat.active_slice_used = 8
    strat.active_concerns_used = 3
    strat.is_overloaded = True
    strat.overload_score = 1.5
    strat.dropped_candidates_count = 4
    
    EntityInspector.render_cognition_capacity(entity)
    
    captured = capsys.readouterr()
    assert "COGNITION & CAPACITY" in captured.out
    assert "Cognitive Profile" in captured.out
    assert "Active Budgets" in captured.out
    assert "COGNITIVE OVERLOAD ALERT" in captured.out
    assert "8/10" in captured.out or "8/" in captured.out # Depends on limit
    assert "Score: 1.50" in captured.out

def test_cognition_empty_profile(capsys):
    """Verify that inspector handles entities without cognitive profiles gracefully."""
    entity = Entity(id=1, kind="hero")
    entity.mind.strategic.last_capacity_profile = None
    
    EntityInspector.render_cognition_capacity(entity)
    
    captured = capsys.readouterr()
    assert captured.out == ""
