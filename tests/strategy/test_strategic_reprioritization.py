import pytest
from src.core.state import (
    EntityState, IdentityComponent, AttributeComponent, 
    AuthoritativeState, PersonalityComponent, BiologicalComponent
)
from src.core.strategic import (
    StrategicComponent, CognitionProfile, ProjectState, 
    ProjectStatus, ObjectiveState, ObjectiveStatus
)
from src.systems.strategic import StrategicIntelligenceSystem

@pytest.fixture
def state():
    return AuthoritativeState(tick=100, seed=42)

@pytest.fixture
def entity():
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(1)
        .kind("hero")
        .at((0, 0))
        .attributes(intelligence=15, wisdom=15)
        .with_strategic_profile(resistance=0.5, max_projects=3)
        .with_personality(industry=0.5)
        .build())

def test_switch_from_harvesting_to_combat_on_high_threat(entity, state):
    from dataclasses import replace
    # Setup harvesting project
    current = ProjectState(
        id="proj_harvest", kind="harvesting", status=ProjectStatus.ACTIVE, score=30.0
    )
    new_strat = replace(entity.strategic, 
                        projects={"proj_harvest": current},
                        current_project_id="proj_harvest")
    entity = replace(entity, strategic=new_strat)
    
    # Candidate project B with higher score
    candidate = ProjectState(
        id="proj_combat", kind="combat", status=ProjectStatus.ACTIVE, score=80.0
    )
    
    # Resistance margin = 0.5 * 30 = 15.0
    # Effective current = 30 + 15 = 45.0
    # Candidate (80.0) > 45.0 -> Should switch
    update = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=state.tick)
    assert update is not None
    assert update.current_project_id_set == "proj_combat"

def test_boredom_accumulation_in_update(entity, state):
    from dataclasses import replace
    proj = ProjectState(
        id="proj_A", kind="harvesting", status=ProjectStatus.ACTIVE, score=50.0
    )
    new_strat = replace(entity.strategic, 
                        projects={"proj_A": proj},
                        current_project_id="proj_A")
    entity = replace(entity, strategic=new_strat)
    
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    assert "harvesting" in update.boredom_delta
    assert update.boredom_delta["harvesting"] == 0.1
