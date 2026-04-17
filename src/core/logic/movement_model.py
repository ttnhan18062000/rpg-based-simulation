"""MovementModel — Centralized logic for intention-driven, congestion-aware movement.

[Milestone 3]
- Route-level planning vs Local-step selection.
- Congestion handling: WAIT, YIELD, SIDESTEP, REROUTE.
- Occupation rules: Hard one-unit-per-tile, no ally pass-through.
- Tie-breaking: Intention priority (RETREAT > PURSUIT), next_act_at, entity_id.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.core.models.enums import ActionType, MovementIntention
from src.core.models import Vector2
from src.actions.base import ActionProposal, NavigationUpdate
from src.core.models.reason_codes import ActionReason, ReasonCode

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot

logger = logging.getLogger(__name__)

# Intention priority for yielding (higher is more likely to win tile access)
INTENTION_PRIORITY = {
    MovementIntention.RETREAT: 100,
    MovementIntention.PURSUIT: 50,
    MovementIntention.INTERCEPT: 40,
    MovementIntention.REPOSITION: 30,
    MovementIntention.GUARD: 20,
    MovementIntention.REGROUP: 10,
    MovementIntention.NONE: 0,
}

class MovementModel:
    """Stateless service for movement coordination."""

    @staticmethod
    def plan_or_step(
        ctx: AIContext, 
        target_pos: Vector2, 
        intention: MovementIntention, 
        reason: ActionReason | str
    ) -> ActionProposal:
        """Main entry point for AI to propose movement."""
        actor = ctx.actor
        snapshot = ctx.snapshot
        nav = actor.mind.navigation

        # 1. Update Intention (Persistence/Commitment)
        # In Milestone 3, we stay committed to the intention until the target changes significantly
        # or the AI state handler explicitly overrides it.
        
        # 2. Planning Layer: Get or Rebuild Route
        route = MovementModel.plan_route(ctx, target_pos)
        if not route:
            reason_obj = ActionReason(code=ReasonCode.PATH_NOT_FOUND)
            return ActionProposal(
                actor_id=actor.id, 
                verb=ActionType.REST, 
                reason=reason_obj,
                updates=[NavigationUpdate(intention=intention, blocked_ticks=0, reason=reason_obj)]
            )

        # 3. Execution Layer: Local Step Selection
        use_v2 = ctx.config.overhaul_features.get("use_movement_model_v2", True) if ctx.config else True
        if use_v2:
            step, congestion_res = MovementModel.select_step(ctx, route, intention)
        else:
            # Simple legacy-style step: just try the first tile of the route
            step = route[0]
            if MovementModel._get_blocker(ctx, step):
                step = actor.spatial.pos
                congestion_res = ActionReason(code=ReasonCode.LEGACY_FALLBACK, metadata={"detail": "Tile Blocked"})
            else:
                congestion_res = None

        updates = [NavigationUpdate(
            intention=intention,
            cached_path=route,
            target_pos=target_pos,
            blocked_ticks=nav.blocked_ticks + 1 if congestion_res else 0,
            reason=congestion_res or ActionReason(code=ReasonCode.ADVANCING, metadata={"target": str(target_pos)})
        )]

        if step == actor.spatial.pos:
            # We are waiting or stuck
            return ActionProposal(
                actor_id=actor.id,
                verb=ActionType.REST,
                reason=congestion_res or ActionReason(code=ReasonCode.WAITING),
                updates=updates
            )

        # Combine reason with congestion info if any
        return ActionProposal(
            actor_id=actor.id,
            verb=ActionType.MOVE,
            target=step,
            reason=congestion_res or reason,
            updates=updates
        )

    @staticmethod
    def plan_route(ctx: AIContext, target: Vector2) -> list[Vector2] | None:
        """Route-level planning with commitment logic."""
        actor = ctx.actor
        nav = actor.mind.navigation
        
        # Commitment Check: If we have a cached path toward this target, keep it
        if (nav.cached_path and nav.cached_path_target == target 
                and len(nav.cached_path) > 0 
                and nav.cached_path[0] == actor.spatial.pos
                and nav.blocked_ticks < 2): # [Milestone 3] 2-tick stuck threshold
            
            # Verify the next step is still walkable (grid-wise, ignore entities)
            if len(nav.cached_path) > 1:
                next_step = nav.cached_path[1]
                if ctx.snapshot.grid.is_walkable(next_step):
                    return nav.cached_path
        
        # Replan
        from src.ai.pathfinding import Pathfinder
        pf = Pathfinder(ctx.snapshot.grid)
        # Note: In Milestone 3, planning ignores entities to find the "ideal" route.
        # Local step selection handles the entities.
        path = pf.find_path(actor.spatial.pos, target)
        return path

    @staticmethod
    def select_step(
        ctx: AIContext, 
        route: list[Vector2], 
        intention: MovementIntention
    ) -> tuple[Vector2, ActionReason | None]:
        """Local step selection with congestion awareness."""
        actor = ctx.actor
        if not route:
            return actor.spatial.pos, ActionReason(code=ReasonCode.LEGACY_FALLBACK, metadata={"detail": "Arrived/No steps"})

        next_ideal = route[0]
        
        # Check if next_ideal is occupied BY AN ENTITY (Pillar 6 O(1) Check)
        blocker_id = MovementModel._get_blocker(ctx, next_ideal)
        if not blocker_id:
            return next_ideal, None

        # Congestion Response
        blocker = ctx.snapshot.entities.get(blocker_id)
        if blocker:
            # 1. Yielding Priority [Milestone 3]
            if MovementModel._should_yield(actor, blocker, intention):
                return actor.spatial.pos, ActionReason(code=ReasonCode.YIELDING, metadata={"blocker_id": blocker_id})

            # 2. Sidestep [Milestone 3]
            sidestep = MovementModel._find_sidestep(ctx, next_ideal)
            if sidestep:
                return sidestep, ActionReason(code=ReasonCode.SIDESTEPPING)

        return actor.spatial.pos, ActionReason(code=ReasonCode.WAITING)

    @staticmethod
    def _get_blocker(ctx: AIContext, pos: Vector2) -> int | None:
        """Return ID of entity at pos, if any."""
        # AOA Phase 6: Use spatial index or world lookup
        # In AI Context, we use the snapshot's spatial structure
        nearby = ctx.snapshot.nearby_entity_ids(pos.x, pos.y, 0)
        for eid in nearby:
            e = ctx.snapshot.entities.get(eid)
            if e and e.spatial.pos == pos and e.combat.alive:
                return eid
        return None

    @staticmethod
    def _should_yield(actor: Entity, blocker: Entity, actor_intent: MovementIntention) -> bool:
        """True if actor should yield tile to blocker."""
        # 1. Intention priority (RETREAT > PURSUIT)
        blocker_intent = blocker.mind.navigation.intention
        p1 = INTENTION_PRIORITY.get(actor_intent, 0)
        p2 = INTENTION_PRIORITY.get(blocker_intent, 0)
        
        if p1 < p2: return True
        if p1 > p2: return False
        
        # 2. next_act_at (earlier wins)
        if actor.next_act_at > blocker.next_act_at: return True
        if actor.next_act_at < blocker.next_act_at: return False
        
        # 3. entity_id (lower wins)
        return actor.id > blocker.id

    @staticmethod
    def _find_sidestep(ctx: AIContext, target_pos: Vector2) -> Vector2 | None:
        """Find a cardinal neighbor that is walkable and unoccupied."""
        actor_pos = ctx.actor.spatial.pos
        # Cardinal neighbors of the CURRENT position
        directions = [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]
        
        best_sidestep = None
        min_dist = float("inf")
        
        for d in directions:
            cand = actor_pos + d
            if cand == target_pos: continue # Already known blocked
            
            if not ctx.snapshot.grid.is_walkable(cand): continue
            if MovementModel._get_blocker(ctx, cand): continue
            
            # Pick step that keeps us closest to ideal next step or target
            dist = cand.manhattan(target_pos)
            if dist < min_dist:
                min_dist = dist
                best_sidestep = cand
        
        return best_sidestep
