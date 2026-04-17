from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase
from src.systems.infrastructure.base import SystemContext

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class ResolutionPhase(EnginePhase):
    """Resolve action conflicts and apply definitive state changes."""
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Resolution",
            description="Resolving conflicts and applying authoritative state changes.",
            permissions={
                "world": PhaseAccess.READ_WRITE, # Actions mutate world state
                "config": PhaseAccess.READ,
                "rng": PhaseAccess.READ,        # Needed for SystemContext
                "generator": PhaseAccess.READ,  # Needed for SystemContext
                "faction_reg": PhaseAccess.READ, # Needed for SystemContext
                "conflict_resolver": PhaseAccess.READ_WRITE,
                "action_system": PhaseAccess.READ_WRITE,
                "hero_lifecycle": PhaseAccess.READ_WRITE,
                "tick_proposals": PhaseAccess.READ,
                "tick_applied": PhaseAccess.MUTATE,
                "tick_events": PhaseAccess.READ_WRITE,
                "emit": PhaseAccess.READ_WRITE
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        if not ctx.tick_proposals:
            ctx.tick_applied = []
            return

        # 1. Conflict Resolution
        to_apply = ctx.conflict_resolver.resolve(ctx.tick_proposals, ctx.world)
        
        system_ctx = SystemContext(
            ctx.config, ctx.world, ctx.rng, ctx.generator, 
            ctx.faction_reg, ctx.emit
        )

        # 2. Sequential Application & Metadata (The Rebuild: Pillars 1-3)
        # Consolidates tactical actions and AI-intent metadata application.
        ctx.action_system.process_applied_actions(system_ctx, to_apply)
        ctx.tick_applied = to_apply
        
        # 3. [Milestone 1] Hero lifecycle moved to PreSystemsPhase to ensure
        # it runs even on quiet ticks.
