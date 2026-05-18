"""EvolutionSystem handles Nemesis evolution and monster tier-ups.

When a monster kills a hero, it gains experience and can evolve into a higher tier
with a specialized prefix (e.g., 'Hero-Slayer').
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.core.models.enums import EnemyTier, EntityRole

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class EvolutionSystem:
    """Logic for entity evolution based on combat victory."""

    @staticmethod
    def on_hero_slain(monster: Entity, hero: Entity, world: WorldState) -> None:
        """Called when a monster successfully kills a hero."""
        if monster.identity.role != EntityRole.MOB:
            return

        monster.identity.kill_count += 1
        logger.info(f"Tick {world.tick}: Monster {monster.id} ({monster.kind}) killed Hero {hero.id}! Kill count: {monster.identity.kill_count}")

        # Evolution trigger: 1 kill for basic, more for higher
        threshold = 1 if monster.identity.tier < 2 else 3
        
        if monster.identity.kill_count >= threshold and monster.identity.tier < 3:
            EvolutionSystem.evolve_monster(monster, world)

    @staticmethod
    def evolve_monster(monster: Entity, world: WorldState) -> None:
        """Upgrade monster tier and stats."""
        old_kind = monster.kind
        monster.identity.tier += 1
        monster.identity.kill_count = 0
        
        # Add a prefix to the name
        prefixes = ["Bold", "Brutal", "Hero-Slayer", "Merciless", "Ancient"]
        prefix = prefixes[min(monster.identity.tier, len(prefixes)-1)]
        monster.identity.display_name = f"{prefix} {monster.identity.display_name}"
        
        # Stat boost
        monster.combat.max_hp = int(monster.combat.max_hp * 1.5)
        monster.combat.hp = monster.combat.max_hp
        monster.combat.atk_base += 5 * monster.identity.tier
        monster.combat.def_base += 2 * monster.identity.tier
        
        logger.info(f"Tick {world.tick}: NEMESIS EVOLUTION! {old_kind} #{monster.id} evolved into {monster.identity.display_name} (Tier {monster.identity.tier})")
        
        # Add a visual or region-wide aura effect (Pillar 5)
        if hasattr(world, "event_bus") and world.event_bus:
            # world.event_bus.publish(NemesisEvolutionEvent(...))
            pass
