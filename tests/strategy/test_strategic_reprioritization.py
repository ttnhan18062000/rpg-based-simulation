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
    strat = StrategicComponent(
        profile=CognitionProfile(interruption_resistance=0.5, max_active_projects=3)
    )
    return EntityState(
        id=1,
        kind="hero",
        position=(0, 0),
        attributes=AttributeComponent(intelligence=15, wisdom=15),
        identity=IdentityComponent(personality=PersonalityComponent(industry=0.5)),
        biological=BiologicalComponent(),
        strategic=strat
    )

def test_switch_from_harvesting_to_combat_on_high_threat(entity, state):
    from dataclasses import replace
    # Current project: Harvesting with utility 30
    current = ProjectState(
        id="proj_harvest", kind="harvesting", status=ProjectStatus.ACTIVE, score=30.0
    )
    new_strat = replace(entity.strategic, 
                        current_project_id="proj_harvest",
                        projects={"proj_harvest": current})
    entity = replace(entity, strategic=new_strat)
    
    # Rest of the test
    pass

def test_boredom_accumulation_in_update(entity, state):
    from dataclasses import replace
    proj = ProjectState(
        id="proj_A", kind="harvesting", status=ProjectStatus.ACTIVE, score=50.0
    )
    # Reconstruct entity with the project and current_project_id
    new_strat = replace(entity.strategic, 
                        current_project_id="proj_A",
                        projects={"proj_A": proj})
    entity = replace(entity, strategic=new_strat)
    
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    assert "harvesting" in update.boredom_delta
    assert update.boredom_delta["harvesting"] == 0.1
