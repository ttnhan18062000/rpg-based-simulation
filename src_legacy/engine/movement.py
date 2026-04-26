# src/engine/movement.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any
from dataclasses import replace

from src_legacy.core.updates import EntityUpdate, NavigationUpdate

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState, EntityState

class MovementSystem:
    """ Authoritative handler for grid-based movement in V2. """

    @staticmethod
    def resolve_move(
        state_or_context: Any,
        entity: EntityState,
        target_pos: Tuple[float, float]
    ) -> Dict[int, EntityUpdate]:
        """
        Evaluate a move intent and produce an authoritative update dictionary.
        Matches parity with original 'src' MoveAction.
        """
        from src_legacy.engine.legality import LegalityServiceV2
        
        # 1. Subject Alive? (Parity with src Line 28)
        if not entity.active:
            return {entity.id: EntityUpdate(entity_id=entity.id)} # No-Op

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
        
        # 3.1 Sidestepping / Congestion Recovery (Phase 4)
        if not success and reason_code == "OCCUPANCY_VIOLATION":
            # Attempt to sidestep (orthogonal to intended move)
            dx = effective_target[0] - entity.position[0]
            dy = effective_target[1] - entity.position[1]
            
            sidesteps = []
            if dx != 0: # Moving horizontally, sidestep vertically
                sidesteps = [(entity.position[0], entity.position[1] + 1), (entity.position[0], entity.position[1] - 1)]
            elif dy != 0: # Moving vertically, sidestep horizontally
                sidesteps = [(entity.position[0] + 1, entity.position[1]), (entity.position[0] - 1, entity.position[1])]
            
            for side_tile in sidesteps:
                s_ok, s_reason = LegalityServiceV2.verify_occupancy(side_tile, state_or_context, ignore_entity_id=entity.id)
                if s_ok:
                    effective_target = side_tile
                    success = True
                    reason_code = None
                    break
            
            # 3.2 Yielding (Phase 4)
            if not success:
                occupant_id = LegalityServiceV2.get_occupant(effective_target, state_or_context, ignore_entity_id=entity.id)
                if occupant_id:
                    entities = getattr(state_or_context, 'entities', {})
                    occupant = entities.get(occupant_id)
                    if occupant:
                        my_prio = LegalityServiceV2.get_entity_priority(entity)
                        occ_prio = LegalityServiceV2.get_entity_priority(occupant)
                        
                        if my_prio > occ_prio:
                            # Try to find a yield tile for the occupant
                            # (Simple: try tiles adjacent to occupant that aren't the mover's position)
                            for dx in [-1, 0, 1]:
                                for dy in [-1, 0, 1]:
                                    if dx == 0 and dy == 0: continue
                                    yield_tile = (occupant.position[0] + dx, occupant.position[1] + dy)
                                    if yield_tile == entity.position: continue
                                    
                                    y_ok, y_reason = LegalityServiceV2.verify_occupancy(yield_tile, state_or_context, ignore_entity_id=occupant_id)
                                    if y_ok:
                                        # YIELD SUCCESS
                                        # Move occupant to yield tile
                                        yield_update = EntityUpdate(
                                            entity_id=occupant_id,
                                            new_position=yield_tile,
                                            moved_this_tick=True,
                                            navigation=NavigationUpdate(moved_recently_set=True, failure_reason="YIELDED")
                                        )
                                        # Note: We'll add this to the updates dict later
                                        success = True
                                        reason_code = None
                                        # The mover can now take the occupant's OLD position
                                        # effective_target is already set to occupant's position
                                        break
                                if success: break

        if not success:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason=reason_code)
            )}

        # 4. Opportunity Attack Check (Milestone 8 P0)
        # If actor was engaged before moving, trigger OAs on egress.
        engaged_hostiles = LegalityServiceV2.get_engaged_hostiles(entity, state_or_context)
        updates: Dict[int, EntityUpdate] = {}
        
        # Add yield update if exists
        if 'yield_update' in locals():
            updates[occupant_id] = yield_update

        if engaged_hostiles:
            from src_legacy.engine.combat import CombatResolutionSystem
            entities = getattr(state_or_context, 'entities', {})
            attackers = []
            for eid in engaged_hostiles:
                attacker = entities.get(eid)
                if attacker:
                    attackers.append(attacker)
            
            if attackers:
                combat_update = CombatResolutionSystem.resolve_multi_attack(
                    attackers, entity, state_or_context, is_opportunity_attack=True, is_lethal=False
                )
                # The actor takes the damage
                updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    combat=combat_update
                )

        # 5. Success Execution (Apply movement to actor)
        actor_up = updates.get(entity.id, EntityUpdate(entity_id=entity.id))
        updates[entity.id] = replace(
            actor_up,
            new_position=effective_target,
            moved_this_tick=True,
            readiness_delta=-10.0,
            navigation=NavigationUpdate(moved_recently_set=True, failure_reason=None)
        )
        
        return updates
