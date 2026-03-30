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

        if actor.inventory and actor.inventory.is_effectively_full:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Bag full → abandoning loot",
                intent_metadata={"loot_progress_reset": 0})

        key = (actor.spatial.pos.x, actor.spatial.pos.y)
        if key in snapshot.ground_items and snapshot.ground_items[key]:
            if actor.interaction.loot_progress < config.loot_duration:
                return AIState.LOOTING, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Looting... ({actor.interaction.loot_progress + 1}/{config.loot_duration})",
                    intent_metadata={"loot_progress_inc": 1})
            
            return AIState.LOOTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.LOOT, target=actor.spatial.pos,
                reason="Picking up loot")

        loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
        if loot_pos is not None:
            return AIState.LOOTING, propose_move_toward(
                actor, loot_pos, snapshot, "Moving to loot")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No more loot → wander",
            intent_metadata={"loot_progress_reset": 0})


class HarvestingHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot

        if should_flee(actor, ctx.config):
            return propose_retreat_home(ctx, "Low HP → abandoning harvest", 
                                       intent_metadata={"loot_progress_reset": 0})

        enemy = ctx.nearest_enemy()
        if enemy and actor.spatial.pos.manhattan(enemy.spatial.pos) <= 3:
            return AIState.HUNT, propose_move_toward(
                actor, enemy.spatial.pos, snapshot, "Enemy nearby → abandoning harvest",
                intent_metadata={"loot_progress_reset": 0})

        res = None
        for node in snapshot.resource_nodes:
            if node.spatial.pos == actor.spatial.pos and node.is_available:
                res = node
                break

        if res is None:
            res = find_nearby_resource(actor, snapshot, radius=8)
            if res is None:
                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason="No resources available → wander",
                    intent_metadata={"loot_progress_reset": 0})
            return AIState.HARVESTING, propose_move_toward(
                actor, res.spatial.pos, snapshot, f"Moving to {res.name}")

        if actor.interaction.loot_progress >= res.harvest_ticks:
            return AIState.HARVESTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.HARVEST, target=res.spatial.pos,
                reason=f"Harvesting {res.name} (Done)")
        
        return AIState.HARVESTING, ActionProposal(
            actor_id=actor.id, verb=ActionType.HARVEST, target=res.spatial.pos,
            reason=f"Harvesting {res.name} ({actor.interaction.loot_progress + 1}/{res.harvest_ticks})",
            intent_metadata={"loot_progress_inc": 1})


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
            # Metadata-driven recovery (AOA Stabilization)
            metadata = {
                "recover_gold": my_node.gold,
                "recover_items": list(my_node.items),
                "corpse_pop": my_node.node_id
            }
            return AIState.IDLE, ActionProposal(
                actor.id, ActionType.LOOT, 
                f"Recovered corpse #{my_node.node_id}", 
                intent_metadata=metadata
            )

        return AIState.RECOVER_CORPSE, propose_move_toward(
            actor, my_node.spatial.pos, snapshot, 
            f"Running to corpse at {my_node.spatial.pos}"
        )
