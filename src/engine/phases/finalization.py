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
        """Finalization phase now focuses on non-mutating cleanup and notification.
        
        AOA Hardening: AI State and Reasoning are authoritatively applied during 
        the Resolution phase (via ActionSystem). Redundant application here is 
        removed to prevent future divergence.
        """
        pass
