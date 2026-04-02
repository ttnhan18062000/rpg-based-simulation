import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain
from src.core.models.enums import AIState, ActionType
from src.actions.base import ActionProposal

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
    actor = MagicMock()
    actor.mind.ai_state = AIState.IDLE
    actor.id = 1
    actor.identity.identity.faction = "player"
    actor.stats = MagicMock()
    actor.stats.spatial.vision_range = 10
    actor.stats.combat.hp_ratio = 1.0
    actor.identity = MagicMock()
    actor.identity.openness = 0.5
    actor.identity.agreeableness = 0.1
    actor.identity.progression.hero_class = None
    from src.core.aspects.mind import MindAspect
    actor.mind = MindAspect()
    actor.mind.goal_committed_at = 0
    actor.mind.goal_cooldowns = {}
    actor.mind.boredom_multipliers = {}
    
    actor.progression = MagicMock()
    actor.progression.age_ticks = 10
    actor.progression.longevity_limit = 1000
    
    snapshot = MagicMock()
    snapshot.nearby_entity_ids.return_value = []
    snapshot.entities = {}
    snapshot.tick = 100
    
    mock_proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        mock_handler.handle.return_value = (AIState.WANDER, mock_proposal)
        mock_handlers.get.return_value = mock_handler
        
        # Mocking goal evaluation to avoid complex logic
        with patch.object(mock_brain._goal_evaluator, 'evaluate', return_value=[MagicMock(goal="explore", target_state=AIState.WANDER)]):
            selected_mock = MagicMock(target_state=AIState.WANDER)
            selected_mock.goal = "explore"
            with patch.object(mock_brain._goal_evaluator, 'select', return_value=selected_mock):
                state, proposal = mock_brain.decide(actor, snapshot)
                assert state == AIState.WANDER
                assert proposal.verb == ActionType.MOVE

def test_decide_increments_idle_ticks_on_rest(mock_brain):
    actor = MagicMock()
    actor.mind.ai_state = AIState.IDLE
    actor.id = 1
    actor.identity.identity.faction = "player"
    actor.consecutive_idle_ticks = 5
    actor.stats = MagicMock()
    actor.stats.spatial.vision_range = 10
    actor.stats.combat.hp_ratio = 1.0
    actor.identity = MagicMock()
    actor.identity.openness = 0.5
    actor.identity.agreeableness = 0.1
    actor.identity.progression.hero_class = None
    from src.core.aspects.mind import MindAspect
    actor.mind = MindAspect()
    actor.mind.goal_committed_at = 0
    actor.mind.goal_cooldowns = {}
    actor.mind.boredom_multipliers = {}
    
    actor.progression = MagicMock()
    actor.progression.age_ticks = 10
    actor.progression.longevity_limit = 1000
    
    snapshot = MagicMock()
    snapshot.nearby_entity_ids.return_value = []
    snapshot.entities = {}
    snapshot.tick = 100
    
    mock_proposal = ActionProposal(actor_id=1, verb=ActionType.REST)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        mock_handler.handle.return_value = (AIState.IDLE, mock_proposal)
        mock_handlers.get.return_value = mock_handler
        
        # Mocking goal evaluation to stay in IDLE
        with patch.object(mock_brain._goal_evaluator, 'evaluate', return_value=[]):
            mock_brain.decide(actor, snapshot)
            assert actor.consecutive_idle_ticks == 6

def test_perception_phase_appraisal_sync(mock_brain):
    actor = MagicMock()
    actor.stats = MagicMock()
    actor.stats.combat.hp_ratio = 0.5
    actor.stats.spatial.vision_range = 10
    actor.identity = MagicMock()
    actor.identity.openness = 0.5
    actor.identity.agreeableness = 0.1
    actor.identity.progression.hero_class = None
    actor.mind = MagicMock()
    actor.mind.emotional_state = {}
    actor.mind.spatial.pos_history = []
    actor.mind.max_attention_slots = 5
    actor.mind.attention_pool = []
    actor.mind.goal_committed_at = 0
    actor.mind.memory_locations = {}
    actor.mind.region_fatigue = {}
    actor.boredom_multipliers = {}
    actor.identity.identity.faction = "player"
    actor.progression = MagicMock()
    actor.progression.age_ticks = 10
    actor.progression.longevity_limit = 1000
    
    snapshot = MagicMock()
    snapshot.nearby_entity_ids.return_value = []
    snapshot.entities = {}
    snapshot.tick = 100
    
    # This should trigger appraisal without errors
    mock_brain.decide(actor, snapshot)
    
    # Now trigger low HP
    actor.stats.combat.hp_ratio = 0.2
    mock_brain.decide(actor, snapshot)
    assert actor.mind.emotional_state.get("panic", 0) > 0
