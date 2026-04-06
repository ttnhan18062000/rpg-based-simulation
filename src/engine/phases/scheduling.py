from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class SchedulingPhase(EnginePhase):
    """Identify entities ready to act and run immediate generators."""
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Scheduling",
            description="Identifying ready entities and spawning new ones.",
            permissions={
                "world": PhaseAccess.READ,
                "config": PhaseAccess.READ, # Used for tick duration checks
                "generator": PhaseAccess.READ_WRITE,
                "tick_ready_entities": PhaseAccess.MUTATE,
                "tick_new_entities": PhaseAccess.READ_WRITE, # Needed for .append()
                "emit": PhaseAccess.READ
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        # 1. Generators (Emit authoritative WorldUpdate)
        if ctx.generator.should_spawn(ctx.world):
            entity = ctx.generator.spawn(ctx.world)
            # AOA Stabilization: We don't call world.add_entity here!
            # Instead, we queue it for the engine to apply in the Resolution phase.
            ctx.tick_new_entities.append(entity)
            logger.info("Tick %d: Queued spawn of %s #%d at %s", ctx.world.tick, entity.kind, entity.id, entity.spatial.pos)

        # 2. Scheduling (Identify ready entities)

        # 2. Scheduling (Identify ready entities)
        current_time = float(ctx.world.tick)
        ready = [
            e
            for e in ctx.world.entities.values()
            if e.combat.alive and e.kind != "generator" and e.next_act_at <= current_time
        ]
        
        # Deterministic order: next_act_at, then entity ID
        ready.sort(key=lambda e: (e.next_act_at, e.id))
        ctx.tick_ready_entities = ready
