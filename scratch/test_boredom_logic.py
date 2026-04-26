import pytest
from src.core.state import AuthoritativeState, EntityState, StrategicComponent
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_boredom_decay():
    entity = EntityState(
        id=1, kind="hero", position=(0,0),
        strategic=StrategicComponent(boredom={"harvesting": 1.0, "social": 0.04})
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # Apply one tick (decay is 0.05)
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    new_entity = new_state.entities[1]
    
    # Harvesting: 1.0 - 0.05 = 0.95
    assert new_entity.strategic.boredom["harvesting"] == pytest.approx(0.95)
    # Social: 0.04 - 0.05 = -0.01 -> should be removed (below 0.001)
    assert "social" not in new_entity.strategic.boredom

@pytest.mark.v2_contract
def test_boredom_delta_application():
    entity = EntityState(
        id=1, kind="hero", position=(0,0),
        strategic=StrategicComponent(boredom={"harvesting": 1.0})
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # Update with delta
    from src.core.updates import EntityUpdate, StrategicUpdate
    ent_upd = EntityUpdate(entity_id=1, strategic=StrategicUpdate(boredom_delta={"harvesting": 0.5, "social": 0.2}))
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    # Apply generation (decay 1.0 -> 0.95 then delta 0.95 + 0.5 = 1.45)
    gen_state = ApplyPath.apply_generation(state, state_upd)
    
    # Check final state
    assert gen_state.entities[1].strategic.boredom["harvesting"] == pytest.approx(1.45)
    assert gen_state.entities[1].strategic.boredom["social"] == pytest.approx(0.2)
    assert gen_state.entities[1].strategic.boredom["harvesting"] == pytest.approx(1.45)
    assert gen_state.entities[1].strategic.boredom["social"] == pytest.approx(0.2)
