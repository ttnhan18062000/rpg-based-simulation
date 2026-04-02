import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain
from src.core.models import Vector2
from src.core.models.enums import AIState

def test_perception_tracks_position_history():
    config = MagicMock()
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = MagicMock()
    actor.id = 1
    actor.spatial.spatial.pos = Vector2(1, 1)
    actor.identity.identity.faction = "player"
    actor.stats.spatial.vision_range = 10
    actor.mind.max_attention_slots = 5
    actor.mind.pos_history = []
    actor.progression.age_ticks = 0
    actor.progression.longevity_limit = 100

    # Set up hostile check - mock is_hostile as a function, not an attribute access
    # Since FactionRegistry has __slots__, we must be careful with how we mock its methods
    brain._faction_reg = MagicMock()
    brain._faction_reg.is_hostile.return_value = False
    
    ctx = MagicMock(actor=actor)
    # Mock snapshot.tick for rng inside
    snapshot = MagicMock(tick=100)
    
    with patch('src.ai.brain.Perception.visible_entities', return_value=[]):
        brain._sensory_perception_phase(actor, snapshot)
        assert len(actor.mind.pos_history) == 1
        assert actor.mind.pos_history[0] == Vector2(1, 1)

def test_appraisal_detects_stuck():
    config = MagicMock()
    rng = MagicMock()
    brain = AIBrain(config, rng)
    brain._faction_reg = MagicMock()
    
    actor = MagicMock()
    actor.stats.combat.hp_ratio = 1.0
    # 5 identical positions to trigger stuck detection
    p = Vector2(1, 1)
    actor.mind.pos_history = [p, p, p, p, p]
    actor.mind.emotional_state = {}
    actor.mind.memory_locations = {}
    actor.mind.region_fatigue = {}
    actor.progression.age_ticks = 0
    actor.progression.longevity_limit = 10000
    
    ctx = MagicMock(actor=actor)
    with patch('src.ai.brain.Perception.visible_entities', return_value=[]):
        brain._memory_appraisal_phase(ctx)
        
        # Should have 'stuck' emotion or flag
        assert actor.mind.emotional_state.get("stuck", 0.0) > 0.0
