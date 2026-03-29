"""SystemManager for coordinates multiple simulation systems."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from src.systems.infrastructure.base import SystemContext

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG
    from src.systems.infrastructure.base import System

logger = logging.getLogger(__name__)


class SystemManager:
    """Orchestrates the execution of decoupled simulation systems."""
    
    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng
        self._systems: list[tuple[System, int]] = []
        self._context: SystemContext | None = None

    def register(self, system: System, rate: int) -> None:
        """Register a system to run every 'rate' ticks."""
        logger.debug("Registering system %s at rate %d", system.__class__.__name__, rate)
        self._systems.append((system, rate))

    def init_all(self, world: WorldState, generator: Any, faction_reg: Any, emit: Callable) -> None:
        """Initialize all registered systems within a WorldContext."""
        self._context = SystemContext(
            config=self._config, 
            world=world, 
            rng=self._rng,
            generator=generator,
            faction_reg=faction_reg,
            emit=emit
        )
        for system, _ in self._systems:
            system.on_init(self._context)

    def tick(self, world: WorldState, tick: int) -> None:
        """Execute all systems that are due for a tick."""
        if self._context is None:
             # Lazy init if not already done
             self.init_all(world, None, None, lambda *a, **k: None)

        for system, rate in self._systems:
            if tick % rate == 0:
                system.on_tick(self._context, tick)

    def shutdown(self) -> None:
        """Shutdown all systems."""
        if self._context:
            for system, _ in self._systems:
                system.on_shutdown(self._context)
