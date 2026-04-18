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

from src.core.logic.legality_service import LegalityService

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
        reason: ActionReason
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
                congestion_res = ActionReason(code=ReasonCode.CONGESTION, metadata={"detail": "Tile Blocked"})
            else:
                congestion_res = None
        
        # 4. Oscillation Detection [Milestone 3]
        is_oscillating = MovementModel._detect_oscillation(ctx)
        osc_count = nav.oscillation_counter + 1 if is_oscillating else 0
        
        if osc_count >= 2: # [Milestone 3] 2-cycle threshold
            # Force WAIT to break the rhythm
            step = actor.spatial.pos
            congestion_res = ActionReason(code=ReasonCode.WAITING, metadata={"detail": "Oscillation Suppressed"})
            osc_count = 0 # Reset after suppression

        updates = [NavigationUpdate(
            intention=intention,
            cached_path=route,
            target_pos=target_pos,
            blocked_ticks=nav.blocked_ticks + 1 if congestion_res else 0,
            oscillation_counter=osc_count,
            last_route_hash=MovementModel._get_route_hash(route),
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
        """Route-level planning with commitment logic and hysteresis."""
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
        path = pf.find_path(actor.spatial.pos, target)
        
        # Hysteresis Check [Milestone 3]: Prevent flip-flopping between near-equal routes
        if path and nav.last_route_hash and nav.blocked_ticks < 2:
            new_hash = MovementModel._get_route_hash(path)
            if new_hash != nav.last_route_hash:
                # If we switched routes, check improvement
                old_len = len(nav.cached_path) if nav.cached_path else 999
                new_len = len(path)
                if new_len >= old_len - 2: # Improvement must be > 2 tiles to justify switch
                    # Stick to old route if improvement is minor
                    if nav.cached_path and nav.cached_path_target == target:
                        return nav.cached_path

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
            return actor.spatial.pos, ActionReason(code=ReasonCode.TARGET_REACHED, metadata={"detail": "Arrived/No steps"})

        next_ideal = route[0]
        
        # Check if next_ideal is occupied BY AN ENTITY (Pillar 6 O(1) Check)
        blocker_id = LegalityService.get_occupant_id(next_ideal, ctx.snapshot)
        if not blocker_id:
            return next_ideal, None

        # Congestion Response
        blocker = ctx.snapshot.entities.get(blocker_id)
        if blocker:
            # 1. Yielding Priority [Milestone 3]
            # RETREAT always forces lower-priority (PURSUIT/etc) to yield
            if MovementModel._should_yield(actor, blocker, intention):
                return actor.spatial.pos, ActionReason(code=ReasonCode.YIELDING, metadata={"blocker_id": blocker_id})

            # 2. Sidestep [Milestone 3]
            # High-priority intentions (RETREAT/PURSUIT) are more aggressive about sidestepping
            sidestep = MovementModel._find_sidestep(ctx, next_ideal)
            if sidestep:
                return sidestep, ActionReason(code=ReasonCode.SIDESTEPPING)

        return actor.spatial.pos, ActionReason(code=ReasonCode.WAITING)

    @staticmethod
    def _get_blocker(ctx: AIContext, pos: Vector2) -> int | None:
        """DEPRECATED: Use LegalityService.get_occupant_id."""
        return LegalityService.get_occupant_id(pos, ctx.snapshot)

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
        """Find a cardinal neighbor that is walkable and unoccupied with safety heuristics."""
        actor = ctx.actor
        actor_pos = actor.spatial.pos
        # Cardinal neighbors of the CURRENT position
        directions = [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]
        
        best_sidestep = None
        min_dist = float("inf")
        
        from src.core.logic.legality_service import LegalityService
        
        for d in directions:
            cand = actor_pos + d
            if cand == target_pos: continue # Already known blocked
            
            if not ctx.snapshot.grid.is_walkable(cand): continue
            if LegalityService.get_occupant_id(cand, ctx.snapshot): continue
            
            # [Milestone 3] Safety Heuristic: No yielding into danger
            # Danger check: Is cand closer to any known hostile threat?
            # We check if it reduces distance to the NEAREST visible hostile compared to current pos.
            if actor.mind.navigation.intention != MovementIntention.RETREAT:
                # Find nearest hostile threat from actor's memory
                threats = [
                    m.pos for m in actor.mind.perception.entity_memory.values()
                    if (m.threat.overall if not isinstance(m.threat, dict) else m.threat.get("overall", 0)) > 0.3
                ]
                if threats:
                    nearest_threat = min(threats, key=lambda p: LegalityService.get_distance(actor_pos, p))
                    old_dist = LegalityService.get_distance(actor_pos, nearest_threat)
                    new_dist = LegalityService.get_distance(cand, nearest_threat)
                    # If it gets us closer to a threat and we aren't in pursuit-mode with that target, avoid it
                    if new_dist < old_dist and actor.mind.navigation.engagement_target_id is None:
                        continue

            # Pick step that keeps us closest to ideal next step or target
            dist = LegalityService.get_distance(cand, target_pos)
            if dist < min_dist:
                min_dist = dist
                best_sidestep = cand
        
        return best_sidestep

    @staticmethod
    def _detect_oscillation(ctx: AIContext) -> bool:
        """Detect A-B-A patterns in recent move history [Milestone 3]."""
        history = ctx.actor.mind.navigation.pos_history
        if len(history) < 4: return False
        
        # history[-1] is current pos (or last move)
        # Check for A -> B -> A pattern
        # history: [..., P3, P2, P1, P0] where P0 is most recent
        p0 = history[-1]
        p1 = history[-2]
        p2 = history[-3]
        p3 = history[-4]
        
        # A-B-A check: current pos == two steps ago
        if p0 == p2 and p1 == p3:
            return True
        return False

    @staticmethod
    def _get_route_hash(route: list[Vector2] | None) -> str | None:
        """Generate a stable hash for a route to detect flip-flopping."""
        if not route: return None
        import hashlib
        route_str = "".join(f"({v.x},{v.y})" for v in route[:5]) # Sample first 5 steps
        return hashlib.md5(route_str.encode()).hexdigest()
