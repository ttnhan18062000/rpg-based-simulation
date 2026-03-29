import pytest
from unittest.mock import MagicMock
from src.core.models.enums import HeroClass, AIState
from src.ai.goals.base import GoalScore, SkirmishModifier

def test_skirmish_boosts_move_for_ranged():
    modifier = SkirmishModifier()
    
    actor = MagicMock()
    actor.progression.hero_class = HeroClass.RANGER
    actor.mind.combat_target_id = 2
    actor.mind.memory = {2: MagicMock(x=1, y=1)} # Simplified pos
    actor.spatial.pos = MagicMock(x=0, y=0) # Adjacent
    actor.spatial.pos.manhattan.return_value = 1
    
    ctx = MagicMock(actor=actor)
    
    # Test Move goal
    score = GoalScore(goal="move", score=10.0, target_state=AIState.WANDER)
    modifier.modify(score, ctx)
    
    # 10.0 * 2.0 = 20.0
    assert score.score == 20.0

def test_skirmish_does_not_boost_melee():
    modifier = SkirmishModifier()
    
    actor = MagicMock()
    actor.progression.hero_class = HeroClass.WARRIOR
    actor.mind.combat_target_id = 2
    actor.mind.memory = {2: MagicMock()}
    actor.spatial.pos.manhattan.return_value = 1
    
    ctx = MagicMock(actor=actor)
    
    score = GoalScore(goal="move", score=10.0, target_state=AIState.WANDER)
    modifier.modify(score, ctx)
    
    assert score.score == 10.0
