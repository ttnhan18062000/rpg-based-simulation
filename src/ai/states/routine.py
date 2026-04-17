from __future__ import annotations
from src.core.models.enums import AIState, ActionType, MovementIntention
from src.actions.base import ActionProposal, RoutineUpdate
from src.ai.states.base import StateHandler, AIContext

class SleepingHandler(StateHandler):
    """Logic for entities while they are asleep."""
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor = ctx.actor
        rou = actor.mind.routine
        
        # 1. If fully rested, wake up
        if rou.sleep_debt <= 0.05:
            return AIState.IDLE, ActionProposal(
                actor_id=actor.id,
                verb=ActionType.REST,
                reason="Fully rested, waking up",
                updates=[RoutineUpdate(is_sleeping=False)]
            )
        
        # 2. Prefer sleeping at home if a home exists [PHASE 3]
        target_pos = actor.spatial.home_pos
        if not target_pos:
            from src.core.models.enums import AttachmentKind
            attachment = next((a for a in actor.mind.place_attachments if a.kind == AttachmentKind.HOME), None)
            if attachment:
                target_pos = attachment.location_pos

        if target_pos:
            dist = actor.spatial.pos.manhattan(target_pos)
            if dist > 0:
                # We need to get home first
                from src.ai.states.base import propose_move_toward
                return AIState.SLEEPING, propose_move_toward(
                    ctx, target_pos, 
                    "Heading home to sleep", MovementIntention.NONE,
                    updates=[RoutineUpdate(is_sleeping=False)] # Wake up to walk
                )
            else:
                # Arrived at home, make sure we are marked as sleeping for recovery
                if not rou.is_sleeping:
                    return AIState.SLEEPING, ActionProposal(
                        actor_id=actor.id,
                        verb=ActionType.SLEEP,
                        reason="Arrived home, falling asleep",
                        updates=[RoutineUpdate(is_sleeping=True)]
                    )

        # 3. Continue sleeping (either at home or wherever we were if homeless)
        return AIState.SLEEPING, ActionProposal(
            actor_id=actor.id,
            verb=ActionType.SLEEP,
            reason="Sleeping...",
            updates=[RoutineUpdate(is_sleeping=True)]
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
