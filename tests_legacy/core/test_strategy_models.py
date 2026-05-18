import pytest
from src_legacy.core.models.strategy import StrategicState, DirectiveRecord, DirectiveKind, rebuild_strategic_models

def test_strategic_model_rebuild():
    """Verify pydantic model rebuild handles recursive refs."""
    rebuild_strategic_models()
    # If it didn't fail, basic structure is valid

def test_directive_creation():
    d = DirectiveRecord(
        directive_id="dir_1",
        kind=DirectiveKind.PERSONAL,
        label="Test Directive",
        priority=1.5
    )
    assert d.directive_id == "dir_1"
    assert d.priority == 1.5

def test_strategic_state_defaults():
    state = StrategicState()
    assert len(state.directives) == 0
    assert len(state.projects) == 0
    assert state.current_project_id is None
    assert state.last_strategic_tick == 0

def test_strategic_state_serialization():
    state = StrategicState()
    state.directives.append(DirectiveRecord(
        directive_id="dir_1",
        kind=DirectiveKind.PERSONAL,
        label="Test"
    ))
    
    data = state.model_dump()
    assert "directives" in data
    assert data["directives"][0]["directive_id"] == "dir_1"
    
    new_state = StrategicState(**data)
    assert new_state.directives[0].directive_id == "dir_1"
