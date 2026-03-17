"""Stateless handler for repair."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal

if TYPE_CHECKING:
    from src.core.world_state import WorldState

logger = logging.getLogger(__name__)

class RepairAction:
    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        actor = world.entities.get(proposal.actor_id)
        if not actor or not actor.alive: return False
        if actor.stats.gold < 10.0: return False
        target_b = next((b for b in world.buildings if b.building_id == proposal.target), None)
        if not target_b: return False
        if actor.pos.manhattan(target_b.pos) > 1: return False
        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        actor = world.entities.get(proposal.actor_id)
        target_b = next((b for b in world.buildings if b.building_id == proposal.target), None)
        if actor and target_b:
            actor.stats.gold -= 10.0
            target_b.repair(50.0)
            logger.info(f"Tick {world.tick}: {actor.kind} #{actor.id} repaired {target_b.name}")
            actor.stats.stamina = max(0, actor.stats.stamina - 5)
            from src.core.attributes import speed_delay
            actor.next_act_at += speed_delay(actor.effective_spd(), "building")
