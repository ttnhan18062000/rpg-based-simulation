import pytest
from src.core.state import (
    EntityState, IdentityComponent, AttributeComponent, 
    AuthoritativeState, PersonalityComponent
)
from src.core.strategic import (
    StrategicComponent, CognitionProfile, ProjectState, 
    ProjectStatus, ObjectiveState, ObjectiveStatus
)
from src.systems.strategic import StrategicIntelligenceSystem

def create_mock_state(tick: int = 0):
    return AuthoritativeState(tick=tick, seed=42)

def create_mock_entity(
    intelligence: int = 10, 
    wisdom: int = 10, 
    resistance: float = 0.5,
    current_proj_id: str = None
):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .attributes(intelligence=intelligence, wisdom=wisdom)
        .cognition(resistance=resistance)
        .current_project(current_proj_id)
        .with_personality(industry=0.5)
        .build())

def test_interruption_resistance_margin():
    entity = create_mock_entity(resistance=0.8, current_proj_id="proj_A")
    # Add current project to strat
    current = ProjectState(
        id="proj_A", kind="harvesting", status=ProjectStatus.ACTIVE, score=50.0
    )
    entity.strategic.projects["proj_A"] = current
    
    # Candidate project B with slightly higher score
    candidate = ProjectState(
        id="proj_B", kind="combat", status=ProjectStatus.ACTIVE, score=60.0
    )
    
    # Retention margin is resistance * 30 = 0.8 * 30 = 24.0
    # Effective current score = 50 + 24 = 74.0
    # Candidate (60.0) < 74.0 -> Should NOT switch
    up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=100)
    assert up is None
    
    # Candidate project C with MUCH higher score
    candidate_c = ProjectState(
        id="proj_C", kind="combat", status=ProjectStatus.ACTIVE, score=80.0
    )
    # 80.0 > 74.0 -> Should switch
    up_c = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_c, current_tick=100)
    assert up_c is not None
    assert up_c.current_project_id_set == "proj_C"

def test_project_lock():
    entity = create_mock_entity(resistance=0.1, current_proj_id="proj_A")
    # Locked until tick 200
    current = ProjectState(
        id="proj_A", kind="harvesting", status=ProjectStatus.ACTIVE, 
        score=10.0, lock_until_tick=200
    )
    entity.strategic.projects["proj_A"] = current
    
    # Very high utility candidate
    candidate = ProjectState(
        id="proj_B", kind="combat", status=ProjectStatus.ACTIVE, score=100.0
    )
    
    # At tick 100, lock is active
    up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=100)
    assert up is None
    
    # At tick 201, lock is expired
    up_expired = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=201)
    assert up_expired is not None
    assert up_expired.current_project_id_set == "proj_B"

def test_resume_suspended_project():
    entity = create_mock_entity(current_proj_id=None)
    suspended = ProjectState(
        id="proj_S", kind="exploration", status=ProjectStatus.SUSPENDED, 
        score=40.0, active_objective_id="obj_1"
    )
    entity.strategic.projects["proj_S"] = suspended
    
    up = StrategicIntelligenceSystem.resume_project(entity, "proj_S")
    assert up is not None
    assert up.current_project_id_set == "proj_S"
    assert up.current_objective_id_set == "obj_1"
    assert up.projects_add_or_update[0].status == ProjectStatus.ACTIVE
