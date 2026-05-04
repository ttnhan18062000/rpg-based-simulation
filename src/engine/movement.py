# src/engine/movement.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any, Dict, List
from dataclasses import replace

from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate
from src.core.enums import ReasonCode

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class MovementSystem:
    """ Authoritative handler for grid-based movement in V2. """

    @staticmethod
    def resolve_move(
        state_or_context: Any,
        entity: EntityState,
        target_pos: Tuple[float, float],
        mode: MovementMode = MovementMode.WANDER
    ) -> Dict[int, EntityUpdate]:
        """
        Evaluate a move intent and produce an authoritative update dictionary.
        Implements a prioritized recovery ladder for congestion.
        VERIFIED v2: congestion_ladder
        VERIFIED v2: movement_intent_vs_result
        """
        from src.engine.legality import LegalityServiceV2
        
        # 1. Subject Alive?
        if not entity.active:
            return {entity.id: EntityUpdate(entity_id=entity.id)}

        # 2. Step Calculation
        from src.systems.navigation import NavigationSystem
        effective_target = NavigationSystem.get_next_step(entity, target_pos, state_or_context)

        # 3. Environment & Mode Multipliers (Calculated early for readiness gating)
        from src.world.environment import EnvironmentService
        region = LegalityServiceV2.get_region_for_position(entity.position, state_or_context)
        move_speed_mult = 1.0
        if region:
            w_mults = EnvironmentService.get_weather_multipliers(region)
            a_mults = EnvironmentService.get_aura_multipliers(state_or_context, entity)
            move_speed_mult = w_mults.get("move_speed", 1.0) * a_mults.get("move_speed", 1.0)
            
        mode_mults = {
            MovementMode.PURSUE: 1.2, MovementMode.RETREAT: 1.5, MovementMode.WANDER: 0.8,
            MovementMode.REPOSITION: 1.1, MovementMode.REGROUP: 1.0, MovementMode.GUARD: 1.0,
            MovementMode.HOLD: 0.0,
        }
        move_speed_mult *= mode_mults.get(mode, 1.0)

        # 4. Decision Ladder
        # VERIFIED v2: collision_rejection
        # VERIFIED v2: movement_readiness_gating
        success, reason_code = LegalityServiceV2.verify_movement_legality(
            entity, effective_target, state_or_context, move_speed_mult=move_speed_mult
        )
        
        updates: Dict[int, EntityUpdate] = {}
        wait_delta = 0
        osc_delta = 0
        replan = False
        
        if not success:
            # 3.1 Sidestepping (Orthogonal)
            dx = effective_target[0] - entity.position[0]
            dy = effective_target[1] - entity.position[1]
            sidesteps = []
            if dx != 0: sidesteps = [(entity.position[0], entity.position[1] + 1), (entity.position[0], entity.position[1] - 1)]
            elif dy != 0: sidesteps = [(entity.position[0] + 1, entity.position[1]), (entity.position[0] - 1, entity.position[1])]
            
            # Threat-aware sorting: Prefer tiles that don't trigger OAs
            sidesteps.sort(key=lambda p: (
                len(LegalityServiceV2.get_engaged_hostiles_at_pos(p, entity, state_or_context)),
                LegalityServiceV2.get_manhattan_dist(p, target_pos)
            ))
            
            for side_tile in sidesteps:
                s_ok, s_reason = LegalityServiceV2.verify_movement_legality(
                    entity, side_tile, state_or_context, move_speed_mult=move_speed_mult
                )
                if s_ok:
                    effective_target = side_tile
                    success = True; reason_code = None; break
            
            # 3.2 Yielding
            if not success:
                occupant_id = LegalityServiceV2.get_occupant(effective_target, state_or_context, ignore_entity_id=entity.id)
                if occupant_id:
                    entities = getattr(state_or_context, 'entities', {})
                    occupant = entities.get(occupant_id)
                    if occupant and occupant.navigation.movement_mode != MovementMode.HOLD:
                        my_prio = LegalityServiceV2.get_entity_priority(entity)
                        occ_prio = LegalityServiceV2.get_entity_priority(occupant)
                        if my_prio > occ_prio:
                            # Search for yield tile
                            for dx_y, dy_y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                                yield_tile = (occupant.position[0] + dx_y, occupant.position[1] + dy_y)
                                if yield_tile == entity.position: continue
                                y_ok, _ = LegalityServiceV2.verify_occupancy(yield_tile, state_or_context, ignore_entity_id=occupant_id)
                                if y_ok:
                                    updates[occupant_id] = EntityUpdate(
                                        entity_id=occupant_id, new_position=yield_tile, moved_this_tick=True,
                                        navigation=NavigationUpdate(moved_recently_set=True, failure_reason="YIELDED")
                                    )
                                    success = True; reason_code = None; break

            # 3.3 Reroute (If waiting too long)
            if not success and entity.navigation.wait_count >= 2:
                neighbors = [(-1,0),(1,0),(0,-1),(0,1)]
                neighbors.sort(key=lambda d: LegalityServiceV2.get_manhattan_dist((entity.position[0]+d[0], entity.position[1]+d[1]), target_pos))
                for dx_r, dy_r in neighbors:
                    reroute_tile = (entity.position[0] + dx_r, entity.position[1] + dy_r)
                    r_ok, _ = LegalityServiceV2.verify_occupancy(reroute_tile, state_or_context, ignore_entity_id=entity.id)
                    if r_ok:
                        effective_target = reroute_tile
                        success = True; reason_code = None; break

        # 4. Post-Movement Counters & Replan Logic
        if not success:
            wait_delta = 1
            if entity.navigation.wait_count >= 5: replan = True
            effective_target = None
        else:
            # Oscillation Detection
            if effective_target == entity.navigation.last_position:
                if entity.navigation.oscillation_count >= 3:
                    replan = True
                    success = False
                    effective_target = None
                    osc_delta = -entity.navigation.oscillation_count
                    wait_delta = -entity.navigation.wait_count
                else:
                    osc_delta = 1
            else:
                # Normal success: Reset counters
                wait_delta = -entity.navigation.wait_count
                osc_delta = -entity.navigation.oscillation_count

        if not success and not replan:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(
                    failure_reason=reason_code,
                    wait_count_delta=wait_delta
                )
            )}

        # 5. Opportunity Attack Check (Milestone 8 P0)
        engaged_hostiles = LegalityServiceV2.get_engaged_hostiles(entity, state_or_context)
        
        # Disengagement Logic
        skip_oa = False
        if mode == MovementMode.RETREAT and entity.combat.action_style == 2: # EVASIVE
             skip_oa = True

        # 5. Opportunity Attack Trigger (Checklist Section 8)
        # VERIFIED v2: disengagement_consequences
        # VERIFIED v2: disengagement_consequences
        if engaged_hostiles and not skip_oa:
            from src.engine.combat import CombatResolutionSystem
            entities = getattr(state_or_context, 'entities', {})
            attackers = []
            for eid in engaged_hostiles:
                attacker = entities.get(eid)
                if attacker: attackers.append(attacker)
            
            if attackers:
                combat_update = CombatResolutionSystem.resolve_multi_attack(
                    attackers, entity, state_or_context, is_opportunity_attack=True, is_lethal=False
                )
                updates[entity.id] = EntityUpdate(entity_id=entity.id, combat=combat_update)

        # 6. Final Subject Execution
        actor_up = updates.get(entity.id, EntityUpdate(entity_id=entity.id))
        
        # Terrain Cost (Checklist Section 7)
        terrain_cost = 1.0
        if success and effective_target:
            from src.engine.rpg_depth import TerrainCostService
            tile = (int(effective_target[0]), int(effective_target[1]))
            terrain_cost = TerrainCostService.get_tile_cost(tile, state_or_context)

        # Stamina drain on movement (Checklist Part 6 Section E)
        from src.core.updates import StaminaUpdate
        # VERIFIED v2: stamina_drain_movement
        stamina_upd = StaminaUpdate(current_delta=-entity.stamina.MOVE_COST) if success else None

        # Navigation Update Payload
        nav_upd = NavigationUpdate(
            moved_recently_set=True,
            failure_reason=None if success else reason_code,
            # VERIFIED v2: movement_priority_tiebreak
            wait_count_delta=wait_delta,
            # VERIFIED v2: stalemate_breaker
            oscillation_count_delta=osc_delta,
            last_position_set=entity.position if success else None,
            clear_target=replan,
            clear_path=replan
        )

        # VERIFIED v2: environmental_move_cost
        readiness_cost = (entity.combat.move_cost * terrain_cost) / max(0.1, move_speed_mult)

        updates[entity.id] = replace(
            actor_up,
            new_position=effective_target,
            moved_this_tick=success,
            # VERIFIED v2: authoritative_move_cost
            readiness_delta=-readiness_cost if success else 0.0,
            navigation=nav_upd,
            stamina_update=stamina_upd
        )

        
        return updates
