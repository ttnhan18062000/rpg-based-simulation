"""Stateless handler for repair."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class RepairAction:
    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        actor = world.entities.get(proposal.actor_id)
        if not actor or not actor.combat.alive: return False
        if actor.stats.progression.gold < 10.0: return False
        target_b = next((b for b in world.buildings if b.building_id == proposal.target), None)
        if not target_b: return False
        if actor.spatial.pos.manhattan(target_b.spatial.pos) > 1: return False
        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        actor = world.entities.get(proposal.actor_id)
        target_b = next((b for b in world.buildings if b.building_id == proposal.target), None)
        if actor and target_b:
            actor.stats.progression.gold -= 10.0
            target_b.repair(50.0)
            logger.info(f"Tick {world.tick}: {actor.kind} #{actor.id} repaired {target_b.name}")
            actor.stats.progression.stamina = max(0, actor.stats.progression.stamina - 5)
            from src.core.gameplay.attributes import speed_delay
            actor.next_act_at += speed_delay(actor.stats.combat.spd, "building")
