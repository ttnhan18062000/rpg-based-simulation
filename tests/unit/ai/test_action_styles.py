import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain
from src.core.models.enums import AIState, ActionType
from src.actions.base import ActionProposal

def test_execution_phase_modifies_proposal_with_aggressive_style():
    # Setup
    config = MagicMock()
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = MagicMock()
    actor.mind.action_style = "aggressive"
    
    ctx = MagicMock(actor=actor)
    state = AIState.HUNT
    
    # Mock handler that returns a standard proposal
    proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        mock_handler.handle.return_value = (AIState.HUNT, proposal)
        mock_handlers.get.return_value = mock_handler
        
        _, final_proposal = brain._finalization_phase(ctx, state)
        
        # Aggressive style should add a tag or modify the proposal
        assert "aggressive" in final_proposal.reason.lower()

def test_execution_phase_modifies_proposal_with_evasive_style():
    config = MagicMock()
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = MagicMock()
    actor.mind.action_style = "evasive"
    
    ctx = MagicMock(actor=actor)
    state = AIState.WANDER
    
    proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        mock_handler.handle.return_value = (AIState.WANDER, proposal)
        mock_handlers.get.return_value = mock_handler
        
        _, final_proposal = brain._finalization_phase(ctx, state)
        
        assert "evasive" in final_proposal.reason.lower()
