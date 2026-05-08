"""
Strategic Intelligence System.

Analyzes character outcomes to generate or resolve strategic markers.
Expanded in Phase 9 to support full directive/project/objective lifecycle,
interruption resistance, and cognition profile enforcement.

Covers:
- Part 1 §Strategic: Project switching uses interruption resistance / margin logic
- Part 1 §Strategic: Current project gets reservation/retention priority
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from src.core.state import EntityState, AuthoritativeState
from src.core.updates import (
    StrategicUpdate, InventoryUpdate, EntityUpdate, StateUpdate,
    CombatUpdate, BiologicalUpdate, IdentityUpdate
)
from src.core.strategic import (
    BlockerState, LeadState, LeadCertainty,
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    CognitionProfile
)
from src.strategy.cognition_capacity import CapacityService

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class StrategicIntelligenceSystem:
    """
    Analyzes character outcomes to generate or resolve strategic markers.
    Phase 9: Full strategic lifecycle management.
    """

    @staticmethod
    def infer_blockers(
        entity: EntityState,
        last_task: str,
        last_payload: Dict[str, Any],
        navigation_failure: Optional[str] = None,
        current_project: Optional[ProjectState] = None
    ) -> StrategicUpdate:
        """
        Infer blockers based on recent failures.
        VERIFIED v2: strategic_blocker_inference
        """
        blockers = []
        
        # 1. Navigation Failure (ACCESS blocker)
        if navigation_failure in ("PATH_NOT_FOUND", "STUCK", "OSCILLATING"):
            target_pos = last_payload.get("target_position")
            if target_pos:
                subject = f"{target_pos}"
                kind = "access"
                blockers.append(BlockerState(
                    id=f"blocker_access_{int(target_pos[0])}_{int(target_pos[1])}",
                    kind=kind,
                    subject=subject,
                    severity=0.8
                ))
        
        # Phase 4: Congestion Blocker
        if entity.navigation.wait_count >= 5 or entity.navigation.oscillation_count >= 3:
             blockers.append(BlockerState(
                 id="blocker_congestion",
                 kind="access",
                 subject="congestion",
                 severity=0.5
             ))
        
        # 2. Material/Resource Failure (Interactions)
        if last_task == "ENTITY_ACT" and last_payload.get("action") == "INTERACT":
            target_id = last_payload.get("target_id")
            if target_id and current_project and current_project.kind == "harvesting":
                # Check for capacity failure in latest intent results
                capacity_fail = any(r.reason == "INSUFFICIENT_CAPACITY" or r.reason == "INVENTORY_FULL" for r in entity.identity.latest_intent_results)
                if capacity_fail:
                    blockers.append(BlockerState(
                        id="blocker_inventory_full",
                        kind="inventory",
                        subject="capacity",
                        severity=1.0
                    ))
                else:
                    blockers.append(BlockerState(
                        id=f"blocker_node_{target_id}",
                        kind="material",
                        subject="resource", 
                        severity=1.0
                    ))

        # 3. Transaction Failures (Generic)
        for result in entity.identity.latest_intent_results:
            if not result.accepted:
                if result.reason in ("INSUFFICIENT_CAPACITY", "INVENTORY_FULL"):
                     blockers.append(BlockerState(
                        id="blocker_inventory_full",
                        kind="inventory",
                        subject="capacity",
                        severity=1.0
                    ))
                elif result.reason == "OUT_OF_STOCK":
                    blockers.append(BlockerState(
                        id=f"blocker_out_of_stock_{result.source_id}",
                        kind="material",
                        subject="out_of_stock",
                        severity=1.0
                    ))
                elif result.reason == "LIQUIDITY_EXHAUSTED":
                    blockers.append(BlockerState(
                        id=f"blocker_liquidity_{result.source_id}",
                        kind="material",
                        subject="liquidity",
                        severity=1.0
                    ))
        
        if not blockers:
            return StrategicUpdate()
            
        # Deduplicate by ID
        unique_blockers = {}
        for b in blockers:
            unique_blockers[b.id] = b
            
        return StrategicUpdate(blockers_add_or_update=list(unique_blockers.values()))

    @staticmethod
    def generate_crafting_blockers(
        entity: EntityState,
        recipe_mats: Dict[str, int],
        gold_cost: int
    ) -> StrategicUpdate:
        """
        Produce a StrategicUpdate containing blockers for missing requirements.
        """
        blockers = []
        inv = entity.inventory

        for mat_id, needed in recipe_mats.items():
            have = sum((s.quantity if hasattr(s, "quantity") else 1) for s in inv.items if (s.item_id if hasattr(s, "item_id") else s) == mat_id)
            if have < needed:
                blockers.append(BlockerState(
                    id=f"blocker_mat_{mat_id}",
                    kind="material",
                    subject=mat_id,
                    severity=min(1.0, (needed - have) / needed),
                    target_quantity=needed
                ))

        if inv.gold < gold_cost:
            blockers.append(BlockerState(
                id="blocker_gold",
                kind="material",
                subject="gold",
                severity=min(1.0, (gold_cost - inv.gold) / gold_cost),
                target_quantity=gold_cost
            ))

        return StrategicUpdate(blockers_add_or_update=blockers)

    @staticmethod
    def resolve_blockers(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Resolve strategic blockers that are satisfied by the current or pending
        authoritative inventory state.

        Important:
            Do not only inspect items_add from this tick. A blocker may survive
            from a previous tick even though the inventory already satisfies it.
        """
        from dataclasses import replace
        from src.core.updates import EntityUpdate, StrategicUpdate
        from src.core.inventory import InventoryService

        refined_entity_updates = dict(update.entity_updates)

        def has_item(inventory, item_id: str, quantity: int = 1) -> bool:
            if item_id == "gold":
                return inventory.gold >= quantity
            return any(
                stack.item_id == item_id and stack.quantity >= quantity
                for stack in inventory.items
            )

        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))

            pending_inventory = entity.inventory
            if ent_upd.inventory:
                pending_inventory = InventoryService.apply_update(
                    entity.inventory,
                    ent_upd.inventory,
                )

            strat_up = ent_upd.strategic or StrategicUpdate()
            removals = set(strat_up.blockers_remove)
            resolved_ids = set()
            # 1. Passive resolution from existing state
            # We ONLY check blockers from previous ticks. New blockers added this tick (in strat_up)
            # are trusted to be accurate results of current-tick enforcement (e.g. Blacksmith).
            for b_id, b in entity.strategic.blockers.items():
                if b_id in removals or b.resolved: continue
                if b.kind == "material" and has_item(pending_inventory, b.subject, b.target_quantity):
                    resolved_ids.add(b_id)
            
            # 2. Check for newly resolved blockers (explicitly marked as resolved)
            for blocker in strat_up.blockers_add_or_update:
                if blocker.resolved:
                    resolved_ids.add(blocker.id)

            # 3. Objective Resolution (RPG-STRAT-009 Fix)
            # If a blocker was resolved, check if the active objective is also resolved
            current_proj_id = strat_up.current_project_id_set if strat_up.current_project_id_set is not None else entity.strategic.current_project_id
            project_upd = None
            if current_proj_id:
                project = entity.strategic.projects.get(current_proj_id)
                if project and project.status == ProjectStatus.ACTIVE:
                    obj_id = strat_up.current_objective_id_set if strat_up.current_objective_id_set is not None else project.active_objective_id
                    active_obj = next((o for o in project.objectives if o.id == obj_id), None)
                    if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:
                        # Check if all blockers for this objective are resolved
                        all_blockers_resolved = True
                        for b_id in active_obj.blocker_ids:
                            if b_id not in entity.strategic.blockers and b_id not in [b.id for b in strat_up.blockers_add_or_update]:
                                 # This blocker was never there or already removed?
                                 continue
                            
                            is_now_resolved = (b_id in resolved_ids)
                            if not is_now_resolved:
                                 b_obj = entity.strategic.blockers.get(b_id)
                                 if b_obj and not b_obj.resolved:
                                      all_blockers_resolved = False
                                      break
                        
                        # Special case: Crafting/Collecting objectives (Material-based)
                        is_material_obj = active_obj.kind in ("craft", "collect")
                        if is_material_obj:
                             if has_item(pending_inventory, active_obj.target, 1):
                                  all_blockers_resolved = True
                        
                        if all_blockers_resolved:
                            # Resolve Objective and Complete Project
                            new_obj = replace(active_obj, status=ObjectiveStatus.RESOLVED)
                            new_project = replace(project, objectives=[new_obj if o.id == new_obj.id else o for o in project.objectives], status=ProjectStatus.COMPLETED)
                            project_upd = new_project
            
            if not resolved_ids and not project_upd:
                continue

            new_additions = [
                b for b in strat_up.blockers_add_or_update
                if b.id not in resolved_ids
            ]

            new_removals = list(
                set(strat_up.blockers_remove) | resolved_ids
            )

            new_projects = list(strat_up.projects_add_or_update)
            if project_upd:
                new_projects.append(project_upd)

            final_identity_upd = ent_upd.identity
            if project_upd and project_upd.status == ProjectStatus.COMPLETED:
                # Milestone 3 Law: Complete means stop trying [INTEG-FIX]
                final_identity_upd = (final_identity_upd or IdentityUpdate()).merge(IdentityUpdate(craft_target=""))

            refined_entity_updates[e_id] = replace(
                ent_upd,
                identity=final_identity_upd,
                strategic=replace(
                    strat_up,
                    blockers_add_or_update=new_additions,
                    blockers_remove=new_removals,
                    projects_add_or_update=new_projects,
                    current_project_id_set="" if project_upd else strat_up.current_project_id_set,
                    current_objective_id_set="" if project_upd else strat_up.current_objective_id_set
                ),
            )

        return replace(update, entity_updates=refined_entity_updates)



    @staticmethod
    def evaluate_all_concerns(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        Phase 9: Routine, Biological Needs, and Salience Filtering.
        VERIFIED v2: concern_intake_aggregation
        """
        from src.systems.routine import RoutineService
        from src.systems.intake import ConcernIntakeSystem
        from src.engine.domain_logic import SimulationDomainLogic
        
        refined_entity_updates = dict(update.entity_updates)
        
        # Phase 9 Fix: Deterministic entity iteration
        for e_id in sorted(list(state.entities.keys())):
            entity = state.entities[e_id]
            # Phase 5: Bounded frequency and early exit (Hardening)
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
            
            # Legality Guard: Incapacitated entities skip strategic cycles
            if entity.identity.properties.get("status_frozen") or entity.identity.properties.get("status_stunned"):
                continue

            if (state.tick + e_id) % 10 != 0:
                continue

            # 1. Internal/Biological Concerns
            concerns = RoutineService.evaluate_biological_needs(entity, state.world_time)
            anchored_concerns = RoutineService.evaluate_anchored_behavior(entity, state)
            env_concerns = RoutineService.evaluate_environmental_concerns(entity)
            
            # 2. External Salience Concerns (Phase 9 Hardening)
            neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
            salient_concerns = ConcernIntakeSystem.evaluate_salience(entity, neighbors, state)
            
            concerns.extend(anchored_concerns)
            concerns.extend(env_concerns)
            concerns.extend(salient_concerns)
            
            if not concerns:
                continue
                
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            strat_up = ent_upd.strategic or StrategicUpdate()

            new_concerns = list(set(strat_up.concerns_add_or_update + concerns))
            
            # Law 194: Enforce Strategic Bandwidth for concerns
            # Logic ID: 194
            from src.systems.detour import DetourSuggestionSystem
            bandwidth_upd = DetourSuggestionSystem.enforce_bandwidth(entity, state.tick)
            if bandwidth_upd.concerns_remove:
                to_remove = set(bandwidth_upd.concerns_remove)
                new_concerns = [c for c in new_concerns if c.id not in to_remove]
            
            new_strat_up = replace(
                strat_up,
                concerns_add_or_update=new_concerns,
                concerns_remove=list(set(strat_up.concerns_remove + bandwidth_upd.concerns_remove))
            )
            refined_entity_updates[e_id] = replace(ent_upd, strategic=new_strat_up)
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def evaluate_all_strategic_intents(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        Phase 4.1: Strategic Intent Evaluation (Projects/Objectives).
        Orchestrates the loop over evaluate_strategic_intent for all active entities.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id in sorted(list(state.entities.keys())):
            entity = state.entities[e_id]
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
            
            # Legality Guard: Incapacitated entities skip strategic cycles
            if entity.identity.properties.get("status_frozen") or entity.identity.properties.get("status_stunned"):
                continue

            # Staggered frequency (Phase 5/6 spec)
            if (state.tick + e_id) % 10 != 0:
                continue

            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # We must pass the "current best guess" of the entity state to evaluate_strategic_intent.
            # However, evaluate_strategic_intent is designed to work on the static EntityState.
            # For v2 consistency, we call it on the current state.
            strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
            if strat_up:
                # Merge with existing updates if any
                existing_strat = ent_upd.strategic or StrategicUpdate()
                merged_strat = existing_strat.merge(strat_up)
                refined_entity_updates[e_id] = replace(ent_upd, strategic=merged_strat)
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def apply_routine_biasing(
        entity: EntityState,
        world_time: int,
        projects: List[ProjectState],
        neighbors: List[EntityState] = []
    ) -> List[ProjectState]:
        from src.systems.routine import RoutineService
        from src.systems.learning import StrategicLearningService
        from src.engine.cognition import AppraisalSystem
        
        # 1. Routine and Role Biasing
        projects = RoutineService.apply_role_based_biasing(entity, projects, world_time)
        
        # 2. Strategic Memory (Learning) Biasing
        memory_biases = StrategicLearningService.get_goal_biases(entity.strategic.turning_points)
        
        # 3. Emotional Appraisal (Short-term) Biasing
        # We need neighbors for full appraisal, but can use defaults if empty
        emotion = AppraisalSystem.evaluate_emotional_state(entity, neighbors)
        
        biased_projects = []
        for p in projects:
            score = p.score
            
            # Apply memory bias
            kind_key = p.kind.lower()
            if kind_key in memory_biases:
                score += memory_biases[kind_key]
                
            # Apply emotional bias
            if kind_key == "combat" or kind_key == "detour":
                score *= emotion.aggression_mod
                if emotion.is_fleeing:
                    score -= 50.0 # Heavy penalty for combat if panicked
            
            biased_projects.append(replace(p, score=score))
            
        return biased_projects

    @staticmethod
    def evaluate_project_switch(
        entity: EntityState,
        candidate_project: ProjectState,
        current_tick: int
    ) -> Optional[StrategicUpdate]:
        """
        Phase 9: Strategic interruption resistance and retention.
        VERIFIED v2: project_interruption_resistance
        VERIFIED v2: current_project_retention
        """
        profile = entity.strategic.profile
        current_id = entity.strategic.current_project_id

        if not current_id:
            return StrategicUpdate(
                projects_add_or_update=[candidate_project],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        current = entity.strategic.projects.get(current_id)
        if not current or current.status != ProjectStatus.ACTIVE:
            return StrategicUpdate(
                projects_add_or_update=[candidate_project],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        if current.lock_until_tick > current_tick:
            # Bypass lock ONLY for high-urgency danger/safety projects
            if candidate_project.kind == "danger" and candidate_project.score > 80:
                pass 
            else:
                return None 

        retention_margin = profile.interruption_resistance * 30
        effective_current_score = current.score + retention_margin

        if candidate_project.score > effective_current_score:
            return StrategicUpdate(
                projects_add_or_update=[
                    replace(current, status=ProjectStatus.SUSPENDED),
                    candidate_project
                ],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        return None

    @staticmethod
    def resume_project(
        entity: EntityState,
        project_id: str
    ) -> Optional[StrategicUpdate]:
        project = entity.strategic.projects.get(project_id)
        if not project or project.status != ProjectStatus.SUSPENDED:
            return None

        resumed = replace(project, status=ProjectStatus.ACTIVE)
        return StrategicUpdate(
            projects_add_or_update=[resumed],
            current_project_id_set=project_id,
            current_objective_id_set=project.active_objective_id
        )

    @staticmethod
    def process_project_outcome(
        entity: EntityState,
        project_id: str,
        outcome: ProjectStatus,
        current_tick: int
    ) -> StrategicUpdate:
        """
        Record the final result of a project and apply learning effects.
        """
        project = entity.strategic.projects.get(project_id)
        if not project:
            return StrategicUpdate()

        from src.core.strategic import TurningPointState
        tps = []
        boredom_delta = {}

        if outcome == ProjectStatus.COMPLETED:
            # Record Victory
            tps.append(TurningPointState(
                id=f"victory_{project.kind}_{current_tick}",
                kind="great_victory" if project.score > 15.0 else "victory",
                tick=current_tick,
                salience=0.6
            ))
            # Decrement boredom for this kind (success makes it more rewarding)
            boredom_delta[project.kind] = -2.0
            
        elif outcome == ProjectStatus.ABANDONED:
            # Record Loss
            tps.append(TurningPointState(
                id=f"abandon_{project.kind}_{current_tick}",
                kind="loss",
                tick=current_tick,
                salience=0.4
            ))
            # Increment boredom for this kind
            boredom_delta[project.kind] = 5.0

        updated_project = replace(project, status=outcome)
        
        return StrategicUpdate(
            projects_add_or_update=[updated_project],
            turning_points_add=tps,
            boredom_delta=boredom_delta,
            current_project_id_set="" if entity.strategic.current_project_id == project_id else None
        )

    @staticmethod
    def process_outcome(
        observer: EntityState,
        subject_id: int,
        success: bool
    ) -> SocialUpdate:
        """
        VERIFIED v2: StrategicIntelligenceSystem.process_outcome
        """
        from src.social.appraisal import SocialAppraisalSystem
        outcome_quality = 1.0 if success else -1.0
        # recalibrate_trust in appraisal.py takes observer.social
        return SocialAppraisalSystem.recalibrate_trust(observer.social, subject_id, outcome_quality)

    @staticmethod
    def _resolve_active_objective(state: AuthoritativeState, entity: EntityState) -> Optional[StrategicUpdate]:
        strat = entity.strategic
        if not strat.current_project_id:
            return None
        
        project = strat.projects.get(strat.current_project_id)
        if not project or project.status != ProjectStatus.ACTIVE:
            return None
            
        obj = next((o for o in project.objectives if o.id == project.active_objective_id), None)
        if not obj or obj.status != ObjectiveStatus.ACTIVE:
            return None
            
        # 1. Reach Location Resolution
        if obj.kind == "reach_location" and obj.target:
            try:
                if isinstance(obj.target, str):
                    try:
                        import ast
                        target_pos = ast.literal_eval(obj.target)
                    except (ValueError, SyntaxError):
                        target_pos = None
                else:
                    target_pos = obj.target
                dist = abs(entity.navigation.position[0] - target_pos[0]) + abs(entity.navigation.position[1] - target_pos[1])
                if dist < 1.0:
                    resolved_obj = replace(obj, status=ObjectiveStatus.RESOLVED)
                    # For now, we assume 1 objective per detour project
                    return StrategicUpdate(
                        projects_add_or_update=[replace(project, objectives=[resolved_obj], status=ProjectStatus.COMPLETED)],
                        current_project_id_set="",
                        current_objective_id_set=""
                    )
            except:
                 pass
        return None

    @staticmethod
    def evaluate_strategic_intent(
        state: AuthoritativeState,
        entity: EntityState,
        force: bool = False
    ) -> StrategicUpdate:
        """
        Produce a collection of strategic intent updates for the next tick.
        """
        # Phase 5: Bounded frequency and early exit (Hardening)
        if not entity.lifecycle.active or not entity.combat.alive:
            return StrategicUpdate()
        
        # Legality Guard: Incapacitated entities skip strategic cycles
        if entity.identity.properties.get("status_frozen") or entity.identity.properties.get("status_stunned"):
            return StrategicUpdate()

        if not force and (state.tick + entity.id) % 10 != 0:
            return StrategicUpdate()

        # 0. Strategic Memory (PH6: Lead Suppression)
        from src.systems.detour import DetourSuggestionSystem
        memory_upd = DetourSuggestionSystem.suppress_exhausted_leads(entity, state.tick)
        
        res_up = StrategicIntelligenceSystem._resolve_active_objective(state, entity)
        if res_up:
            return replace(res_up, 
                leads_add_or_update=memory_upd.leads_add_or_update,
                leads_remove=memory_upd.leads_remove
            )

        current_tick = state.tick
        strat = entity.strategic
        
        boredom_upd = {}
        if strat.current_project_id:
            proj = strat.projects.get(strat.current_project_id)
            if proj and proj.status == ProjectStatus.ACTIVE:
                boredom_upd[proj.kind] = 0.1
        
        # 1. Detour Completion & Project Resumption
        active_or_completed_detour = None
        if strat.current_project_id:
            p = strat.projects.get(strat.current_project_id)
            if p and p.kind == "detour":
                active_or_completed_detour = p
        else:
            # Check for a detour that just completed but isn't current anymore
            active_or_completed_detour = next((p for p in strat.projects.values() if p.kind == "detour" and p.status == ProjectStatus.COMPLETED), None)

        if active_or_completed_detour and active_or_completed_detour.status == ProjectStatus.COMPLETED:
            # Phase 6: Resolve associated blockers
            blockers_to_resolve = []
            for obj in active_or_completed_detour.objectives:
                if obj.status == ObjectiveStatus.RESOLVED:
                     blockers_to_resolve.extend(obj.blocker_ids)
            
            blocker_updates = []
            for b_id in blockers_to_resolve:
                b = strat.blockers.get(b_id)
                if b:
                    blocker_updates.append(replace(b, resolved=True))

            suspended = next((p for p in strat.projects.values() if p.status == ProjectStatus.SUSPENDED), None)
            if suspended:
                resumed_up = StrategicIntelligenceSystem.resume_project(entity, suspended.id)
                if resumed_up:
                    final_resumed = replace(
                        resumed_up,
                        projects_add_or_update=resumed_up.projects_add_or_update + [active_or_completed_detour],
                        blockers_add_or_update=resumed_up.blockers_add_or_update + blocker_updates,
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )
                    return final_resumed

        # 2. Project Abandonment (PH6)
        if strat.current_project_id:
            project = strat.projects.get(strat.current_project_id)
            if project and project.status == ProjectStatus.ACTIVE:
                # If project has failed too many times, abandon it
                if project.failure_count >= 3:
                    abandoned = replace(project, status=ProjectStatus.ABANDONED)
                    # Frustration penalty (Phase 6 spec)
                    boredom_upd[project.kind] = boredom_upd.get(project.kind, 0.0) + 0.5
                    return StrategicUpdate(
                        projects_add_or_update=[abandoned],
                        current_project_id_set="",
                        current_objective_id_set="",
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )

                if project.kind == "harvesting" and project.active_objective_id:
                    target_id_str = project.active_objective_id.split("_")[-1]
                    try:
                        target_id = int(target_id_str)
                        node = state.resource_nodes.get(target_id)
                        if not node or node.remaining_charges <= 0:
                            return StrategicUpdate(
                                projects_add_or_update=[replace(project, status=ProjectStatus.COMPLETED)],
                                current_project_id_set="",
                                current_objective_id_set="",
                                boredom_delta=boredom_upd,
                                leads_add_or_update=memory_upd.leads_add_or_update,
                                leads_remove=memory_upd.leads_remove
                            )
                    except ValueError:
                        pass
                
                # Milestone 8: Shop scarcity feedback
                if project.kind == "shopping" and project.active_objective_id:
                     target_id_str = project.active_objective_id.split("_")[-1]
                     try:
                         b_id = int(target_id_str)
                         building = state.buildings.get(b_id)
                         if not building or not building.functional:
                              return StrategicUpdate(
                                 projects_add_or_update=[replace(project, status=ProjectStatus.ABANDONED)],
                                 current_project_id_set="",
                                 current_objective_id_set="",
                                 boredom_delta=boredom_upd,
                                 leads_add_or_update=memory_upd.leads_add_or_update,
                                 leads_remove=memory_upd.leads_remove
                             )
                     except ValueError:
                         pass
                
                if strat.blockers and entity.identity.group_id is None:
                    from src.systems.detour import DetourSuggestionSystem
                    detours = DetourSuggestionSystem.suggest_detours(entity, current_tick)
                    if detours:
                        best = detours[0]
                        obj = ObjectiveState(
                            id=f"detour_{best.blocker_id}_{current_tick}",
                            kind=best.objective_kind,
                            target=best.target,
                            status=ObjectiveStatus.ACTIVE,
                            blocker_ids=[best.blocker_id]
                        )
                        detour_proj = ProjectState(
                            id=f"proj_detour_{current_tick}",
                            kind="detour",
                            status=ProjectStatus.ACTIVE,
                            objectives=[obj],
                            active_objective_id=obj.id,
                            lock_until_tick=current_tick + 20,
                            created_tick=current_tick,
                            score=best.score + 50.0 
                        )
                        detour_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, detour_proj, current_tick)
                        if detour_up:
                            final_detour = replace(detour_up, 
                                boredom_delta=boredom_upd,
                                leads_add_or_update=memory_upd.leads_add_or_update,
                                leads_remove=memory_upd.leads_remove
                            )
                            return final_detour
        
        from src.ai.goals import GoalRegistry
        from src.ai.score_modifiers import ScoreModifierSystem
        from src.systems.party import PartyCoordinationSystem
        
        # 4. Goal Scoring & Routine Biasing
        all_scores = GoalRegistry.get_all_scores(entity, state)
        
        # PH9: Routine & Life-Rhythm Biasing
        from src.systems.routine import RoutineService
        all_scores = [
            replace(s, utility=s.utility + 
                    RoutineService.get_routine_utility_boost(entity, s.kind.lower(), state.world_time) +
                    RoutineService.get_role_utility_boost(entity, s.kind.lower()))
            for s in all_scores
        ]
        
        # PH7: Leadership Influence
        from src.systems.party import PartyCoordinationSystem
        all_scores = PartyCoordinationSystem.apply_leadership_influence(entity, state, all_scores)
        
        modified_scores = ScoreModifierSystem.apply_modifiers(entity, state, all_scores)
        modified_scores.sort(key=lambda x: x.utility, reverse=True)
        
        best_candidate = None
        for g_score in modified_scores:
            if g_score.utility < 20.0 or g_score.target_id is None:
                continue
            best_candidate = g_score
            break
            
        if best_candidate:
            existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)
            
            if existing and existing.status == ProjectStatus.SUSPENDED:
                resumed_up = StrategicIntelligenceSystem.resume_project(entity, existing.id)
                if resumed_up:
                    return replace(resumed_up,
                        boredom_delta=boredom_upd,
                        leads_add_or_update=memory_upd.leads_add_or_update,
                        leads_remove=memory_upd.leads_remove
                    )
            
            obj = ObjectiveState(
                id=f"{best_candidate.kind}_{best_candidate.target_id}",
                kind="reach_location",
                target=best_candidate.target_id,
                status=ObjectiveStatus.ACTIVE
            )
            candidate_proj = ProjectState(
                id=f"proj_{best_candidate.kind}_{current_tick}",
                kind=best_candidate.kind,
                status=ProjectStatus.ACTIVE,
                objectives=[obj],
                active_objective_id=obj.id,
                lock_until_tick=current_tick + 10,
                created_tick=current_tick,
                score=best_candidate.utility
            )
            
            at_capacity = len(strat.projects) >= strat.profile.max_active_projects
            if at_capacity and not existing:
                if boredom_upd:
                    return StrategicUpdate(boredom_delta=boredom_upd)
                return StrategicUpdate()

            switch_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_proj, current_tick)
            if switch_up:
                return replace(switch_up, 
                    boredom_delta=boredom_upd,
                    leads_add_or_update=memory_upd.leads_add_or_update,
                    leads_remove=memory_upd.leads_remove
                )
            
            # Law 194-197: Enforce Strategic Bandwidth
            # Logic ID: 195, 196
            bandwidth_upd = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick)
            if bandwidth_upd.leads_remove or bandwidth_upd.concerns_remove:
                # Merge with current state of updates
                return StrategicUpdate(
                    leads_add_or_update=memory_upd.leads_add_or_update,
                    leads_remove=list(set(memory_upd.leads_remove + bandwidth_upd.leads_remove)),
                    concerns_remove=bandwidth_upd.concerns_remove,
                    overload_source_set=bandwidth_upd.overload_source_set,
                    overload_tick_set=bandwidth_upd.overload_tick_set,
                    boredom_delta=boredom_upd
                )

        if memory_upd.leads_add_or_update or memory_upd.leads_remove:
            return memory_upd

        if boredom_upd:
            return StrategicUpdate(boredom_delta=boredom_upd)
            
        return StrategicUpdate()

    @staticmethod
    def derive_cognition_profile(entity: EntityState) -> CognitionProfile:
        """
        VERIFIED v2: StrategicIntelligenceSystem.derive_cognition_profile
        """
        return CapacityService.derive_profile(entity)
