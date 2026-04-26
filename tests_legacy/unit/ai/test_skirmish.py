import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock
from src_legacy.core.models.enums import HeroClass, AIState, GoalType
from src_legacy.ai.goals.base import GoalScore, SkirmishModifier
from src_legacy.core.models.vectors import Vector2

def test_skirmish_boosts_move_for_ranged():
    modifier = SkirmishModifier()
    
    actor = MagicMock()
    actor.progression.hero_class = HeroClass.RANGER
    actor.combat.combat_target_id = 2
    
    # MemoryRecord mock
    mem = MagicMock()
    mem.pos = Vector2(1, 1)
    actor.mind.perception.entity_memory = {2: mem}
    
    actor.spatial.pos = Vector2(0, 0)
    
    ctx = MagicMock(actor=actor)
    
    # Test Explore goal (used as proxy for move in skirmish modifier)
    score = GoalScore(goal=GoalType.EXPLORE, score=10.0, target_state=AIState.WANDER)
    modifier.modify(score, ctx)
    
    # 10.0 * 2.0 = 20.0 (since dist is sqrt(1^2 + 1^2) approx 1.4, which is <= 3)
    # Manhattan dist is 1+1=2, which is <= 3.
    assert score.score == 20.0

def test_skirmish_does_not_boost_melee():
    modifier = SkirmishModifier()
    
    actor = MagicMock()
    actor.progression.hero_class = HeroClass.WARRIOR
    actor.combat.combat_target_id = 2
    
    mem = MagicMock()
    mem.pos = Vector2(1, 1)
    actor.mind.perception.entity_memory = {2: mem}
    
    actor.spatial.pos = Vector2(0, 0)
    
    ctx = MagicMock(actor=actor)
    
    score = GoalScore(goal=GoalType.EXPLORE, score=10.0, target_state=AIState.WANDER)
    modifier.modify(score, ctx)
    
    assert score.score == 10.0
