import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.engine.cognition import AppraisalSystem
from src.ai.goals.scorers import TownScorer
from src.systems.strategic import StrategicIntelligenceSystem

def test_near_death_panic_progression():
    """Verify that panic levels scale smoothly and predictably as HP decreases."""
    
    # 1. Healthy / Low Panic (HP = 80%)
    ent_healthy = (V2EntityBuilder(1)
        .kind("HERO")
        .combat(hp=80, max_hp=100)
        .build())
    profile_healthy = AppraisalSystem.evaluate_emotional_state(ent_healthy, [])
    assert profile_healthy.panic_level == 0.0
    assert not profile_healthy.is_fleeing

    # 2. HP = 35% (< 40%) -> Panic should spike slightly (+0.2)
    ent_35 = (V2EntityBuilder(1)
        .kind("HERO")
        .combat(hp=35, max_hp=100)
        .build())
    profile_35 = AppraisalSystem.evaluate_emotional_state(ent_35, [])
    assert profile_35.panic_level == pytest.approx(0.2)
    assert not profile_35.is_fleeing

    # 3. HP = 15% (< 20%) -> Panic should increase further (+0.5)
    ent_15 = (V2EntityBuilder(1)
        .kind("HERO")
        .combat(hp=15, max_hp=100)
        .build())
    profile_15 = AppraisalSystem.evaluate_emotional_state(ent_15, [])
    assert profile_15.panic_level == pytest.approx(0.5)
    assert profile_15.is_fleeing  # Panic 0.5 > 0.4 threshold triggers fleeing

    # 4. HP = 5% (< 10%) -> Panic should spike to the maximum (+0.8)
    ent_5 = (V2EntityBuilder(1)
        .kind("HERO")
        .combat(hp=5, max_hp=100)
        .build())
    profile_5 = AppraisalSystem.evaluate_emotional_state(ent_5, [])
    assert profile_5.panic_level == pytest.approx(0.8)
    assert profile_5.is_fleeing

    # Ensure panic progression is strictly monotonic
    assert profile_5.panic_level > profile_15.panic_level
    assert profile_15.panic_level > profile_35.panic_level
    assert profile_35.panic_level > profile_healthy.panic_level


def test_town_scorer_bridge():
    """Verify that TownScorer returns a valid target_id and successfully creates a strategic project."""
    
    # 1. Setup extremely high fatigue & hunger to guarantee town_return project choice
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .location(5.0, 5.0)
        .biological(sleep_debt=95.0, hunger=95.0)
        .build())
        
    region = RegionState(id="forest", name="Deep Forest", bounds=(0, 0, 10, 10))
    state = AuthoritativeState(
        tick=100, 
        seed=42, 
        entities={1: ent}, 
        world_time=1200, 
        regions={"forest": region}
    )
    
    # 2. Verify Scorer returns correct target details
    scorer = TownScorer()
    score = scorer.score(ent, state)
    
    assert score.kind == "town_return"
    assert score.target_id == "town_center"
    assert score.target_pos == state.town_center
    assert score.utility > 50.0  # Should be very high under extreme biological pressure

    # 3. Verify Strategic Intent Evaluation builds the project
    strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, ent, force=True)
    
    assert strat_up.current_project_id_set is not None
    assert "town_return" in strat_up.current_project_id_set
    
    # The new active project must be added to the updates list
    added_projects = strat_up.projects_add_or_update
    assert len(added_projects) > 0
    
    town_proj = next((p for p in added_projects if p.kind == "town_return"), None)
    assert town_proj is not None
    assert town_proj.active_objective_id is not None
    
    # The active objective should match reach_location
    active_obj = town_proj.objectives[0]
    assert active_obj.kind == "reach_location"
    assert active_obj.target == "town_center"
    assert active_obj.target_position == state.town_center
