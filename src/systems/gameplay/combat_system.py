"""CombatSystem handles status effects, engagement, and threat decay."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class CombatSystem(System):
    """System for managing combat-related logic and status effects."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute combat sub-phases."""
        self._tick_effects(context)
        self._tick_engagement(context)
        self._tick_threat_decay(context)

    def _tick_effects(self, context: SystemContext) -> None:
        """Tick down status effect durations and apply per-tick HP changes."""
        for entity in context.world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            combat = entity.combat
            if not combat or not combat.effects:
                continue
                
            # Use a list copy to allow removal during iteration if needed 
            # (though here we filter at the end)
            for eff in combat.effects:
                # Apply hp_per_tick (positive = regen, negative = DoT)
                if eff.hp_per_tick != 0 and not eff.expired:
                    combat.hp = max(0, min(
                        combat.hp + eff.hp_per_tick,
                        entity.combat.max_hp,
                    ))
                eff.tick()
                
            combat.effects = [e for e in combat.effects if not e.expired]

    def _tick_engagement(self, context: SystemContext) -> None:
        """Track how many ticks each entity has been adjacent to a hostile."""
        reg = context.faction_reg
        spatial = context.world.spatial_index
        entities = context.world.entities
        
        for entity in entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            combat = entity.combat
            if not combat:
                continue
                
            adjacent_hostile = False
            for oid in spatial.query_radius(entity.spatial.pos, 1):
                if oid == entity.id:
                    continue
                other = entities.get(oid)
                if other is None or not other.combat.alive or other.kind == "generator":
                    continue
                    
                # Manhattan distance check and hostility check
                if (abs(entity.spatial.pos.x - other.spatial.pos.x) + abs(entity.spatial.pos.y - other.spatial.pos.y) <= 1 
                    and reg.is_hostile(entity.identity.faction, other.identity.faction)):
                    adjacent_hostile = True
                    break
                    
            if adjacent_hostile:
                entity.mind.navigation.engaged_ticks = min(entity.mind.navigation.engaged_ticks + 1, 10)
                # Disrupt routine patterns for 50 ticks (5 hours) after contact [PHASE 3]
                entity.mind.routine.disrupted_until_tick = context.world.tick + 50
            else:
                entity.mind.navigation.engaged_ticks = 0

    def _tick_threat_decay(self, context: SystemContext) -> None:
        """Decay threat values over time."""
        decay = 1.0 - context.config.threat_decay_rate
        entities = context.world.entities
        
        for entity in entities.values():
            to_remove: list[int] = []
            for attacker_id, threat in entity.mind.perception.threat_table.items():
                attacker = entities.get(attacker_id)
                if attacker is None or not attacker.combat.alive:
                    to_remove.append(attacker_id)
                    continue
                    
                new_threat = threat * decay
                if new_threat < 1.0:
                    to_remove.append(attacker_id)
                else:
                    entity.mind.perception.threat_table[attacker_id] = new_threat
                    
            for aid in to_remove:
                del entity.mind.perception.threat_table[aid]
