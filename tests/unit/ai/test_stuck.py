import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain
from src.core.models.vectors import Vector2
from src.core.models.enums import AIState, EmotionType
from src.actions.base import NavigationUpdate, MindUpdate
from src.core.aspects.mind import MindAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.progression import ProgressionAspect

def test_perception_tracks_position_history():
    config = MagicMock()
    config.flee_hp_threshold = 0.2
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = MagicMock()
    actor.id = 1
    actor.spatial.pos = Vector2(1, 1)
    actor.spatial.vision_range = 10
    actor.identity.faction = "player"
    actor.mind.perception.max_attention_slots = 5
    actor.mind.navigation.pos_history = []
    actor.progression.age_ticks = 0
    actor.progression.longevity_limit = 100

    # Set up hostile check
    brain._faction_reg = MagicMock()
    brain._faction_reg.is_hostile.return_value = False
    
    updates = []
    # Mock snapshot
    snapshot = MagicMock(tick=100)
    
    with patch('src.ai.brain.Perception.visible_entities', return_value=[]):
        brain._sensory_perception_phase(actor, snapshot, updates)
        
        # Check NavigationUpdate in updates list
        nav_up = next((u for u in updates if isinstance(u, NavigationUpdate)), None)
        assert nav_up is not None
        assert len(nav_up.pos_history) == 1
        assert nav_up.pos_history[0] == Vector2(1, 1)

def test_appraisal_detects_stuck():
    config = MagicMock()
    config.flee_hp_threshold = 0.2
    rng = MagicMock()
    brain = AIBrain(config, rng)
    brain._faction_reg = MagicMock()
    
    actor = MagicMock()
    actor.id = 1
    
    # 5 identical positions to trigger stuck detection
    p = Vector2(1, 1)
    actor.spatial.pos = p
    actor.spatial.current_region_id = None
    
    # Real aspects to support comparison logic
    actor.mind = MindAspect()
    actor.mind.navigation.pos_history = [p, p, p, p, p]
    actor.mind.emotion.mood = 0.5
    
    actor.combat = CombatAspect(hp=100, max_hp=100)
    actor.progression = ProgressionAspect(age_ticks=0, longevity_limit=10000)
    
    ctx = MagicMock(actor=actor, snapshot=MagicMock(tick=100), visible=[])
    ctx.config.flee_hp_threshold = 0.2
    updates = []
    
    brain._memory_appraisal_phase(ctx, updates)
    
    # Check MindUpdate for STUCK emotion
    mind_up = next((u for u in updates if isinstance(u, MindUpdate) and u.emotion_set), None)
    assert mind_up is not None
    assert mind_up.emotion_set.get(EmotionType.STUCK, 0.0) > 0.0
