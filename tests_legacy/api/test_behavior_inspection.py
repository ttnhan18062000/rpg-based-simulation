import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from src_legacy.api.presenters.ai_presenter import AIPresenter
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.aspects.mind import BeliefRecord, ThreatEstimate, DecisionDriver, DecisionState
from src_legacy.core.models.vectors import Vector2

@pytest.fixture
def rng():
    return DeterministicRNG(42)

def test_ai_presenter_maps_structured_drivers(rng):
    # 1. Create a hero with structured drivers
    hero = EntityBuilder(rng, 1).kind("hero").build()
    
    # Manually populate driver_details (bypassing brain for isolation)
    hero.mind.decision.driver_details = [
        DecisionDriver(kind="personality", label="Greed", weight=1.5),
        DecisionDriver(kind="emotion", label="Panic", weight=2.0),
        DecisionDriver(kind="belief", label="Sensed danger", weight=1.2)
    ]
    
    explanation = AIPresenter.get_explanation(hero)
    
    # 2. Verify mapping to schema
    assert hasattr(explanation, "driver_details")
    assert len(explanation.driver_details) == 3
    
    greed_driver = next((d for d in explanation.driver_details if d.label == "Greed"), None)
    assert greed_driver is not None
    assert greed_driver.kind == "personality"
    assert greed_driver.weight == 1.5
    
    panic_driver = next((d for d in explanation.driver_details if d.label == "Panic"), None)
    assert panic_driver.weight == 2.0

def test_api_belief_inspection_includes_apparent_state(rng):
    hero = EntityBuilder(rng, 1).kind("hero").build()
    
    # Add a rich belief
    hero.mind.perception.entity_memory[2] = BeliefRecord(
        entity_id=2, 
        pos=Vector2(0,0),
        apparent_faction="mob",
        apparent_role="BOSS",
        apparent_class="WARRIOR",
        visible_injury=0.3,
        threat=ThreatEstimate(overall=0.9),
        confidence=1.0
    )
    
    explanation = AIPresenter.get_explanation(hero)
    
    # Verify belief fields
    assert len(explanation.beliefs) == 1
    belief_data = explanation.beliefs[0]
    
    assert belief_data["apparent_faction"] == "mob"
    assert belief_data["apparent_role"] == "BOSS"
    assert belief_data["apparent_class"] == "WARRIOR"
    assert belief_data["visible_injury"] == 0.3

def test_injury_blurring_in_api_response(rng):
    hero = EntityBuilder(rng, 1).kind("hero").build()
    
    # 1. High confidence (visible)
    hero.mind.perception.entity_memory[2] = BeliefRecord(
        entity_id=2, pos=Vector2(0,0), visible_injury=0.3, confidence=0.8
    )
    explanation = AIPresenter.get_explanation(hero)
    assert explanation.beliefs[0]["visible_injury"] == 0.3
    
    # 2. Low confidence (blurred)
    hero.mind.perception.entity_memory[2].confidence = 0.4
    explanation = AIPresenter.get_explanation(hero)
    assert explanation.beliefs[0]["visible_injury"] == -1.0 # Unknown/Blurred
