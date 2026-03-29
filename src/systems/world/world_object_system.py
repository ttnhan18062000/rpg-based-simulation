"""WorldObjectSystem handles resource nodes and treasure chests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class WorldObjectSystem(System):
    """System for managing world objects like resource nodes and chests."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute world object sub-phases."""
        self._tick_resource_nodes(context)
        self._tick_treasure_chests(context, tick)

    def _tick_resource_nodes(self, context: SystemContext) -> None:
        """Tick cooldowns on depleted resource nodes so they respawn."""
        for node in context.world.resource_nodes.values():
            node.tick_cooldown()

    def _tick_treasure_chests(self, context: SystemContext, tick: int) -> None:
        """Respawn looted treasure chests and their guards."""
        for chest in context.world.treasure_chests.values():
            if chest.try_respawn(tick):
                # Respawn guard if it was killed
                if chest.guard_entity_id is not None:
                    guard = context.world.entities.get(chest.guard_entity_id)
                    if guard is None or not guard.combat.alive:
                        self._spawn_chest_guard(context, chest)
                logger.info("Tick %d: Treasure chest %d respawned at %s (tier %d)",
                            tick, chest.chest_id, chest.spatial.pos, chest.identity.tier)

    def _spawn_chest_guard(self, context: SystemContext, chest: Any) -> None:
        """Spawn an elite guard entity next to a treasure chest."""
        from src.core.models.enums import EnemyTier
        from src.core.gameplay.items.items import TERRAIN_RACE
        
        world = context.world
        # Determine race from terrain at chest position
        mat = world.grid.material_at(chest.spatial.pos.x, chest.spatial.pos.y)
        race = TERRAIN_RACE.get(mat, "goblin")
        tier = min(chest.identity.tier + 1, EnemyTier.ELITE)  # Chest tier 1→WARRIOR, 2→ELITE, 3→ELITE
        
        entity = context.generator.spawn_race(
            world, race=race, tier=tier, near_pos=chest.spatial.pos)
        world.add_entity(entity)
        chest.guard_entity_id = entity.id
        logger.info("Tick %d: Spawned chest guard %s #%d at %s (tier %d)",
                    world.tick, entity.kind, entity.id, entity.spatial.pos, tier)
