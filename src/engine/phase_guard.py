"""Phase boundary enforcement: Runtime guards for AOA simulation phases."""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class ActionProposalGuard:
    """Context manager to enforce read-only world state during Action Proposal phase.
    
    Any attempt to mutate the world or its entities within this block will raise 
    a RuntimeError, ensuring that AI logic remains purely functional and proposal-based.
    """
    
    def __init__(self, world: WorldState):
        self.world = world

    def __enter__(self):
        # Lock the world state
        if hasattr(self.world, "freeze"):
            self.world.freeze()
        return self.world

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We don't un-freeze here because snapshots should stay frozen.
        # This guard is purely for runtime detection of illegal mutations.
        pass
