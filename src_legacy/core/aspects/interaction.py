from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import Field
from src_legacy.core.models.base import Aspect

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity

class InteractionAspect(Aspect):
    """Aspect handling non-combat interactions: looting, harvesting, trade, and resting."""
    
    # State tracking
    loot_progress: int = 0
    
    # Interaction modifiers
    interaction_speed: float = 1.0
    loot_bonus: float = 1.0
    trade_bonus: float = 1.0
    rest_efficiency: float = 1.0
    
    def on_tick(self, tick: int) -> None:
        """Lifecycle hook (could be used for automatic cooldowns or decay)."""
        pass


# Rebuild Model to finalize Pydantic setup
InteractionAspect.model_rebuild()
