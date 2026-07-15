# Compliance IDs: COMBAT-019, SOC-009
# Compliance IDs: COMB-013, COMB-014, COMB-015, COMB-016, COMB-209, COMB-210, COMB-215, COMB-254, COMB-255, COMB-263, COMB-264, COMB-265, COMB-267, COMB-268, COMB-269, COMB-270, COMB-271, COMB-274, COMB-275, COMB-276, COMB-277, STRAT-188
# Compliance IDs: COMB-014, COMB-015, COMB-016
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Tuple
from dataclasses import replace
import logging

logger = logging.getLogger(__name__)

from src.core.updates import EntityUpdate, TaskUpdate, NavigationUpdate
from src.engine.legality import LegalityServiceV2
from src.engine.positioning import PositioningService
from src.core.strategic import ProjectStatus, ObjectiveKind
from src.core.movement_modes import MovementMode
from src.core.enums import ActionStyle, ReasonCode, EntityRole, Faction
from src.core.skills import SKILL_REGISTRY

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState
    from src.core.strategic import ObjectiveState

class TacticalDecisionSystem:
    """
    Authoritative logic for bounded local tactical decisions.
    Logic ID: 123
    Responsible for target selection, engagement commitment, and anti-stalemate.
    VERIFIED v2: TacticalDecisionSystem

    SYSTEM BOUNDARIES:
    - Tactical Decision strictly consumes the selected strategic state
      (`entity.strategic.current_project_id` and the active project/objective).
    - It does not mutate or make parallel strategic decisions, maintaining the
      Strategic Pass as the single source of truth for planning.
    """

    @staticmethod
    def evaluate_entity_intent(
        state: AuthoritativeState,
        entity: EntityState,
        neighbors: Optional[List[EntityState]] = None,
        region_trauma: Optional[float] = None
    ) -> EntityUpdate:
        """
        Determines the next tactical intent for an entity.
        Bounded to local visibility and immediate combat state.
        Optimized v2.5: Accepts pre-calculated context from cognition domain.
        """

        # 0. Global Legality Guard
        # Optimized v2.5: verify_action_legality now uses DomainView cache
        legal, reason = LegalityServiceV2.verify_action_legality(entity, "TACTICAL_EVAL", state)
        if not legal:
            return EntityUpdate(entity_id=entity.id)

        from src.engine.cognition import AppraisalSystem
        
        # 1. Goal Hysteresis (Pillar 3.2)
        current_project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
        if current_project and state.tick < current_project.lock_until_tick:
            # Maintain current task if target is still valid
            current_target_id = entity.task.payload.get("target_id")
            if current_target_id:
                target = state.entities.get(current_target_id)
                if target and target.combat.alive:
                    stale_ticks = entity.task.payload.get("stale_ticks", 0)
                    return EntityUpdate(
                        entity_id=entity.id,
                        task=TaskUpdate(
                            work_kind_set=entity.task.work_kind,
                            payload_set={**entity.task.payload, "stale_ticks": stale_ticks + 1}
                        )
                    )

        # 2. Context retrieval
        if neighbors is None:
             from src.engine.domain_logic import SimulationDomainLogic
             from src.engine.cognition import SensoryFilter
             raw_neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
             neighbors = SensoryFilter.filter_saliency(entity, raw_neighbors, max_targets=5)
        
        if region_trauma is None:
             from src.engine.domain_logic import SimulationDomainLogic
             region_trauma = SimulationDomainLogic.get_region_trauma(state, entity.navigation.position)

        # 3. Emotional Appraisal (Pillar 1.1)
        emotion = AppraisalSystem.evaluate_emotional_state(
            entity, 
            neighbors, 
            region_trauma=region_trauma,
            social_context=entity.social
        )
        
        if emotion.is_fleeing:
             # PANIC: Move to safe origin
             return EntityUpdate(
                 entity_id=entity.id,
                 navigation=NavigationUpdate(target_set=(0.0, 0.0), movement_mode_set=MovementMode.RETREAT),
                 task=TaskUpdate(
                     work_kind_set="ENTITY_MOVE",
                     payload_set={"target_position": (0.0, 0.0), "reason": "PANIC_RETREAT"}
                 )
             )

        # Section 8: Mob Leashing (GAP-T08)
        from src.engine.rpg_depth import LeashService
        is_engaged = entity.task.payload.get("target_id") is not None
        
        # If beyond leash AND not chasing, or beyond chase limit
        if (not is_engaged and LeashService.is_beyond_leash(entity)) or LeashService.should_give_up_chase(entity):
             home_pos = LeashService.get_return_home_target(entity)
             if home_pos:
                  return EntityUpdate(
                      entity_id=entity.id,
                      navigation=NavigationUpdate(target_set=home_pos, movement_mode_set=MovementMode.RETREAT),
                      task=TaskUpdate(
                          work_kind_set="ENTITY_MOVE",
                          payload_set={"target_position": home_pos, "reason": "LEASH_RETURN"}
                      )
                  )

        from src.content_semantics.faction import get_faction_semantics_service, get_faction_id_str, get_race_id_str
        from src.content_semantics.relation import RelationContext
        from src.entities.identity_resolver import EntityIdentityResolver, IdentityResolutionError
        from src.engine.behavior_consumers import (
            get_perception_gate, get_pressure_resolver, get_entity_signals,
        )
        from src.world.motivation.pressure_resolver import MotivationPressureSet

        # Resolve entity pressures once — used for scoring and flee gating
        try:
            entity_pressures = get_pressure_resolver().resolve_pressures(entity)
        except Exception:
            entity_pressures = MotivationPressureSet.empty()

        semantics_service = get_faction_semantics_service()
        _id_resolver = EntityIdentityResolver()
        _gate = get_perception_gate()
        hostiles = []
        hostile_identity_sources: dict = {}

        try:
            _src_identity = _id_resolver.resolve(entity)
            _src_faction_id = _src_identity.faction_id
            _src_identity_source = _src_identity.source
        except IdentityResolutionError:
            _src_faction_id = get_faction_id_str(entity)
            _src_identity_source = "legacy_fallback"

        for n in neighbors:
            if not n.combat.alive:
                continue
            dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, n.navigation.position)
            # Perception gate: entity can only engage targets it can detect
            try:
                if not _gate.can_perceive(entity, get_entity_signals(n), {"distance": float(dist)}).perceived:
                    continue
            except Exception:
                pass  # Gate failure → permissive fallback
            combat_engaged = (
                entity.task.payload.get("target_id") == n.id
                or n.task.payload.get("target_id") == entity.id
            )
            context = RelationContext(
                distance=float(dist),
                combat_engaged=combat_engaged,
                target_race=get_race_id_str(n),
                intruding=False,
            )
            try:
                _tgt_identity = _id_resolver.resolve(n)
                _tgt_faction_id = _tgt_identity.faction_id
            except IdentityResolutionError:
                _tgt_faction_id = get_faction_id_str(n)

            if semantics_service.is_hostile_compat(_src_faction_id, _tgt_faction_id, context):
                hostiles.append(n)
                hostile_identity_sources[n.id] = _src_identity_source
        
        # 4. Strategic Persistence (Pillar 5.1)
        # If hostiles are present, we should SUSPEND the current project if it's not already
        strat_up = None
        if hostiles and entity.strategic.current_project_id:
             project = entity.strategic.projects.get(entity.strategic.current_project_id)
             if project and project.status == ProjectStatus.ACTIVE:
                  # Suspend to handle threat
                  from src.core.updates import StrategicUpdate
                  strat_up = StrategicUpdate(
                      projects_add_or_update=[replace(project, status=ProjectStatus.SUSPENDED)],
                      current_project_id_set="",
                      current_objective_id_set=""
                  )

        # Safety pressure: high-safety entities retreat from threats rather than engage
        if hostiles and entity_pressures.safety_pressure > 0.75:
            return EntityUpdate(
                entity_id=entity.id,
                strategic=strat_up,
                navigation=NavigationUpdate(target_set=(0.0, 0.0), movement_mode_set=MovementMode.RETREAT),
                task=TaskUpdate(
                    work_kind_set="ENTITY_MOVE",
                    payload_set={"target_position": (0.0, 0.0), "reason": "SAFETY_PRESSURE_RETREAT"}
                )
            )

        if not hostiles:
            # Pillar 5.1: Objective Pursuit
            if entity.strategic.current_objective_id:
                obj_id = entity.strategic.current_objective_id
                # Find the objective in projects
                project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
                if project:
                    obj = next((o for o in project.objectives if o.id == obj_id), None)
                    if obj and obj.kind == "reach_location" and obj.target:
                        target_pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(state, obj)

                        if target_pos:
                            dist = abs(target_pos[0] - entity.navigation.position[0]) + abs(target_pos[1] - entity.navigation.position[1])
                            if dist <= 1.0:
                                if node_id is not None:
                                    from src.core.updates import InteractionUpdate
                                    return EntityUpdate(
                                        entity_id=entity.id,
                                        task=TaskUpdate(
                                            work_kind_set="ENTITY_ACT",
                                            payload_set={"action": "INTERACT", "target_id": node_id}
                                        ),
                                        interaction=InteractionUpdate(target_node_id=node_id, progress_delta=1)
                                    )
                                elif building_id is not None:
                                    # At a building: dispatch survival action by project kind
                                    proj_kind = getattr(project, "kind", "")
                                    if proj_kind == "hunger":
                                        return EntityUpdate(
                                            entity_id=entity.id,
                                            task=TaskUpdate(
                                                work_kind_set="ENTITY_ACT",
                                                payload_set={"action": "EAT", "target_id": building_id}
                                            )
                                        )
                                    elif proj_kind == "fatigue":
                                        return EntityUpdate(
                                            entity_id=entity.id,
                                            task=TaskUpdate(
                                                work_kind_set="ENTITY_ACT",
                                                payload_set={"action": "REST", "target_id": building_id}
                                            )
                                        )
                                    else:
                                        return EntityUpdate(entity_id=entity.id)
                                else:
                                    return EntityUpdate(entity_id=entity.id)
                            else:
                                # Still en-route — update nav target and stay idle
                                # so the brain re-evaluates on each cadence tick.
                                return EntityUpdate(
                                    entity_id=entity.id,
                                    navigation=NavigationUpdate(target_set=target_pos, movement_mode_set=MovementMode.WANDER),
                                )
                    elif obj and obj.kind not in (ObjectiveKind.REACH_LOCATION, ObjectiveKind.DEFEAT_ENEMY):
                        # Pillar 5.1 continued: every other ObjectiveKind System A/B can
                        # produce reaches real execution via ObjectiveIntentResolver +
                        # ActionIntentAdapter, not just REACH_LOCATION. DEFEAT_ENEMY is
                        # excluded — handled entirely by the hostile-engagement branch
                        # below (gated on `hostiles`, not `obj.kind`).
                        target_pos = None
                        node_id = None
                        if obj.target:
                            target_pos, node_id, _ = TacticalDecisionSystem._resolve_target_position(state, obj)

                        if target_pos:
                            dist = abs(target_pos[0] - entity.navigation.position[0]) + abs(target_pos[1] - entity.navigation.position[1])
                            if dist > 1.0:
                                return EntityUpdate(
                                    entity_id=entity.id,
                                    navigation=NavigationUpdate(target_set=target_pos, movement_mode_set=MovementMode.WANDER),
                                )
                            if obj.kind == ObjectiveKind.REACH_RESOURCE and node_id is not None:
                                # Arrived at the resource node: transition to a harvest
                                # action instead of falling through to
                                # ObjectiveIntentResolver's REACH_RESOURCE -> MOVE_TO
                                # mapping, which would re-issue navigation forever.
                                from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter

                                harvest_intent = ActionIntent(
                                    kind="HARVEST_RESOURCE",
                                    actor_id=entity.id,
                                    target_id=node_id,
                                    source_opportunity_id=obj.id,
                                    reason=f"Arrived at resource node {node_id} for objective {obj.id}",
                                )
                                updates = ActionIntentAdapter.execute(
                                    entity, harvest_intent, current_tick=state.tick, neighbor_view=neighbors, context=state
                                )
                                return updates.get(entity.id, EntityUpdate(entity_id=entity.id))

                        from src.domains.adventure.resolver import ObjectiveIntentResolver
                        from src.engine.intent.action_intent import ActionIntentAdapter

                        intent = ObjectiveIntentResolver.resolve(
                            entity.id, obj, payload={"position": target_pos} if target_pos else {}
                        )
                        updates = ActionIntentAdapter.execute(
                            entity, intent, current_tick=state.tick, neighbor_view=neighbors, context=state
                        )
                        return updates.get(entity.id, EntityUpdate(entity_id=entity.id))

            # 4.1 Role-Based Obligation (Phase 7)
            group = state.groups.get(entity.identity.group_id) if entity.identity.group_id is not None else None
            if group and not hostiles:
                leader = state.entities.get(group.leader_id)
                if leader and leader.combat.alive:
                    role = group.roles.get(entity.id)
                    # If leader is interacting with something, hirelings should guard/support
                    if leader.task.work_kind == "ENTITY_ACT" and leader.task.payload.get("action") == "INTERACT":
                        if role in ("VANGUARD", "PROTECTOR"):
                            # Guard position near leader
                            guard_pos = PositioningService.find_guard_position(entity, leader, None, state)
                            if guard_pos != entity.navigation.position:
                                return EntityUpdate(
                                    entity_id=entity.id,
                                    navigation=NavigationUpdate(target_set=guard_pos, movement_mode_set=MovementMode.GUARD),
                                    task=TaskUpdate(
                                        work_kind_set="ENTITY_MOVE",
                                        payload_set={"target_position": guard_pos, "reason": "CONTRACT_OBLIGATION_GUARD", "target_id": leader.id}
                                    )
                                )

            # 4.2 Cohesion Check: If too far from group anchor, prioritize regrouping
            if group:
                dx = entity.navigation.position[0] - group.anchor[0]
                dy = entity.navigation.position[1] - group.anchor[1]
                dist_sq = dx*dx + dy*dy
                if dist_sq > group.cohesion_radius**2:
                    return EntityUpdate(
                        entity_id=entity.id,
                        navigation=NavigationUpdate(target_set=group.anchor, movement_mode_set=MovementMode.REGROUP),
                        task=TaskUpdate(
                            work_kind_set="ENTITY_MOVE",
                            payload_set={"target_position": group.anchor, "reason": "REGROUP"}
                        )
                    )
            
            return EntityUpdate(entity_id=entity.id)

        # 4. Target Selection with Focus Fire
        group = state.groups.get(entity.identity.group_id) if entity.identity.group_id is not None else None
        def target_score(h: EntityState) -> Tuple[float, int, float, int, int]:
            dist = abs(h.navigation.position[0] - entity.navigation.position[0]) + abs(h.navigation.position[1] - entity.navigation.position[1])
            
            # Domain 7 Hardening: Trust-based focus fire bias
            group_bias = 1.0
            if group and group.shared_target_id == h.id:
                bond = entity.social.bonds.get(group.leader_id)
                trust = (bond.sentiment + 1.0) / 2.0 if bond else entity.social.trust_history.get(group.leader_id, 0.5)
                
                # Trust mapping:
                # If trust is < 0.2, bias is 1.0 (neutral, ignoring leader).
                # If trust is high, bias is lower (higher priority).
                if trust >= 0.2:
                    group_bias = 1.0 - trust
                    
                    # VANGUARDS are more likely to focus on the group target.
                    if entity.combat.tactical_role == "VANGUARD":
                        group_bias *= 0.5
                
            # Local Hysteresis: Previous target gets a small bonus
            is_current_target = 0 if h.id == entity.task.payload.get("target_id") else 1

            # Pressure-based priority: territory and duty pressure reduce effective distance
            # (lower score = higher priority), making territorial/duty-bound entities more
            # aggressive toward threats.
            pressure_dist_mod = max(
                0.0,
                1.0
                - entity_pressures.territory_pressure * 0.4
                - entity_pressures.duty_pressure * 0.3,
            )

            return (group_bias, is_current_target, h.combat.hp, dist * pressure_dist_mod, h.id)

        logger.debug(f"DEBUG: entity {entity.id} evaluating targets. Group target: {group.shared_target_id if group else None}")
        for h in hostiles:
            logger.debug(f"DEBUG: target {h.id} score: {target_score(h)}")
        hostiles.sort(key=target_score)
        
        # Phase E5.2: Tactical Legality Envelope (Hardening)
        # Filter hostiles by actual attack legality (LoS, Range, Faction)
        legal_attack_targets = []
        for h in hostiles:
            # Logic ID: COMB-254 (Tactical action choice uses only legal candidate actions)
            legal, _ = LegalityServiceV2.verify_attack_legality(entity, h, state)
            if legal:
                legal_attack_targets.append(h)
        
        target = legal_attack_targets[0] if legal_attack_targets else (hostiles[0] if hostiles else None)
        is_attack_legal = target in legal_attack_targets

        # 5. Decision: Attack vs Positioning (Kiting/Closing)
        dist_to_target = abs(target.navigation.position[0] - entity.navigation.position[0]) + abs(target.navigation.position[1] - entity.navigation.position[1])
        
        # 4. Anti-Stalemate (GAP-T05)
        # Logic ID: COMB-270 (Target stickiness prevents unrealistic full retarget every tick)
        # Logic ID: COMB-271 (Target stickiness can break when target invalid/dead/out of range)
        # Logic ID: COMB-274 (Anti-stalemate handles chase loops)
        # Logic ID: COMB-275 (Anti-stalemate handles kite loops)
        # Logic ID: COMB-276 (Anti-stalemate handles repeated step-back loops)
        stale_ticks = entity.task.payload.get("stale_ticks", 0)
        recent_positions = list(entity.task.payload.get("recent_positions", []))
        
        # Detect Oscillation: A-B-A-B
        curr_pos = (int(entity.navigation.position[0]), int(entity.navigation.position[1]))
        if curr_pos in recent_positions:
             # Oscillating: Break stalemate
             stale_ticks += 5 

        recent_positions = ([curr_pos] + recent_positions)[:4]

        if stale_ticks > 10:
             # Logic ID: COMB-277 (Anti-stalemate does not force illegal movement)
             return EntityUpdate(
                 entity_id=entity.id,
                 strategic=strat_up,
                 navigation=NavigationUpdate(target_set=(0.0, 0.0), movement_mode_set=MovementMode.WANDER),
                 task=TaskUpdate(
                     work_kind_set="ENTITY_MOVE",
                     payload_set={"target_position": (0.0, 0.0), "reason": "STALEMATE_BREAK"}
                 )
             )

        # Tactical Role Logic
        role = entity.combat.tactical_role
        style = entity.combat.action_style
        
        # 5.1 Cover Seeking and Low HP Retreat (Task 4.2/4.3)
        # Ranged threats trigger cover seeking for Skirmishers or wounded entities
        # Logic ID: COMB-268 (Low HP affects tactical choice)
        hp_percent = entity.combat.hp / max(1, entity.combat.max_hp)
        if (role == "SKIRMISHER" or hp_percent < 0.4):
             # Logic ID: COMB-269 (Threat level affects tactical choice)
             ranged_threats = [h for h in hostiles if h.combat.range > 2]
             if ranged_threats:
                 cover_pos = PositioningService.find_nearest_cover(entity, ranged_threats[0], state)
                 if cover_pos and cover_pos != entity.navigation.position:
                     return EntityUpdate(
                         entity_id=entity.id,
                         navigation=NavigationUpdate(target_set=cover_pos, movement_mode_set=MovementMode.REPOSITION),
                         task=TaskUpdate(
                             work_kind_set="ENTITY_MOVE",
                             payload_set={"target_position": cover_pos, "reason": "SEEK_COVER", "target_id": ranged_threats[0].id}
                         )
                     )
             
             # Pure Retreat if HP is very low and engaged
             if hp_percent < 0.15:
                  # Move to safe origin or away from all hostiles
                  retreat_pos = (0.0, 0.0) # Simple fallback to origin for now
                  return EntityUpdate(
                      entity_id=entity.id,
                      navigation=NavigationUpdate(target_set=retreat_pos, movement_mode_set=MovementMode.RETREAT),
                      task=TaskUpdate(
                          work_kind_set="ENTITY_MOVE",
                          payload_set={"target_position": retreat_pos, "reason": "PANIC_RETREAT"}
                      )
                  )

        # 5.2 Bracketing Logic (Task 4.3)
        if role == "VANGUARD" and group:
             # Find ally in same group also targeting this target
             ally_ids = [eid for eid in group.member_ids if eid != entity.id]
             allies = [state.entities[eid] for eid in ally_ids if eid in state.entities]
             targeting_ally = next((a for a in allies if a.task.payload.get("target_id") == target.id), None)
             
             if targeting_ally:
                 bracket_pos = PositioningService.get_bracketing_position(entity, targeting_ally, target)
                 is_walkable, _ = LegalityServiceV2.verify_occupancy(bracket_pos, state, ignore_entity_id=entity.id)
                 if is_walkable and bracket_pos != entity.navigation.position:
                     return EntityUpdate(
                         entity_id=entity.id,
                         navigation=NavigationUpdate(target_set=bracket_pos, movement_mode_set=MovementMode.REPOSITION),
                         task=TaskUpdate(
                             work_kind_set="ENTITY_MOVE",
                             payload_set={"target_position": bracket_pos, "reason": "BRACKETING", "target_id": target.id}
                         )
                     )

        # 5.3 Guarding Logic (Task 4.1 / 6.5)
        # PROTECTOR role prioritizes wounded allies over direct combat
        if group and role == "PROTECTOR":
             ally_ids = [eid for eid in group.member_ids if eid != entity.id]
             allies = [state.entities[eid] for eid in ally_ids if eid in state.entities]
             
             # Priority 1: Guard Leader if they are interacting or low HP
             leader = state.entities.get(group.leader_id)
             wounded_ally = None
             if leader and leader.id != entity.id:
                  hp_ratio = leader.combat.hp / max(1, leader.combat.max_hp)
                  if leader.interaction.target_node_id is not None or hp_ratio < 0.8:
                       wounded_ally = leader
             
             # Priority 2: Guard any other wounded ally
             if not wounded_ally:
                  wounded_ally = next((a for a in allies if a.combat.hp / max(1, a.combat.max_hp) < 0.7), None)
             
             if wounded_ally:
                  guard_pos = PositioningService.find_guard_position(entity, wounded_ally, target, state)
                  if guard_pos != entity.navigation.position:
                      return EntityUpdate(
                          entity_id=entity.id,
                          navigation=NavigationUpdate(target_set=guard_pos, movement_mode_set=MovementMode.GUARD),
                          task=TaskUpdate(
                              work_kind_set="ENTITY_MOVE",
                              payload_set={"target_position": guard_pos, "reason": "GUARDING_ALLY", "target_id": wounded_ally.id}
                          )
                      )

        # 5.4 Intercept Logic (Task 4.1)
        if dist_to_target > 3 and target.navigation.target:
             intercept_pos = PositioningService.find_intercept_position(entity, target, state)
             if intercept_pos != target.navigation.position:
                 return EntityUpdate(
                     entity_id=entity.id,
                     navigation=NavigationUpdate(target_set=intercept_pos, movement_mode_set=MovementMode.INTERCEPT),
                     task=TaskUpdate(
                         work_kind_set="ENTITY_MOVE",
                         payload_set={"target_position": intercept_pos, "reason": "INTERCEPTING", "target_id": target.id}
                     )
                 )

        if role == "VANGUARD" and dist_to_target <= 5:
             chokepoints = PositioningService.identify_chokepoints(entity, state)
             curr_pos = (float(int(entity.navigation.position[0])), float(int(entity.navigation.position[1])))
             if curr_pos in chokepoints:
                  # Already at chokepoint: HOLD if target is still relatively close
                  if dist_to_target > entity.combat.range:
                       return EntityUpdate(
                           entity_id=entity.id,
                           navigation=NavigationUpdate(movement_mode_set=MovementMode.HOLD),
                           task=TaskUpdate(
                               work_kind_set="ENTITY_ACT",
                               payload_set={"action": "HOLD", "reason": "HOLD_CHOKEPOINT", "target_id": target.id}
                           )
                       )

        if role == "SKIRMISHER" and dist_to_target < entity.combat.range:
            # Kiting: Move away from target
            dx = entity.navigation.position[0] - target.navigation.position[0]
            dy = entity.navigation.position[1] - target.navigation.position[1]
            
            # ActionStyle Impact: Aggressive skirmishers kite less, Evasive kite MORE
            kite_dist = 2 if style == ActionStyle.AGGRESSIVE else 6 if style == ActionStyle.EVASIVE else 4
            
            # Role-Based Kiting Enhancement (Task 6.5)
            if role == "SKIRMISHER":
                kite_dist += 2
            
            # Domain 7 Hardening: Kite towards group anchor if possible
            base_kite_pos = (entity.navigation.position[0] + (dx * kite_dist), entity.navigation.position[1] + (dy * kite_dist))
            if group:
                # Weighted average: 70% away from target, 30% towards group anchor
                anchor_dx = group.anchor[0] - entity.navigation.position[0]
                anchor_dy = group.anchor[1] - entity.navigation.position[1]
                kite_pos = (
                    base_kite_pos[0] * 0.7 + (entity.navigation.position[0] + anchor_dx) * 0.3,
                    base_kite_pos[1] * 0.7 + (entity.navigation.position[1] + anchor_dy) * 0.3
                )
            else:
                kite_pos = base_kite_pos
            
            # Verify kite position is walkable (Phase E5.2)
            kite_legal, _ = LegalityServiceV2.verify_occupancy(kite_pos, state, ignore_entity_id=entity.id)
            if not kite_legal:
                 # If kiting destination is blocked, fallback to pursuit
                 return EntityUpdate(
                     entity_id=entity.id,
                     navigation=NavigationUpdate(target_set=target.navigation.position, movement_mode_set=MovementMode.PURSUE),
                     task=TaskUpdate(
                         work_kind_set="ENTITY_MOVE",
                         payload_set={"target_position": target.navigation.position, "reason": "PURSUIT_BLOCKED_KITE", "target_id": target.id}
                     )
                 )

            return EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(target_set=kite_pos, movement_mode_set=MovementMode.RETREAT),
                task=TaskUpdate(
                    work_kind_set="ENTITY_MOVE",
                    payload_set={"target_position": kite_pos, "reason": "KITING", "target_id": target.id}
                )
            )

        # ActionStyle Bias: Aggressive entities ignore range buffers, Evasive entities maintain them strictly
        # Logic ID: COMB-263 (Weapon range affects tactical choice)
        attack_range = entity.combat.range
        if style == ActionStyle.AGGRESSIVE:
             attack_range += 1
        elif style == ActionStyle.EVASIVE and dist_to_target < attack_range:
             # Evasive skirmishers might choose to reposition instead of attacking if too close
             pass

        if is_attack_legal:
            # 5.5 Skill Selection (Task 8.7 Hardening)
            # Logic ID: COMB-264 (Skill range affects tactical choice)
            # Logic ID: COMB-265 (Skill cost affects tactical choice)
            chosen_skill_id = None
            if entity.identity.learned_skills:
                available_skills = []
                for skill_id in entity.identity.learned_skills:
                    skill = SKILL_REGISTRY.get(skill_id)
                    if not skill: continue
                    
                    # Readiness/Cooldown check
                    on_cooldown = entity.identity.cooldowns.get(skill_id, 0) > state.tick
                    # Logic ID: COMB-266 (Readiness/cooldown affects tactical choice)
                    
                    if not on_cooldown and dist_to_target <= skill.range:
                        # Cost check
                        if entity.stamina.current >= skill.cost:
                            available_skills.append(skill)
                
                if available_skills:
                    # Choice Bias: Pick highest power
                    available_skills.sort(key=lambda s: s.power, reverse=True)
                    chosen_skill_id = available_skills[0].id

            # Logic ID: COMB-267 (Exhaustion affects tactical choice)
            # If stamina is low and no free skills, might favor basic attack or rest
            # But resolve_attack handles stamina drain.

            # Final Action Emission
            if chosen_skill_id:
                return EntityUpdate(
                    entity_id=entity.id,
                    strategic=strat_up,
                    task=TaskUpdate(
                        work_kind_set="ENTITY_ACT",
                        payload_set={
                            "action": "SKILL",
                            "skill_id": chosen_skill_id,
                            "target_id": target.id,
                            "stale_ticks": stale_ticks + 1,
                            "recent_positions": recent_positions,
                            "target_identity_source": hostile_identity_sources.get(target.id, _src_identity_source),
                        }
                    )
                )
            
            # Default: Basic Attack
            return EntityUpdate(
                entity_id=entity.id,
                strategic=strat_up,
                task=TaskUpdate(
                    work_kind_set="ENTITY_ACT",
                    payload_set={
                        "action": "ATTACK",
                        "target_id": target.id,
                        "stale_ticks": stale_ticks + 1,
                        "recent_positions": recent_positions,
                        "target_identity_source": hostile_identity_sources.get(target.id, _src_identity_source),
                    }
                )
            )
        else:
            # Pursuit
            target_pos = target.navigation.position
            
            # Domain 7 Hardening: Vanguard charge limit
            if role == "VANGUARD" and group:
                dx = target.navigation.position[0] - group.anchor[0]
                dy = target.navigation.position[1] - group.anchor[1]
                dist_from_anchor = (dx*dx + dy*dy)**0.5
                if dist_from_anchor > group.cohesion_radius * 1.5:
                    # Too far from group: only move to the edge of the cohesion zone
                    scale = (group.cohesion_radius * 1.5) / dist_from_anchor
                    target_pos = (group.anchor[0] + dx * scale, group.anchor[1] + dy * scale)
                    
            return EntityUpdate(
                entity_id=entity.id,
                strategic=strat_up,
                navigation=NavigationUpdate(target_set=target_pos, movement_mode_set=MovementMode.PURSUE),
                task=TaskUpdate(
                    work_kind_set="ENTITY_MOVE",
                    payload_set={
                        "target_position": target_pos,
                        "target_id": target.id,
                        "stale_ticks": stale_ticks + 1,
                        "recent_positions": recent_positions,
                        "target_identity_source": hostile_identity_sources.get(target.id, _src_identity_source),
                    }
                )
            )

    @staticmethod
    def _resolve_target_position(
        state: AuthoritativeState, obj: "ObjectiveState"
    ) -> Tuple[Optional[Tuple[float, float]], Optional[int], Optional[int]]:
        """
        Resolve an objective's `target` (an int-castable resource-node/building id,
        or a stringified coordinate tuple) into a concrete world position.

        Caller must guard `obj.target` truthy before calling — `int(None)` raises
        TypeError, which is deliberately left uncaught here to keep this a byte-
        identical extraction of the pre-existing REACH_LOCATION inline logic.
        """
        target_pos = None
        node_id = None
        building_id = None
        try:
            candidate_id = int(obj.target)
            node = state.resource_nodes.get(candidate_id)
            if node:
                target_pos = node.position
                node_id = candidate_id
            else:
                # Not a resource node — check buildings (e.g. HUNGER→tavern, FATIGUE→inn)
                building = state.buildings.get(candidate_id)
                if building:
                    target_pos = building.position
                    building_id = candidate_id
        except ValueError:
            # Not an int, try coordinate tuple
            # Safe coordinate parse: "(x, y)" -> (float, float)
            try:
                import ast
                target_pos = ast.literal_eval(obj.target)
            except (ValueError, SyntaxError):
                target_pos = None
        return target_pos, node_id, building_id

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
            dist = abs(h.navigation.position[0] - attacker.navigation.position[0]) + abs(h.navigation.position[1] - attacker.navigation.position[1])
            return (h.combat.hp, dist, h.id)
            
        sorted_candidates = sorted(candidates, key=target_score)
        return sorted_candidates[0]
