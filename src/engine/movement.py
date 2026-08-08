# Compliance IDs: AUTH-022, COMBAT-008, COMBAT-009, COMBAT-011, COMBAT-014, COMBAT-015, COMBAT-021, COMBAT-024, COMBAT-025, COMBAT-044, COMBAT-056, COMBAT-057, COMBAT-058, COMBAT-059, COMBAT-067, COMBAT-068, COMBAT-069, PROG-090, PROG-091, RES-028, SOC-049, STRAT-041, STRAT-042, STRAT-055, STRAT-057, STRAT-093, WORLD-023, WORLD-024, WORLD-026, WORLD-033, WORLD-034, WORLD-069, WORLD-071, WORLD-088, WORLD-094, WORLD-095, WORLD-096, WORLD-098, WORLD-101, WORLD-119, WORLD-139, WORLD-140, WORLD-141, WORLD-142, WORLD-143, WORLD-144, WORLD-145, WORLD-146, WORLD-147, WORLD-148, WORLD-149, WORLD-150, WORLD-151, WORLD-152, WORLD-153, WORLD-154, WORLD-155, WORLD-156, WORLD-157, WORLD-158, WORLD-159, WORLD-161, WORLD-162, WORLD-163, WORLD-165, WORLD-166, WORLD-167, WORLD-168, WORLD-169, WORLD-174, WORLD-175, WORLD-176, WORLD-177, WORLD-178, WORLD-179, WORLD-180, WORLD-181, WORLD-182, WORLD-183, WORLD-184, WORLD-185, WORLD-186, WORLD-187, WORLD-188, WORLD-189, WORLD-190, WORLD-191, WORLD-192, WORLD-193, WORLD-194, WORLD-195, WORLD-196, WORLD-197, WORLD-198, WORLD-199, WORLD-200, WORLD-201, WORLD-204, WORLD-205, WORLD-206, WORLD-221, WORLD-230, WORLD-231, WORLD-232, WORLD-233, WORLD-234, WORLD-235, WORLD-236, WORLD-237, WORLD-238, WORLD-239, WORLD-240, WORLD-241, WORLD-242, WORLD-243, WORLD-244, WORLD-245, WORLD-246, WORLD-249
# Compliance IDs: COMB-009, COMB-010, COMB-011, COMB-012, COMB-188, COMB-189, COMB-190, COMB-199, COMB-201, COMB-202, COMB-203, COMB-204, COMB-205, COMB-206, COMB-207, COMB-208, COMB-211, COMB-212, COMB-213, COMB-214, COMB-219, COMB-220, COMB-221, COMB-222, COMB-223, COMB-224, COMB-225, COMB-226, COMB-231, COMB-232, COMB-233, COMB-234, COMB-235, COMB-236, COMB-238, COMB-239, COMB-240, COMB-241, COMB-242, COMB-243, COMB-272, COMB-273
# src/engine/movement.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any, Dict, List
from dataclasses import replace

from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate, StaminaUpdate, LifecycleUpdate
from src.core.enums import ReasonCode

from src.engine.legality import LegalityServiceV2
from src.systems.world_systems.navigation import NavigationSystem
from src.world.environment import EnvironmentService
from src.engine.combat import CombatResolutionSystem
from src.engine.rpg_depth import TerrainCostService

from src.engine.movement_cache import MovementPlanKey, MovementPlan

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
        Logic ID: COMB-012 (Congestion is handled via ladder)
        VERIFIED v2: movement_intent_vs_result
        Logic ID: COMB-201 (Movement intentions are distinct from results)
        """
        # 1. Subject Alive?
        if not entity.lifecycle.active:
            return {entity.id: EntityUpdate(entity_id=entity.id)}

        # 2. Cache Lookup & Step Calculation
        m_cache = getattr(state_or_context, "movement_cache", None)
        current_tile = (int(entity.navigation.position[0]), int(entity.navigation.position[1]))
        target_tile = (int(target_pos[0]), int(target_pos[1]))
        current_tick = getattr(state_or_context, "tick", 0)

        cache_key = None
        cached_plan = None
        if m_cache is not None:
            cache_key = MovementPlanKey(entity.id, current_tile, target_tile, m_cache.occupancy_version)
            cached_plan = m_cache.get(cache_key, current_tick)

        if cached_plan is not None:
            effective_target = cached_plan.next_step
        else:
            effective_target = NavigationSystem.get_next_step(entity, target_pos, state_or_context)

        # 3. Environment & Mode Multipliers (Calculated early for readiness gating)
        region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state_or_context)
        move_speed_mult = 1.0
        if region:
            w_mults = EnvironmentService.get_weather_multipliers(region)
            a_mults = EnvironmentService.get_aura_multipliers(state_or_context, entity)
            move_speed_mult = w_mults.get("move_speed", 1.0) * a_mults.get("move_speed", 1.0)
            
        mode_mults = {
            MovementMode.PURSUE: 1.2, MovementMode.RETREAT: 1.5, MovementMode.WANDER: 0.5,
            MovementMode.REPOSITION: 1.1, MovementMode.REGROUP: 1.0, MovementMode.GUARD: 1.0,
            MovementMode.HOLD: 0.0,
        }
        # Logic ID: COMB-011 (Movement intentions exist as semantic modes)
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
            dx = effective_target[0] - entity.navigation.position[0]
            dy = effective_target[1] - entity.navigation.position[1]
            sidesteps = []
            if dx != 0: sidesteps = [(entity.navigation.position[0], entity.navigation.position[1] + 1), (entity.navigation.position[0], entity.navigation.position[1] - 1)]
            elif dy != 0: sidesteps = [(entity.navigation.position[0] + 1, entity.navigation.position[1]), (entity.navigation.position[0] - 1, entity.navigation.position[1])]
            
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
                        my_prio = LegalityServiceV2.get_entity_priority(entity, state_or_context)
                        occ_prio = LegalityServiceV2.get_entity_priority(occupant, state_or_context)
                        if my_prio > occ_prio:
                            # Search for yield tile
                            for dx_y, dy_y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                                yield_tile = (int(occupant.navigation.position[0]) + dx_y, int(occupant.navigation.position[1]) + dy_y)
                                if yield_tile == entity.navigation.position: continue
                                y_ok, _ = LegalityServiceV2.verify_occupancy(yield_tile, state_or_context, ignore_entity_id=occupant_id)
                                if y_ok:
                                    updates[occupant_id] = EntityUpdate(
                                        entity_id=occupant_id, new_position=yield_tile, moved_this_tick=True,
                                        navigation=NavigationUpdate(moved_recently_set=True, failure_reason=ReasonCode.YIELDING)
                                    )
                                    success = True; reason_code = None; break

            # 3.3 Reroute (If waiting too long)
            if not success and entity.navigation.wait_count >= 2:
                neighbors = [(-1,0),(1,0),(0,-1),(0,1)]
                neighbors.sort(key=lambda d: LegalityServiceV2.get_manhattan_dist((entity.navigation.position[0]+d[0], entity.navigation.position[1]+d[1]), target_pos))
                for dx_r, dy_r in neighbors:
                    reroute_tile = (entity.navigation.position[0] + dx_r, entity.navigation.position[1] + dy_r)
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

                # Cache successful move on cache miss
                if m_cache is not None and cache_key is not None and cached_plan is None and effective_target is not None:
                    m_cache.put(cache_key, MovementPlan(next_step=effective_target, valid_until_tick=current_tick + 10))

        # Logic ID: COMB-010 (Anti-stalemate logic handles chase/kite loops)
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
        # Logic ID: COMB-009 (Disengagement, pursuit, target stickiness are explicit rules)
        # Logic ID: COMB-272 (Disengagement has explicit consequence)
        # VERIFIED v2: disengagement_consequences
        # Logic ID: COMB-273 (Opportunity consequences apply only under legal conditions)
        if engaged_hostiles and not skip_oa:
            entities = getattr(state_or_context, 'entities', {})
            attackers = []
            for eid in engaged_hostiles:
                attacker = entities.get(eid)
                if attacker: attackers.append(attacker)
            
            if attackers:
                combat_update = CombatResolutionSystem.resolve_multi_attack(
                    attackers, entity, state_or_context, is_opportunity_attack=True, is_lethal=False
                )
                # Lift generation_delta/is_permadeath_set onto entity's own top-level lifecycle
                # field, mirroring the reference pattern in combat_actions.py::execute_attack()'s
                # defender_up construction -- left un-lifted (as with resource_transfers before
                # it), rebirth/permadeath was computed correctly inside combat_update but never
                # applied to real state (TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION).
                lifecycle_upd = LifecycleUpdate(
                    age_delta=0,
                    generation_delta=combat_update.generation_delta,
                    is_permadeath_set=combat_update.is_permadeath_set,
                ) if (combat_update.generation_delta != 0 or combat_update.is_permadeath_set is not None) else None
                updates[entity.id] = EntityUpdate(entity_id=entity.id, combat=combat_update, lifecycle=lifecycle_upd)

                # combat_update.resource_transfers rewards whoever defeated `entity` (the
                # attackers), not `entity` itself — must be lifted onto the attacker's own
                # top-level EntityUpdate.resource_transfers, the only field
                # ResourceTransactionSystem.resolve_all() reads (src/engine/economy.py:58).
                # Left un-lifted, the reward was silently orphaned inside a nested CombatUpdate
                # that nothing ever reads back out. attacker_id follows the same "first attacker"
                # attribution convention already used for multi-attacker kills elsewhere
                # (src/observability/event_shapers.py:158).
                if combat_update.resource_transfers and combat_update.attacker_id is not None:
                    reward_upd = EntityUpdate(
                        entity_id=combat_update.attacker_id,
                        resource_transfers=combat_update.resource_transfers,
                    )
                    existing_attacker_upd = updates.get(combat_update.attacker_id)
                    updates[combat_update.attacker_id] = (
                        existing_attacker_upd.merge(reward_upd) if existing_attacker_upd else reward_upd
                    )

        # 6. Final Subject Execution
        actor_up = updates.get(entity.id, EntityUpdate(entity_id=entity.id))
        
        # Terrain Cost (Checklist Section 7)
        terrain_cost = 1.0
        if success and effective_target:
            tile = (int(effective_target[0]), int(effective_target[1]))
            terrain_cost = TerrainCostService.get_tile_cost(tile, state_or_context)

        # Stamina drain on movement (Checklist Part 6 Section E)
        # VERIFIED v2: stamina_drain_movement
        stamina_upd = StaminaUpdate(current_delta=-entity.stamina.MOVE_COST) if success else None

        # Navigation Update Payload
        new_region_id = None
        if success and effective_target and effective_target != entity.navigation.position:
             new_region = LegalityServiceV2.get_region_for_position(effective_target, state_or_context)
             if new_region:
                 new_region_id = new_region.id

        nav_upd = NavigationUpdate(
            moved_recently_set=True,
            failure_reason=None if success else reason_code,
            # VERIFIED v2: movement_priority_tiebreak
            wait_count_delta=wait_delta,
            # VERIFIED v2: stalemate_breaker
            oscillation_count_delta=osc_delta,
            last_position_set=entity.navigation.position if success else None,
            clear_target=replan,
            clear_path=replan,
            region_id_set=new_region_id
        )

        # VERIFIED v2: environmental_move_cost
        # Logic ID: COMB-199 (Movement cost applied during authoritative application)
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
