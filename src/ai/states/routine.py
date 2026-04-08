from __future__ import annotations
from src.core.models.enums import AIState, ActionType
from src.actions.base import ActionProposal, RoutineUpdate
from src.ai.states.base import StateHandler, AIContext

class SleepingHandler(StateHandler):
    """Logic for entities while they are asleep."""
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor = ctx.actor
        rou = actor.mind.routine
        
        # If fully rested, wake up
        if rou.sleep_debt <= 0.05:
            return AIState.IDLE, ActionProposal(
                actor_id=actor.id,
                verb=ActionType.REST,
                reason="Fully rested, waking up",
                updates=[RoutineUpdate(is_sleeping=False)]
            )
        
        # Continue sleeping, recovery is handled authoritatively in ActionSystem
        # but we can propose a small boost here if desired, or just stay in state.
        return AIState.SLEEPING, ActionProposal(
            actor_id=actor.id,
            verb=ActionType.SLEEP,
            reason="Sleeping...",
            updates=[] # Authoritative decay handles recovery
        )

class EatingHandler(StateHandler):
    """Logic for entities while they are eating."""
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor = ctx.actor
        rou = actor.mind.routine
        
        # 1. Check if satiated
        if rou.hunger_level <= 0.1:
            return AIState.IDLE, ActionProposal(
                actor_id=actor.id,
                verb=ActionType.REST,
                reason="Satiated, finished eating",
                updates=[]
            )
        
        # 2. Find food in inventory
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        food_item = None
        for item_id in actor.inventory.items:
            template = ITEM_REGISTRY.get(item_id)
            if template and template.hunger_reduction > 0:
                food_item = item_id
                break
        
        if not food_item:
            return AIState.IDLE, ActionProposal(
                actor_id=actor.id,
                verb=ActionType.REST,
                reason="No more food in inventory",
                updates=[]
            )

        # 3. Propose EAT action
        # Note: Hunger reduction value is fetched from the item template inside EatAction.apply
        return AIState.EATING, ActionProposal(
            actor_id=actor.id,
            verb=ActionType.EAT,
            reason=f"Eating {food_item}",
            metadata={"item_id": food_item},
            updates=[] # Hunger reduction is handled by EatAction.apply emitting RoutineUpdate
        )
