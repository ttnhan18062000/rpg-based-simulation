import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock, patch
from src.ai.goals.base import GoalScore, GoalEvaluator
from src.core.models.enums import AIState

def test_emotional_modifier_panic_boosts_flee():
    from src.ai.goals.base import EmotionalModifier
    
    # Setup: High Panic
    ctx = MagicMock()
    ctx.actor.mind.emotional_state = {"panic": 0.8}
    
    modifier = EmotionalModifier()
    
    # Base flee score
    gs_flee = GoalScore("flee", 1.0, AIState.FLEE)
    modifier.modify(gs_flee, ctx)
    
    # Panic should boost flee significantly
    assert gs_flee.score > 1.5
    
    # Panic should reduce combat
    gs_combat = GoalScore("combat", 1.0, AIState.HUNT)
    modifier.modify(gs_combat, ctx)
    assert gs_combat.score < 1.0

def test_appraisal_phase_triggers_panic_on_low_hp():
    from src.ai.brain import AIBrain
    config = MagicMock()
    config.flee_hp_threshold = 0.3
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    # Setup actor mock with necessary components
    actor = MagicMock()
    actor.stats.combat.hp_ratio = 0.2  # Set as value, not MagicMock comparison
    actor.mind.emotional_state = {"panic": 0.0}
    actor.mind.memory_locations = {}
    actor.mind.region_fatigue = {}
    actor.mind.spatial.pos_history = []
    actor.stats.spatial.vision_range = 10
    actor.progression.age_ticks = 0
    actor.progression.longevity_limit = 100
    
    ctx = MagicMock(actor=actor)
    # Patch Perception to avoid deep calls
    with patch('src.ai.brain.Perception.visible_entities', return_value=[]):
        brain._memory_appraisal_phase(ctx)
        
        # Should have some panic now
        assert actor.mind.emotional_state["panic"] > 0.0
