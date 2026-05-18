from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.engine.phases.base import EnginePhase
from src_legacy.utils.metrics import SIM_TICK_DURATION
from src_legacy.systems.infrastructure.base import SystemContext

if TYPE_CHECKING:
    from src_legacy.engine.phases.context import EngineContext
    from src_legacy.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class PreSystemsPhase(EnginePhase):
    """Execute environmental systems, calamities, and other pre-action logic."""
    
    @property
    def contract(self) -> PhaseContract:
        from src_legacy.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Pre-Systems",
            description="Executing regional systems and calamities.",
            permissions={
                "config": PhaseAccess.READ,
                "world": PhaseAccess.READ_WRITE,
                "system_manager": PhaseAccess.READ_WRITE,
                "rng": PhaseAccess.READ_WRITE,
                "emit": PhaseAccess.READ,
                "action_system": PhaseAccess.READ,
                "hero_lifecycle": PhaseAccess.READ,
                "generator": PhaseAccess.READ,
                "faction_reg": PhaseAccess.READ
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        with SIM_TICK_DURATION.labels(phase="subsystems").time():
            # 1. Passive World Advancement (Milestone 1)
            # These must run every tick, even if no entities act.
            ctx.action_system._apply_biological_decay(ctx.world, ctx.config)
            
            # Milestone 2: Propagate on_tick to all entities (resets moved_this_tick, etc.)
            for entity in ctx.world.entities.values():
                if entity.combat.alive:
                    entity.on_tick(ctx.world.tick)
            
            system_ctx = SystemContext(
                ctx.config, ctx.world, ctx.rng, ctx.generator, 
                ctx.faction_reg, ctx.emit
            )
            ctx.hero_lifecycle.on_tick(system_ctx, ctx.world.tick)
            
            # 2. Existing Subsystems
            ctx.system_manager.tick(ctx.world, ctx.world.tick)
