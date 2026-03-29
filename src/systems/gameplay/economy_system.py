"""EconomySystem handles town healing, hero respawns, and global state."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.models.enums import AIState
from src.core.gameplay.faction import Faction
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class EconomySystem(System):
    """System for managing simulation lifecycle, town services, and rewards."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute economy phases."""
        self._heal_home_entities(context, tick)
        self._process_hero_replacements(context, tick)
        self._check_endgame_conditions(context, tick)

    def _heal_home_entities(self, context: SystemContext, tick: int) -> None:
        """Heal entities on home territory and apply town aura damage."""
        cfg = context.config
        world = context.world
        reg = context.identity
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue

            on_town = world.grid.is_town(entity.spatial.pos)
            on_camp = world.grid.is_camp(entity.spatial.pos)

            # Town aura: hostile entities in town take damage
            if on_town and reg.is_hostile(entity.identity.faction, Faction.HERO_GUILD):
                entity.stats.combat.hp -= cfg.town_aura_damage
                continue

            # Healing in allied territory
            if entity.stats.combat.hp < entity.stats.combat.max_hp:
                if (entity.identity.faction == Faction.HERO_GUILD and on_town):
                    heal = cfg.hero_heal_per_tick if entity.mind.ai_state == AIState.RESTING_IN_TOWN else cfg.town_passive_heal
                    entity.stats.combat.hp = min(entity.stats.combat.hp + heal, entity.stats.combat.max_hp)
                elif (entity.identity.faction == Faction.GOBLIN_HORDE and on_camp and entity.mind.ai_state == AIState.GUARD_CAMP):
                    entity.stats.combat.hp = min(entity.stats.combat.hp + 1, entity.stats.combat.max_hp)

    def _process_hero_replacements(self, context: SystemContext, tick: int) -> None:
        """Handle hero respawn/replacement logic."""
        cfg = context.config
        world = context.world
        
        # Check for dead heroes to replace
        for eid, entity in list(world.entities.items()):
            if not entity.combat.alive and entity.identity.role == Faction.HERO_GUILD:
                # Logic for hero replacement (e.g., adding to a queue)
                pass

    def _check_endgame_conditions(self, context: SystemContext, tick: int) -> None:
        """Check for terminal world states (e.g., town destruction)."""
        # Future: If town is destroyed, signal simulation stop
        pass
