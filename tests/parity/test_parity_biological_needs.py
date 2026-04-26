import pytest
from src.core.state import AuthoritativeState, EntityState, BiologicalComponent, CombatComponent, StrategicComponent, BuildingState
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
from src.engine.apply import ApplyPath
from src.systems.strategic import StrategicIntelligenceSystem
from src.engine.domain_logic import SimulationDomainLogic

@pytest.mark.v2_contract
def test_biological_debt_accumulation():
    # Setup state
    bio = BiologicalComponent(hunger=10.0, sleep_debt=5.0)
    entity = EntityState(id=1, kind="hero", position=(0,0), biological=bio)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # Apply one tick
    next_state = ApplyPath.apply_generation(state, StateUpdate())
    
    # Check debt increased (Hunger +0.1, Sleep +0.05)
    new_bio = next_state.entities[1].biological
    assert new_bio.hunger == pytest.approx(10.1)
    assert new_bio.sleep_debt == pytest.approx(5.05)

@pytest.mark.v2_contract
def test_biological_goal_triggering():
    # Setup state with high fatigue
    bio = BiologicalComponent(sleep_debt=70.0)
    entity = EntityState(
        id=1, 
        kind="hero", 
        position=(0,0), 
        biological=bio,
        strategic=StrategicComponent()
    )
    # Add an inn building
    inn = BuildingState(id=10, kind="inn", position=(5,5))
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, buildings={10: inn})
    
    # Evaluate strategic intent
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    # Should propose a fatigue project
    assert update.current_project_id_set is not None
    proj = update.projects_add_or_update[0]
    assert proj.kind == "fatigue"
    assert proj.active_objective_id is not None
    assert "10" in proj.active_objective_id

@pytest.mark.v2_contract
def test_biological_recovery_at_building():
    # Setup state at an inn with REST task
    from src.core.state import TaskComponent
    bio = BiologicalComponent(sleep_debt=50.0)
    entity = EntityState(
        id=1, 
        kind="hero", 
        position=(5,5), 
        biological=bio,
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "REST"})
    )
    inn = BuildingState(id=10, kind="inn", position=(5,5))
    state = AuthoritativeState(
        tick=1, 
        seed=42, 
        entities={1: entity}, 
        buildings={10: inn},
        building_tiles={(5,5): "inn"},
        town_tiles={(5,5)}
    )
    
    # Resolve town (this should apply recovery)
    from src.engine.town_resolution import TownResolutionSystem
    from src.core.updates import TaskUpdate
    state_upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "REST"}))})
    resolved_upd = TownResolutionSystem.resolve(state, state_upd)
    
    # Apply the resolved update
    final_state = ApplyPath.apply_generation(state, resolved_upd)
    
    # Check sleep debt decreased (-5.0, but +0.05 passive)
    # Final = 50.0 - 5.0 + 0.05 = 45.05
    new_bio = final_state.entities[1].biological
    assert new_bio.sleep_debt == pytest.approx(45.05)
