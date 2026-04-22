from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Tuple
from dataclasses import replace

from src_v2.core.updates import EntityUpdate, TaskUpdate, NavigationUpdate
from src_v2.engine.legality import LegalityServiceV2

if TYPE_CHECKING:
    from src_v2.core.state import EntityState, AuthoritativeState

class TacticalDecisionSystem:
    """
    Authoritative logic for bounded local tactical decisions.
    Responsible for target selection, engagement commitment, and anti-stalemate.
    """

    @staticmethod
    def evaluate_entity_intent(
        state: AuthoritativeState,
        entity: EntityState
    ) -> EntityUpdate:
        """
        Determines the next tactical intent for an entity.
        Bounded to local visibility and immediate combat state.
        """
        # 0. Retreat Logic (GAP-T03)
        # If HP is critically low, retreat to town or safe spot
        if entity.combat.hp < entity.combat.max_hp * 0.2:
            # Simple retreat: Move to (0,0) - assuming town is at origin for this baseline
            return EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(target_set=(0.0, 0.0)),
                task=TaskUpdate(
                    work_kind_set="ENTITY_MOVE",
                    payload_set={"target_position": (0.0, 0.0), "reason": "RETREAT"}
                )
            )

        # 1. Get hostiles in visibility range
        from src_v2.engine.domain_logic import SimulationDomainLogic
        neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
        
        hostiles = [
            n for _, n in neighbors 
            if n.identity.faction != entity.identity.faction and n.combat.alive
        ]
        
        if not hostiles:
            return EntityUpdate(entity_id=entity.id)

        # 2. Stickiness / Target Lock (GAP-T04)
        current_target_id = entity.task.payload.get("target_id")
        target = None
        
        if current_target_id is not None:
            # Check if current target is still viable (alive and in range 15)
            potential_target = state.entities.get(current_target_id)
            if potential_target and potential_target.combat.alive:
                dist = abs(potential_target.position[0] - entity.position[0]) + abs(potential_target.position[1] - entity.position[1])
                if dist <= 15.0: # Stickiness threshold (slightly larger than visibility)
                    target = potential_target

        if target is None:
            # 2.1 Target Selection (GAP-T01)
            # Criteria: Lowest HP > Closest > Lowest ID (Tie-breaker)
            def target_score(h: EntityState) -> Tuple[int, float, int]:
                dist = abs(h.position[0] - entity.position[0]) + abs(h.position[1] - entity.position[1])
                return (h.combat.hp, dist, h.id)

            hostiles.sort(key=target_score)
            target = hostiles[0]

        # 3. Decision: Attack vs Pursuit
        dist_to_target = abs(target.position[0] - entity.position[0]) + abs(target.position[1] - entity.position[1])
        
        # 4. Anti-Stalemate (GAP-T05)
        stale_ticks = entity.task.payload.get("stale_ticks", 0)
        
        # If we've been trying to reach/attack this target for too long without progress
        # (For this baseline, we use a simple counter; in real engine we'd check HP delta)
        if stale_ticks > 10:
             # Force target switch by ignoring this one or retreating
             return EntityUpdate(
                 entity_id=entity.id,
                 navigation=NavigationUpdate(target_set=(0.0, 0.0)),
                 task=TaskUpdate(
                     work_kind_set="ENTITY_MOVE",
                     payload_set={"target_position": (0.0, 0.0), "reason": "STALEMATE_BREAK"}
                 )
             )

        if dist_to_target <= entity.combat.range:
            # LEGAL ATTACK
            return EntityUpdate(
                entity_id=entity.id,
                task=TaskUpdate(
                    work_kind_set="ENTITY_ACT",
                    payload_set={
                        "action": "ATTACK", 
                        "target_id": target.id,
                        "stale_ticks": stale_ticks + 1
                    }
                )
            )
        else:
            # PURSUIT (Move towards target)
            return EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(target_set=target.position),
                task=TaskUpdate(
                    work_kind_set="ENTITY_MOVE",
                    payload_set={
                        "target_position": target.position, 
                        "target_id": target.id,
                        "stale_ticks": stale_ticks + 1
                    }
                )
            )

    @staticmethod
    def select_best_target(
        attacker: EntityState,
        candidates: List[EntityState]
    ) -> Optional[EntityState]:
        """
        Public helper for deterministic target selection.
        Matches legacy 'TacticalEvaluator.SelectTarget'.
        """
        if not candidates:
            return None
            
        def target_score(h: EntityState) -> Tuple[int, float, int]:
            dist = abs(h.position[0] - attacker.position[0]) + abs(h.position[1] - attacker.position[1])
            return (h.combat.hp, dist, h.id)
            
        sorted_candidates = sorted(candidates, key=target_score)
        return sorted_candidates[0]
