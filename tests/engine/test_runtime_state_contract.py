from src.core.state import AuthoritativeState, EntityState
from src.core.export import to_export_state, StateDTO


def test_hotpath_purity():
    """Verify that state.py does not import from export or diagnostic modules."""
    import pathlib
    
    state_file = pathlib.Path("src/core/state.py")
    content = state_file.read_text()
    
    assert "src.core.export" not in content
    assert "src.core.diagnostic" not in content
    assert "pydantic" not in content.lower()


def test_export_factory_isolation():
    """Verify that to_export_state produces a valid DTO without mutating source."""
    state = AuthoritativeState(tick=1, seed=42, world_time=10, entities={
        1: EntityState(id=1, kind="hero", position=(0,0))
    })
    
    dto = to_export_state(state)
    
    # Check DTO structure
    assert isinstance(dto, StateDTO)
    assert dto.tick == 1
    assert len(dto.entities) == 1
    assert dto.entities[0].id == 1
    assert dto.entities[0].position_x == 0.0
    
    # Verify source purity
    assert state.tick == 1
    assert state.entities[1].position == (0,0)
    # Check that DTO didn't just copy the reference of the dict
    assert dto.entities[0].props is not state.entities[1].properties
