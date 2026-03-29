from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState
from src.core.entities.entity import Entity, Vector2
from src.ai.states.base import (
    AIContext, StateHandler, clear_dead_from_memory, 
    propose_move_toward, should_flee, propose_retreat_home
)


def find_nearby_resource(actor: Entity, snapshot, radius: int = 6):
    """Find the nearest available resource node within radius."""
    best = None
    best_dist = radius + 1
    for node in snapshot.resource_nodes:
        if not node.is_available:
            continue
        dist = actor.spatial.pos.manhattan(node.spatial.pos)
        if dist < best_dist:
            best_dist = dist
            best = node
    return best


class LootingHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        if actor.inventory and actor.inventory.is_effectively_full:
            actor.loot_progress = 0
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Bag full → abandoning loot")

        key = (actor.spatial.pos.x, actor.spatial.pos.y)
        if key in snapshot.ground_items and snapshot.ground_items[key]:
            if actor.loot_progress < config.loot_duration:
                actor.loot_progress += 1
                return AIState.LOOTING, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Looting... ({actor.loot_progress}/{config.loot_duration})")
            actor.loot_progress = 0
            return AIState.LOOTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.LOOT, target=actor.spatial.pos,
                reason="Picking up loot")

        actor.loot_progress = 0
        loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
        if loot_pos is not None:
            return AIState.LOOTING, propose_move_toward(
                actor, loot_pos, snapshot, "Moving to loot")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No more loot → wander")


class HarvestingHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot

        if should_flee(actor, ctx.config):
            actor.loot_progress = 0
            return propose_retreat_home(ctx, "Low HP → abandoning harvest")

        enemy = ctx.nearest_enemy()
        if enemy and actor.spatial.pos.manhattan(enemy.spatial.pos) <= 3:
            actor.loot_progress = 0
            return AIState.HUNT, propose_move_toward(
                actor, enemy.spatial.pos, snapshot, "Enemy nearby → abandoning harvest")

        res = None
        for node in snapshot.resource_nodes:
            if node.spatial.pos == actor.spatial.pos and node.is_available:
                res = node
                break

        if res is None:
            res = find_nearby_resource(actor, snapshot, radius=8)
            if res is None:
                actor.loot_progress = 0
                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason="No resources available → wander")
            return AIState.HARVESTING, propose_move_toward(
                actor, res.spatial.pos, snapshot, f"Moving to {res.name}")

        actor.loot_progress += 1
        if actor.loot_progress >= res.harvest_ticks:
            actor.loot_progress = 0
            return AIState.HARVESTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.HARVEST, target=res.spatial.pos,
                reason=f"Harvested {res.name} → got {res.yields_item}")
        return AIState.HARVESTING, ActionProposal(
            actor_id=actor.id, verb=ActionType.HARVEST, target=res.spatial.pos,
            reason=f"Harvesting {res.name} ({actor.loot_progress}/{res.harvest_ticks})")


class CorpseRunHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        my_node = None
        nodes = getattr(snapshot, "corpse_nodes", {})
        for node in nodes.values():
            if node.entity_id == actor.id:
                my_node = node
                break
        
        if not my_node:
            return AIState.WANDER, ActionProposal(actor.id, ActionType.REST, "Corpse gone")
            
        if actor.spatial.pos.manhattan(my_node.spatial.pos) == 0:
            actor.stats.progression.gold += my_node.gold
            if actor.inventory:
                for iid in my_node.items:
                    actor.inventory.add_item(iid)
            
            if hasattr(snapshot, "corpse_nodes"):
                snapshot.corpse_nodes.pop(my_node.node_id, None)
            
            return AIState.IDLE, ActionProposal(actor.id, ActionType.LOOT, f"Recovered corpse #{my_node.node_id}")

        return AIState.RECOVER_CORPSE, propose_move_toward(actor, my_node.spatial.pos, snapshot, f"Running to corpse at {my_node.spatial.pos}")
