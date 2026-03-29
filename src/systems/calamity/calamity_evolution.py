"""CalamityEvolutionSystem manages world boss growth and skill acquisition."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.models.enums import AIState, Element
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class CalamityEvolutionSystem(System):
    """System that evolves World Bosses (Calamities) based on their achievements."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Process evolution checks every 500 ticks."""
        if tick % 500 != 0:
            return

        for entity in context.world.entities.values():
            if not entity.combat.alive or not entity.identity.is_world_boss:
                continue

            self._check_evolution(context, entity, tick)

    def _check_evolution(self, context: SystemContext, entity: Any, tick: int) -> None:
        """Evaluate glory and trigger evolution if threshold met."""
        glory_total = sum(
            entry.get("impact", 0.0) 
            for entry in entity.mind.memory_log 
            if entry.get("type") == "GLORY"
        )

        # Basic evolution logic: every 50 glory = 1 evolution level
        current_evo = entity.mind.memory.get("evolution_level", 0)
        target_evo = int(glory_total // 50)

        if target_evo > current_evo:
            self._evolve(context, entity, current_evo, target_evo)
            entity.mind.memory["evolution_level"] = target_evo

    def _evolve(self, context: SystemContext, entity: Any, old_level: int, new_level: int) -> None:
        """Apply stat boosts and new skills upon evolution."""
        levels_gained = new_level - old_level
        
        # Stat boosts: +20% HP/ATK per evolution level
        boost_factor = 1.0 + (0.2 * levels_gained)
        entity.combat.max_hp = int(entity.combat.max_hp * boost_factor)
        entity.combat.hp = entity.combat.max_hp
        entity.combat.atk = int(entity.combat.atk * boost_factor)
        
        # Evolution title update
        entity.identity.display_name = f"Evolved {entity.identity.display_name}"
        
        from src.core.data.events import RenownEvent
        if hasattr(context.world, "event_bus") and context.world.event_bus:
            context.world.event_bus.publish(RenownEvent(
                entity_id=entity.id,
                glory_type="evolution",
                description=f"The calamity {entity.kind} has EVOLVED into a more powerful form!",
                renown_gain=levels_gained * 10
            ))

        if context.emit:
            context.emit("calamity", f"CALAMITY {entity.id} ({entity.kind}) HAS EVOLVED! Level {old_level} → {new_level}",
                        entity_ids=(entity.id,),
                        metadata={"type": "evolution", "level": new_level})
        
        logger.info("Calamity %d evolved to level %d", entity.id, new_level)
