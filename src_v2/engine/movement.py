# src_v2/engine/movement.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any

from src_v2.core.updates import EntityUpdate, NavigationUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState

class MovementSystem:
    """ Authoritative handler for grid-based movement in V2. """

    @staticmethod
    def resolve_move(
        state_or_context: Any,
        entity: EntityState,
        target_pos: Tuple[float, float]
    ) -> EntityUpdate:
        """
        Evaluate a move intent and produce an authoritative update.
        Matches parity with original 'src' MoveAction.
        """
        from src_v2.engine.legality import LegalityServiceV2
        
        # 1. Subject Alive? (Parity with src Line 28)
        if not entity.active:
            return EntityUpdate(entity_id=entity.id) # No-Op

        # 2. Manhattan Adjacency?
        dist = LegalityServiceV2.get_manhattan_dist(entity.position, target_pos)
        
        effective_target = target_pos
        if dist > 1:
            dx = target_pos[0] - entity.position[0]
            dy = target_pos[1] - entity.position[1]
            if abs(dx) > abs(dy):
                effective_target = (entity.position[0] + (1 if dx > 0 else -1), entity.position[1])
            else:
                effective_target = (entity.position[0], entity.position[1] + (1 if dy > 0 else -1))

        # 3. Legality Check (Terrain & Occupancy)
        success, reason_code = LegalityServiceV2.verify_occupancy(effective_target, state_or_context, ignore_entity_id=entity.id)
        
        if not success:
            return EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason=reason_code)
            )

        # 4. Opportunity Attack Check (Milestone 8 P0)
        # If actor was engaged before moving, trigger OAs on egress.
        engaged_hostiles = LegalityServiceV2.get_engaged_hostiles(entity, state_or_context)
        combat_update = None
        if engaged_hostiles:
            from src_v2.engine.combat import CombatReactionSystem
            # P0: For now, we resolve the first hostile's OA and apply it.
            entities = getattr(state_or_context, 'entities', {})
            attacker = entities.get(engaged_hostiles[0])
            if attacker:
                combat_update = CombatReactionSystem.resolve_opportunity_attack(attacker, entity)

        # 5. Success Execution
        return EntityUpdate(
            entity_id=entity.id,
            new_position=effective_target,
            moved_this_tick=True,
            readiness_delta=-10.0, # Adjusted for loop integrity
            combat=combat_update,
            navigation=NavigationUpdate(moved_recently_set=True, failure_reason=None)
        )
