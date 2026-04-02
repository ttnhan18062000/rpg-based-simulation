from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase
from src.core.gameplay.faction import Faction
from src.systems.infrastructure.base import SystemContext

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class CleanupPhase(EnginePhase):
    """Remove dead entities, drop loot, and handle hero respawns."""
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Cleanup",
            description="Removing dead entities and handling respawns.",
            permissions={
                "world": PhaseAccess.READ_WRITE, # Removing entities mutates world
                "config": PhaseAccess.READ,
                "generator": PhaseAccess.READ,
                "faction_reg": PhaseAccess.READ,
                "hero_lifecycle": PhaseAccess.READ_WRITE,
                "emit": PhaseAccess.READ_WRITE
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        tick = ctx.world.tick
        dead_ids = sorted([eid for eid, e in ctx.world.entities.items() if not e.combat.alive])
        
        for eid in dead_ids:
            entity = ctx.world.entities.get(eid)
            if entity is None:
                continue

            # 1. Hero Death Handling (Respawn/Recovery)
            if entity.identity.faction == Faction.HERO_GUILD and entity.spatial.home_pos is not None:
                system_ctx = SystemContext(
                    ctx.config, ctx.world, ctx.rng, ctx.generator, 
                    ctx.faction_reg, ctx.emit
                )
                resolved = ctx.hero_lifecycle.process_hero_death(system_ctx, entity, tick)
                if resolved:
                    continue

            # 2. Mob/Generic Death Handling
            from src.utils.metrics import TOTAL_DEATHS
            TOTAL_DEATHS.inc()

            # Loot Drop
            if entity.inventory:
                dropped = entity.inventory.get_all_item_ids()
                if dropped:
                    ctx.world.drop_items(entity.spatial.pos, dropped)
                    logger.info(
                        "Tick %d: Entity %d (%s) dropped %d items at %s",
                        tick, eid, entity.kind, len(dropped), entity.spatial.pos,
                    )

            # World Removal
            removed = ctx.world.remove_entity(eid)
            if removed:
                logger.info(
                    "Tick %d: Entity %d (%s Lv%d) died.", 
                    tick, eid, removed.kind, removed.progression.level
                )
                
                # Publish to event bus if available
                if hasattr(ctx.world, "event_bus") and ctx.world.event_bus:
                    from src.core.data.events import DeathEvent
                    ctx.world.event_bus.publish(DeathEvent(
                        entity_id=eid, killer_id=None,
                        x=removed.spatial.pos.x, y=removed.spatial.pos.y,
                        level_at_death=removed.progression.level,
                        is_permadeath=True
                    ))
