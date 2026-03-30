from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .context import EngineContext

class EnginePhase(ABC):
    """Abstract base class for all engine execution phases."""
    
    @abstractmethod
    def execute(self, ctx: EngineContext) -> Any:
        """Run the logic for this phase."""
        pass
