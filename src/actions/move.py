"""MoveAction — validates and applies movement proposals.

Refactored for AOA Stabilization:
- Direct aspect access (spatial, combat, progression).
- Removed legacy property shims and StatsProxy dependencies.
- Standardized action delay and stamina costs.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal
from src.core.models.enums import ActionType
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class MoveAction:
    """Stateless handler for MOVE proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState, occupied: set[tuple[int, int]]) -> bool:
        if proposal.verb != ActionType.MOVE: return False
        entity = world.entities.get(proposal.actor_id)
        if not entity or not entity.combat.alive: return False
        
        target: Vector2 = proposal.target
        if not world.grid.is_walkable(target): return False
        
        # O(1) Check: Is anyone already there? (AOA Phase 6)
        if world.is_occupied(target): return False
        
        # Set Check: Did anyone ELSE move there this tick?
        if (target.x, target.y) in occupied: return False
        
        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        entity = world.entities.get(proposal.actor_id)
        if not entity: return
        
        target: Vector2 = proposal.target
        world.move_entity(proposal.actor_id, target)
        
        # Action Delay Calculation
        from src.core.gameplay.attributes import speed_delay
        spd = entity.combat.spd
        # Road tiles grant a speed bonus
        if world.grid.is_road(target) or world.grid.is_bridge(target):
            spd = max(spd, int(spd * 1.3))
            
        delay = speed_delay(spd, "move", entity.interaction.interaction_speed)
        
        # Engagement Lock: fleeing costs extra delay
        # Only double delay if moving FURTHER AWAY from nearest hostile
        move_delay_mult = 1.0
        if entity.mind.navigation.engaged_ticks >= 2:
            old_pos = entity.spatial.pos
            # Find nearest hostile within range 5
            nearest_hostile = None
            min_dist = 999
            for oid in world.spatial_index.query_radius(old_pos, 5):
                other = world.entities.get(oid)
                if other and other.combat.alive:
                    # check faction (simplified)
                    if other.identity.faction != entity.identity.faction:
                        d = old_pos.manhattan(other.spatial.pos)
                        if d < min_dist:
                            min_dist = d
                            nearest_hostile = other
            
            if nearest_hostile:
                old_d = old_pos.manhattan(nearest_hostile.spatial.pos)
                new_d = target.manhattan(nearest_hostile.spatial.pos)
                if new_d > old_d: # Fleeing!
                    move_delay_mult = 2.0
                    entity.mind.navigation.engaged_ticks = 0
        
        entity.next_act_at += (delay * move_delay_mult)
        
        # Resource Costs
        entity.progression.stamina = max(0, entity.progression.stamina - 1)
        
        # Attribute Training
        from src.core.gameplay.attributes import train_attributes
        train_attributes(entity, "move")
