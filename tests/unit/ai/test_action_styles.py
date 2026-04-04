import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain, AIContext
from src.core.models.enums import AIState, ActionType
from src.actions.base import ActionProposal
from src.core.entities.entity import Entity

def test_execution_phase_modifies_proposal_with_aggressive_style():
    # Setup with REAL Entity [AOA STABILIZATION: Entity-First Mocking]
    config = MagicMock()
    config.min_commitment_ticks = 3
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = Entity(id=1, kind="hero", faction="player")
    actor.identity.display_name = "AggressiveAgent"
    actor.mind.decision.action_style = "aggressive"
    
    snapshot = MagicMock()
    snapshot.tick = 0
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=config, 
        rng=rng, 
        faction_reg=brain._faction_reg
    )
    state = AIState.HUNT
    
    # Mock handler that returns a standard proposal
    proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        # Use a REAL AIState for handle return to avoid int() conversion errors
        mock_handler.handle.return_value = (AIState.IDLE, proposal)
        mock_handlers.get.return_value = mock_handler
        
        _, final_proposal = brain._finalization_phase(ctx, state, [])
        
        # Aggressive style should add a tag or modify the proposal
        assert "aggressive" in final_proposal.reason.lower()

def test_execution_phase_modifies_proposal_with_evasive_style():
    # Setup with REAL Entity [AOA STABILIZATION]
    config = MagicMock()
    config.min_commitment_ticks = 3
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = Entity(id=2, kind="hero", faction="player")
    actor.identity.display_name = "EvasiveAgent"
    actor.mind.decision.action_style = "evasive"
    
    snapshot = MagicMock()
    snapshot.tick = 0
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=config, 
        rng=rng, 
        faction_reg=brain._faction_reg
    )
    state = AIState.WANDER
    
    # Mock handler that returns a standard proposal
    proposal = ActionProposal(actor_id=2, verb=ActionType.MOVE)
    with patch('src.ai.brain.STATE_HANDLERS') as mock_handlers:
        mock_handler = MagicMock()
        mock_handler.handle.return_value = (AIState.IDLE, proposal)
        mock_handlers.get.return_value = mock_handler
        
        _, final_proposal = brain._finalization_phase(ctx, state, [])
        
        # Evasive style should add a tag or modify the proposal
        assert "evasive" in final_proposal.reason.lower()
