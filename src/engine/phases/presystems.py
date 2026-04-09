from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase
from src.utils.metrics import SIM_TICK_DURATION

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class PreSystemsPhase(EnginePhase):
    """Execute environmental systems, calamities, and other pre-action logic."""
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Pre-Systems",
            description="Executing regional systems and calamities.",
            permissions={
                "config": PhaseAccess.READ,
                "world": PhaseAccess.READ_WRITE,
                "system_manager": PhaseAccess.READ_WRITE,
                "rng": PhaseAccess.READ_WRITE,
                "emit": PhaseAccess.READ
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        with SIM_TICK_DURATION.labels(phase="subsystems").time():
            ctx.system_manager.tick(ctx.world, ctx.world.tick)
