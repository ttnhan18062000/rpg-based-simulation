from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Tuple
from dataclasses import replace

from src.core.updates import EntityUpdate, TaskUpdate, NavigationUpdate
from src.engine.legality import LegalityServiceV2
from src.engine.positioning import PositioningService
from src.core.strategic import ProjectStatus
from src.core.movement_modes import MovementMode
from src.core.enums import ActionStyle

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

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

        from src.engine.domain_logic import SimulationDomainLogic
        from src.engine.cognition import SensoryFilter, AppraisalSystem
        
        # 1. Goal Hysteresis (Pillar 3.2)
        # If we have a locked project/objective, maintain focus unless it's impossible
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

        # 2. Get hostiles in visibility range (Pillar 1.2: Selective Attention)
        raw_neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
        neighbors = SensoryFilter.filter_saliency(entity, raw_neighbors, max_targets=5)
        
        # 3. Emotional Appraisal (Pillar 1.1)
        region_trauma = SimulationDomainLogic.get_region_trauma(state, entity.position)
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

        hostiles = [
            n for n in neighbors 
            if n.identity.faction != entity.identity.faction and n.combat.alive
        ]
        
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

        if not hostiles:
            # Pillar 5.1: Objective Pursuit
            if entity.strategic.current_objective_id:
                obj_id = entity.strategic.current_objective_id
                # Find the objective in projects
                project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
                if project:
                    obj = next((o for o in project.objectives if o.id == obj_id), None)
                    if obj and obj.kind == "reach_location" and obj.target:
                        # Find the node
                        node_id = int(obj.target)
                        node = state.resource_nodes.get(node_id)
                        if node and node.remaining_charges > 0:
                            dist = abs(node.position[0] - entity.position[0]) + abs(node.position[1] - entity.position[1])
                            if dist < 1.0:
                                # At node: Interact
                                from src.core.updates import InteractionUpdate
                                return EntityUpdate(
                                    entity_id=entity.id,
                                    task=TaskUpdate(
                                        work_kind_set="ENTITY_ACT",
                                        payload_set={"action": "INTERACT", "target_id": node.id}
                                    ),
                                    interaction=InteractionUpdate(target_node_id=node.id, progress_delta=1)
                                )
                            else:
                                # Move to it
                                return EntityUpdate(
                                    entity_id=entity.id,
                                    navigation=NavigationUpdate(target_set=node.position, movement_mode_set=MovementMode.WANDER),
                                    task=TaskUpdate(
                                        work_kind_set="ENTITY_MOVE",
                                        payload_set={"target_position": node.position, "target_id": node.id}
                                    )
                                )
            
            # 4.1 Cohesion Check: If too far from group anchor, prioritize regrouping
            group = state.groups.get(entity.group_id) if entity.group_id is not None else None
            if group:
                dx = entity.position[0] - group.anchor[0]
                dy = entity.position[1] - group.anchor[1]
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
        group = state.groups.get(entity.group_id) if entity.group_id is not None else None
        def target_score(h: EntityState) -> Tuple[int, int, float, int]:
            dist = abs(h.position[0] - entity.position[0]) + abs(h.position[1] - entity.position[1])
            # Bias: Group shared target gets -1 in the first tuple element (highest priority)
            is_group_target = 0 if (group and group.shared_target_id == h.id) else 1
            # Local Hysteresis: Previous target gets a small bonus
            is_current_target = 0 if h.id == entity.task.payload.get("target_id") else 1
            return (is_group_target, is_current_target, h.combat.hp, dist, h.id)

        hostiles.sort(key=target_score)
        target = hostiles[0]

        # 5. Decision: Attack vs Positioning (Kiting/Closing)
        dist_to_target = abs(target.position[0] - entity.position[0]) + abs(target.position[1] - entity.position[1])
        
        # 4. Anti-Stalemate (GAP-T05)
        stale_ticks = entity.task.payload.get("stale_ticks", 0)
        recent_positions = list(entity.task.payload.get("recent_positions", []))
        
        # Detect Oscillation: A-B-A-B
        curr_pos = (int(entity.position[0]), int(entity.position[1]))
        if curr_pos in recent_positions:
             # Oscillating: Break stalemate
             stale_ticks += 5 

        recent_positions = ([curr_pos] + recent_positions)[:4]

        if stale_ticks > 10:
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
        hp_percent = entity.combat.hp / max(1, entity.combat.max_hp)
        if (role == "SKIRMISHER" or hp_percent < 0.4):
             ranged_threats = [h for h in hostiles if h.combat.range > 2]
             if ranged_threats:
                 cover_pos = PositioningService.find_nearest_cover(entity, ranged_threats[0], state)
                 if cover_pos and cover_pos != entity.position:
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
                 if is_walkable and bracket_pos != entity.position:
                     return EntityUpdate(
                         entity_id=entity.id,
                         navigation=NavigationUpdate(target_set=bracket_pos, movement_mode_set=MovementMode.REPOSITION),
                         task=TaskUpdate(
                             work_kind_set="ENTITY_MOVE",
                             payload_set={"target_position": bracket_pos, "reason": "BRACKETING", "target_id": target.id}
                         )
                     )

        # 5.3 Guarding Logic (Task 4.1)
        if group:
             # If an ally is wounded (<50% HP), try to guard them
             ally_ids = [eid for eid in group.member_ids if eid != entity.id]
             allies = [state.entities[eid] for eid in ally_ids if eid in state.entities]
             wounded_ally = next((a for a in allies if a.combat.hp / max(1, a.combat.max_hp) < 0.5), None)
             if wounded_ally:
                 guard_pos = PositioningService.find_guard_position(entity, wounded_ally, target, state)
                 if guard_pos != entity.position:
                     return EntityUpdate(
                         entity_id=entity.id,
                         navigation=NavigationUpdate(target_set=guard_pos, movement_mode_set=MovementMode.GUARD),
                         task=TaskUpdate(
                             work_kind_set="ENTITY_MOVE",
                             payload_set={"target_position": guard_pos, "reason": "GUARDING", "target_id": wounded_ally.id}
                         )
                     )

        # 5.4 Intercept Logic (Task 4.1)
        if dist_to_target > 3 and target.navigation.target:
             intercept_pos = PositioningService.find_intercept_position(entity, target, state)
             if intercept_pos != target.position:
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
             curr_pos = (float(int(entity.position[0])), float(int(entity.position[1])))
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
            dx = entity.position[0] - target.position[0]
            dy = entity.position[1] - target.position[1]
            
            # ActionStyle Impact: Aggressive skirmishers kite less, Evasive kite MORE
            kite_dist = 2 if style == ActionStyle.AGGRESSIVE else 6 if style == ActionStyle.EVASIVE else 4
            kite_pos = (entity.position[0] + (dx * kite_dist), entity.position[1] + (dy * kite_dist))
            
            return EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(target_set=kite_pos, movement_mode_set=MovementMode.RETREAT),
                task=TaskUpdate(
                    work_kind_set="ENTITY_MOVE",
                    payload_set={"target_position": kite_pos, "reason": "KITING", "target_id": target.id}
                )
            )

        # ActionStyle Bias: Aggressive entities ignore range buffers, Evasive entities maintain them strictly
        attack_range = entity.combat.range
        if style == ActionStyle.AGGRESSIVE:
             attack_range += 1
        elif style == ActionStyle.EVASIVE and dist_to_target < attack_range:
             # Evasive skirmishers might choose to reposition instead of attacking if too close
             pass

        if dist_to_target <= attack_range:
            # Attack
            return EntityUpdate(
                entity_id=entity.id,
                strategic=strat_up,
                task=TaskUpdate(
                    work_kind_set="ENTITY_ACT",
                    payload_set={
                        "action": "ATTACK", 
                        "target_id": target.id,
                        "stale_ticks": stale_ticks + 1,
                        "recent_positions": recent_positions
                    }
                )
            )
        else:
            # Pursuit
            return EntityUpdate(
                entity_id=entity.id,
                strategic=strat_up,
                navigation=NavigationUpdate(target_set=target.position, movement_mode_set=MovementMode.PURSUE),
                task=TaskUpdate(
                    work_kind_set="ENTITY_MOVE",
                    payload_set={
                        "target_position": target.position, 
                        "target_id": target.id,
                        "stale_ticks": stale_ticks + 1,
                        "recent_positions": recent_positions
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
