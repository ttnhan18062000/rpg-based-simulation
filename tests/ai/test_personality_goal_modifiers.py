import pytest
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, PersonalityComponent, 
    LifeStage, StrategicComponent, BiologicalComponent, ResourceNodeState
)
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.builder import V2EntityBuilder
from src.core.strategic import ProjectState, ProjectStatus, StrategicComponent
from dataclasses import replace

@pytest.mark.v2_contract
def test_greedy_personality_bias():
    # Setup state with a harvesting node
    node = ResourceNodeState(id=1, kind="iron", position=(1,1), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5)
    
    # Greedy entity
    greedy_entity = (V2EntityBuilder(1)
        .at((0.0, 0.0))
        .personality(PersonalityComponent(greed=1.0))
        .build())
    
    # Non-greedy entity
    neutral_entity = (V2EntityBuilder(2)
        .at((0.0, 0.0))
        .personality(PersonalityComponent(greed=0.0))
        .build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: greedy_entity, 2: neutral_entity}, resource_nodes={1: node})
    
    # Evaluate greedy
    upd1 = StrategicIntelligenceSystem.evaluate_strategic_intent(state, greedy_entity, force=True)
    proj1 = upd1.projects_add_or_update[0]
    
    # Evaluate neutral
    upd2 = StrategicIntelligenceSystem.evaluate_strategic_intent(state, neutral_entity, force=True)
    proj2 = upd2.projects_add_or_update[0]
    
    # Greedy score should be higher (+50% per logic in personality.py)
    assert proj1.score > proj2.score
    assert proj1.score == pytest.approx(proj2.score * 1.5)

@pytest.mark.v2_contract
def test_boredom_accumulation_and_switch():
    # Setup state with two goals of similar utility
    # Node 1 is slightly closer
    node1 = ResourceNodeState(id=1, kind="iron", position=(1,1), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5)
    node2 = ResourceNodeState(id=2, kind="iron", position=(2,2), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5)
    
    # Initial state with active project
    entity = (V2EntityBuilder(1)
        .at((0.0, 0.0))
        .build())
    
    # Add project manually since builder doesn't support active project injection yet
    entity = replace(entity, strategic=replace(entity.strategic, 
        current_project_id="proj_harvesting",
        projects={
            "proj_harvesting": ProjectState(id="proj_harvesting", kind="harvesting", status=ProjectStatus.ACTIVE)
        }
    ))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, resource_nodes={1: node1, 2: node2})
    
    # 1. Initial evaluation (no boredom)
    upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    # It should increment boredom since there is an active project
    assert upd.boredom_delta.get("harvesting") == pytest.approx(0.1)
    
    # 2. Add high boredom
    bored_entity = replace(entity, strategic=replace(entity.strategic, boredom={"harvesting": 100.0}))
    upd_bored = StrategicIntelligenceSystem.evaluate_strategic_intent(state, bored_entity, force=True)
    
    # With 100 boredom, harvesting utility should be negative or below threshold
    if upd_bored.projects_add_or_update:
        proj = upd_bored.projects_add_or_update[0]
        assert proj.kind != "harvesting"
    else:
        assert True # Switching to None is also valid

@pytest.mark.v2_contract
def test_life_stage_multipliers():
    # Setup state
    entity_child = (V2EntityBuilder(1)
        .at((0.0, 0.0))
        .life_stage(LifeStage.CHILD)
        .biological(sleep_debt=50.0)
        .build())
        
    entity_elder = (V2EntityBuilder(2)
        .at((0.0, 0.0))
        .life_stage(LifeStage.ELDER)
        .biological(sleep_debt=50.0)
        .build())

    # Add an inn
    from src.core.state import BuildingState
    inn = BuildingState(id=10, kind="inn", position=(1,1))
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity_child, 2: entity_elder}, buildings={10: inn})
    
    # Evaluate fatigue goal
    upd_child = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity_child, force=True)
    upd_elder = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity_elder, force=True)
    
    score_child = upd_child.projects_add_or_update[0].score
    score_elder = upd_elder.projects_add_or_update[0].score
    
    # Elder multiplier is 1.5, Child is 0.8. Base utility is 50 + 30 (night) = 80.
    assert score_elder > score_child
    assert score_elder == pytest.approx(80.0 * 1.5)
    assert score_child == pytest.approx(80.0 * 0.8)
