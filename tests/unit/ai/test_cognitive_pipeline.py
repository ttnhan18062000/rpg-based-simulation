import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain
from src.core.models.enums import AIState, ActionType, GoalType
from src.actions.base import ActionProposal, MindUpdate
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2

@pytest.fixture
def mock_brain():
    config_mock = MagicMock()
    config_mock.flee_hp_threshold = 0.3
    config_mock.min_commitment_ticks = 3
    config_mock.goal_cooldown_ticks = 5
    config_mock.goal_cooldown_penalty = 0.5
    rng_mock = MagicMock()
    # Ensure next_float returns a predictable value
    rng_mock.next_float.return_value = 0.0
    return AIBrain(config_mock, rng_mock)

def test_decide_produces_consistent_result(mock_brain):
    # REAL Entity [AOA STABILIZATION]
    actor = Entity(id=1, kind="hero", faction=0)
    actor.spatial.pos = Vector2(5, 5)
    actor.mind.decision.ai_state = AIState.IDLE
    
    snapshot = MagicMock()
    snapshot.nearby_entity_ids.return_value = []
    snapshot.entities = {}
    snapshot.tick = 100
    snapshot.hour = 12
    
    mock_proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        mock_handler.handle.return_value = (AIState.WANDER, mock_proposal)
        mock_handlers.get.return_value = mock_handler
        
        # Mocking goal evaluation to avoid complex logic
        goal_mock = MagicMock(goal=GoalType.EXPLORE, target_state=AIState.WANDER)
        with patch.object(mock_brain._goal_evaluator, 'evaluate', return_value=[goal_mock]):
            with patch.object(mock_brain._goal_evaluator, 'select', return_value=goal_mock):
                state, proposal = mock_brain.decide(actor, snapshot)
                assert state == AIState.WANDER
                assert proposal.verb == ActionType.MOVE

def test_decide_increments_idle_ticks_on_rest(mock_brain):
    # REAL Entity [AOA STABILIZATION]
    actor = Entity(id=2, kind="hero", faction=0)
    actor.mind.decision.ai_state = AIState.IDLE
    actor.mind.decision.consecutive_idle_ticks = 5
    
    snapshot = MagicMock()
    snapshot.nearby_entity_ids.return_value = []
    snapshot.entities = {}
    snapshot.tick = 100
    snapshot.hour = 12
    
    # Force a REST proposal from AI logic
    mock_proposal = ActionProposal(actor_id=2, verb=ActionType.REST)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        mock_handler.handle.return_value = (AIState.IDLE, mock_proposal)
        mock_handlers.get.return_value = mock_handler
        
        # Mocking goal evaluation to stay in IDLE
        with patch.object(mock_brain._goal_evaluator, 'evaluate', return_value=[]):
            # Ensure return value uses a REAL AIState (IntEnum) to avoid int() conversion errors in brain.py
            mock_handler = MagicMock()
            mock_handler.handle.return_value = (AIState.IDLE, mock_proposal)
            with patch('src.ai.brain.STATE_HANDLERS', {AIState.IDLE: mock_handler}):
                state, proposal = mock_brain.decide(actor, snapshot)
                # AOA: decide is pure, check the proposal updates
                from src.actions.base import MindUpdate
                # Filter for the MindUpdate that actually has consecutive_idle_ticks set
                mind_up = next(u for u in proposal.updates if isinstance(u, MindUpdate) and u.consecutive_idle_ticks is not None)
                assert mind_up.consecutive_idle_ticks == 6

def test_perception_phase_appraisal_sync(mock_brain):
    from src.core.models.enums import EmotionType
    
    # REAL Entity [AOA STABILIZATION]
    actor = Entity(id=3, kind="hero", faction=0)
    actor.combat.max_hp = 100
    actor.combat.hp = 50 # 0.5 ratio
    actor.spatial.pos = Vector2(5, 5)
    actor.spatial.vision_range = 10
    
    snapshot = MagicMock()
    snapshot.nearby_entity_ids.return_value = []
    snapshot.entities = {}
    snapshot.tick = 100
    snapshot.hour = 12
    
    # Initial decide (appraisal)
    mock_brain.decide(actor, snapshot)
    
    # Low HP trigger
    actor.combat.hp = 20 # 0.2 ratio
    
    # Mock goals with proper Enums to avoid MindUpdate validation errors
    goal_mock = MagicMock(goal=GoalType.FLEE, target_state=AIState.FLEE)
    with patch.object(mock_brain._goal_evaluator, 'evaluate', return_value=[goal_mock]):
        with patch.object(mock_brain._goal_evaluator, 'select', return_value=goal_mock):
            # Ensure return value uses a REAL AIState (IntEnum) to avoid int() conversion errors in brain.py
            mock_handler = MagicMock()
            mock_handler.handle.return_value = (AIState.COMBAT, ActionProposal(actor_id=actor.id, verb=ActionType.ATTACK))
            with patch('src.ai.brain.STATE_HANDLERS', {AIState.COMBAT: mock_handler}):
                state, proposal = mock_brain.decide(actor, snapshot)
                # Check for panic delta in MindUpdate
                from src.actions.base import MindUpdate
                mind_up = next(u for u in proposal.updates if isinstance(u, MindUpdate) and u.emotion_delta is not None)
                assert mind_up.emotion_delta[EmotionType.PANIC] > 0
