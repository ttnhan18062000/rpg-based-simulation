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
        
        # If no longer hungry, stop eating
        if rou.hunger_level <= 0.1:
            return AIState.IDLE, ActionProposal(
                actor_id=actor.id,
                verb=ActionType.REST,
                reason="Satiated, finished eating",
                updates=[]
            )
        
        # Propose immediate hunger reduction (eating is faster than sleeping)
        return AIState.EATING, ActionProposal(
            actor_id=actor.id,
            verb=ActionType.EAT,
            reason="Eating...",
            updates=[RoutineUpdate(hunger_delta=-0.3)]
        )
