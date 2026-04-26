from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .context import EngineContext
    from .contract import PhaseContract

class EnginePhase(ABC):
    """Abstract base class for all engine execution phases."""
    
    @property
    @abstractmethod
    def contract(self) -> PhaseContract:
        """Declared formal access contract for this phase."""
        pass
    
    @abstractmethod
    def execute(self, ctx: EngineContext) -> Any:
        """Run the logic for this phase."""
        pass
