from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase
from src.core.models.enums import AIState

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class FinalizationPhase(EnginePhase):
    """Propagate resolved AI state and intent changes back to WorldState actors."""
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Finalization",
            description="Syncing AI state and reasoning for applied actions.",
            permissions={
                "world": PhaseAccess.READ_WRITE,
                "tick_applied": PhaseAccess.READ,
                "emit": PhaseAccess.READ
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        tick = ctx.world.tick
        applied = ctx.tick_applied
        
        # Propagate AI State changes from authoritative decisions
        for proposal in applied:
            entity = ctx.world.entities.get(proposal.actor_id)
            if entity is None: 
                continue
            
            # Sync AI State (Decision Aspect)
            if proposal.new_ai_state is not None:
                entity.mind.decision.ai_state = AIState(proposal.new_ai_state)
            
            # Sync Reasoning for Introspection
            if proposal.reason:
                entity.mind.decision.last_reason = proposal.reason
