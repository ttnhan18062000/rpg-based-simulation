"""Base classes for simulation systems and their execution context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG


@dataclass(frozen=True)
class SystemContext:
    """Narrow interface for systems to access world state and infrastructure."""
    config: SimulationConfig
    world: WorldState
    rng: DeterministicRNG
    generator: Any
    faction_reg: Any
    emit: Callable[[str, str, tuple[int, ...], dict | None], None]


class System:
    """Base class for all decoupled simulation systems."""
    
    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self.config = config
        self.rng = rng

    def on_init(self, context: SystemContext) -> None:
        """Called when the system is first initialized."""
        pass

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Called every N ticks based on registration rate."""
        pass

    def on_shutdown(self, context: SystemContext) -> None:
        """Called when the simulation ends."""
        pass
