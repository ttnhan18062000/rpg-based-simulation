"""EnvironmentSystem handles territory effects, perception, and memories."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.gameplay.effects import territory_debuff
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class EnvironmentSystem(System):
    """System for spatial-awareness, memory, and environmental effects."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute environment phases."""
        self._process_territory_effects(context)
        self._update_entity_memory(context, tick)
        self._update_entity_goals(context)

    def _process_territory_effects(self, context: SystemContext) -> None:
        """Apply passive debuffs to entities in non-allied territory."""
        world = context.world
        reg = context.faction_reg
        grid = world.grid
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            # Check territory (Town vs Camp)
            is_town = grid.is_town(entity.spatial.pos)
            is_camp = grid.is_camp(entity.spatial.pos)
            
            if is_town and not reg.is_allied(entity.identity.faction, "HERO_GUILD"):
                entity.combat.effects.append(territory_debuff(source="Town Watch"))
            elif is_camp and not reg.is_allied(entity.identity.faction, "GOBLIN_HORDE"):
                entity.combat.effects.append(territory_debuff(source="Camp Sentinels"))

    def _update_entity_memory(self, context: SystemContext, tick: int) -> None:
        """Update entity perception of terrain and other entities."""
        world = context.world
        grid = world.grid
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            # Vision-based terrain update
            vr = int(entity.spatial.vision_range)
            px, py = int(entity.spatial.pos.x), int(entity.spatial.pos.y)
            for dx in range(-vr, vr + 1):
                for dy in range(-vr, vr + 1):
                    # Simple square vision for performance
                    tx, ty = px + dx, py + dy
                    if grid.in_bounds_xy(tx, ty):
                        mat = grid.get_xy(tx, ty)
                        entity.mind.perception.terrain_memory[(tx, ty)] = mat
            
            # Entity awareness: REMOVED [PHASE 1]
            # Entity perception is now handled by BeliefService in AIBrain._sensory_perception_phase.
            # The legacy dict-based entity_memory was incompatible with typed BeliefRecord objects.


    def _update_entity_goals(self, context: SystemContext) -> None:
        """Re-evaluate goals for all entities if needed."""
        world = context.world
        for entity in world.entities.values():
            if not entity.combat.alive or not entity.mind.decision.goals:
                continue
            
            # Logic for pruning completed goals or prioritizing new ones
            entity.mind.decision.goals = [g for g in entity.mind.decision.goals if not getattr(g, 'is_complete', False)]
