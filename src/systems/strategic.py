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
    CombatUpdate, BiologicalUpdate
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
        """
        blockers = []
        
        # 1. Navigation Failure (ACCESS blocker)
        if navigation_failure == "PATH_NOT_FOUND":
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
        
        # 2. Material/Resource Failure
        if last_task == "ENTITY_ACT" and last_payload.get("action") == "INTERACT":
            target_id = last_payload.get("target_id")
            if target_id and current_project and current_project.kind == "harvesting":
                blockers.append(BlockerState(
                    id=f"blocker_node_{target_id}",
                    kind="material",
                    subject="wood", 
                    severity=1.0
                ))
        
        if not blockers:
            return StrategicUpdate()
            
        return StrategicUpdate(blockers_add_or_update=blockers)

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
                    severity=min(1.0, (needed - have) / needed)
                ))

        if inv.gold < gold_cost:
            blockers.append(BlockerState(
                id="blocker_gold",
                kind="material",
                subject="gold",
                severity=min(1.0, (gold_cost - inv.gold) / gold_cost)
            ))

        return StrategicUpdate(blockers_add_or_update=blockers)

    @staticmethod
    def resolve_blockers(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        State-wide resolution of material and access blockers.
        Called by the Kernel in Phase 4 (Resolution).
        """
        refined_entity_updates = dict(update.entity_updates)

        for e_id, ent_upd in update.entity_updates.items():
            if e_id not in state.entities:
                continue

            entity = state.entities[e_id]
            resolved_ids = []
            
            # 1. Scan for material blockers matching added items
            items_added = []
            if ent_upd.inventory:
                items_added.extend(ent_upd.inventory.items_add)
            
            # Milestone 7: Also check resource_transfers
            for transfer in ent_upd.resource_transfers:
                items_added.extend(transfer.items_add)

            active_blocker_ids = set(entity.strategic.blockers.keys())
            if ent_upd.strategic:
                active_blocker_ids.update(b.id for b in ent_upd.strategic.blockers_add_or_update)

            for item in items_added:
                item_id = item.item_id if hasattr(item, "item_id") else item
                blocker_id = f"blocker_mat_{item_id}"
                if blocker_id in active_blocker_ids:
                    resolved_ids.append(blocker_id)

            # 2. Scan for access blockers (Resolved by proximity)
            for b_id, blocker in entity.strategic.blockers.items():
                if blocker.kind == "access" and not blocker.resolved:
                    try:
                        # blocker.subject might be "(5.0, 6.0)"
                        target_pos = eval(blocker.subject)
                        dist = abs(entity.position[0] - target_pos[0]) + abs(entity.position[1] - target_pos[1])
                        if dist < 1.0:
                            resolved_ids.append(b_id)
                    except:
                        pass

            if not resolved_ids:
                continue

            # 3. Produce update
            # V2 Law: Resolved blockers are REMOVED to maintain lean state (Pillar 1).
            strat_up = ent_upd.strategic or StrategicUpdate()
            
            # Milestone 8 P0: Add resolved versions to add_or_update 
            # to signal the event to other systems/tests.
            new_additions = list(strat_up.blockers_add_or_update)
            for b_id in resolved_ids:
                original = entity.strategic.blockers.get(b_id)
                if original:
                    new_additions.append(replace(original, resolved=True))
            
            # Then ensure they are in the removal list for final purge
            new_removals = list(set(strat_up.blockers_remove + resolved_ids))

            new_strat_up = replace(
                strat_up,
                blockers_add_or_update=new_additions,
                blockers_remove=new_removals
            )
            refined_entity_updates[e_id] = replace(ent_upd, strategic=new_strat_up)
            
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def evaluate_biological_concerns(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        Phase 9: Routine, Biological Needs, and Life-Rhythm.
        """
        from src.systems.routine import RoutineService
        
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            concerns = RoutineService.evaluate_biological_needs(entity, state.world_time)
            anchored_concerns = RoutineService.evaluate_anchored_behavior(entity, state)
            concerns.extend(anchored_concerns)
            
            if not concerns:
                continue
                
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            strat_up = ent_upd.strategic or StrategicUpdate()

            new_concerns = list(set(strat_up.concerns_add_or_update + concerns))
            
            new_strat_up = replace(
                strat_up,
                concerns_add_or_update=new_concerns
            )
            refined_entity_updates[e_id] = replace(ent_upd, strategic=new_strat_up)
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def apply_routine_biasing(
        entity: EntityState,
        world_time: int,
        projects: List[ProjectState]
    ) -> List[ProjectState]:
        from src.systems.routine import RoutineService
        return RoutineService.apply_role_based_biasing(entity, projects, world_time)

    @staticmethod
    def evaluate_project_switch(
        entity: EntityState,
        candidate_project: ProjectState,
        current_tick: int
    ) -> Optional[StrategicUpdate]:
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
    def process_outcome(
        observer: EntityState,
        subject_id: int,
        success: bool
    ) -> StrategicUpdate:
        from src.systems.social import SocialAppraisalSystem
        outcome_quality = 1.0 if success else -1.0
        social_up = SocialAppraisalSystem.recalibrate_trust(observer, subject_id, outcome_quality)
        return social_up

    @staticmethod
    def evaluate_strategic_intent(
        state: AuthoritativeState,
        entity: EntityState
    ) -> StrategicUpdate:
        current_tick = state.tick
        strat = entity.strategic
        
        boredom_upd = {}
        if strat.current_project_id:
            proj = strat.projects.get(strat.current_project_id)
            if proj and proj.status == ProjectStatus.ACTIVE:
                boredom_upd[proj.kind] = 0.1
        
        if strat.current_project_id:
            project = strat.projects.get(strat.current_project_id)
            if project:
                if project.kind == "detour" and project.status == ProjectStatus.COMPLETED:
                    suspended = next((p for p in strat.projects.values() if p.status == ProjectStatus.SUSPENDED), None)
                    if suspended:
                        resumed_up = StrategicIntelligenceSystem.resume_project(entity, suspended.id)
                        if resumed_up:
                            if project.status != ProjectStatus.COMPLETED:
                                resumed_up = replace(
                                    resumed_up,
                                    projects_add_or_update=resumed_up.projects_add_or_update + [replace(project, status=ProjectStatus.COMPLETED)]
                                )
                            if boredom_upd:
                                resumed_up = replace(resumed_up, boredom_delta=boredom_upd)
                            return resumed_up

                if project.status == ProjectStatus.ACTIVE:
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
                                    boredom_delta=boredom_upd
                                )
                        except ValueError:
                            pass
                
                if strat.blockers:
                    from src.systems.detour import DetourSuggestionSystem
                    detours = DetourSuggestionSystem.suggest_detours(entity, current_tick)
                    if detours:
                        best = detours[0]
                        obj = ObjectiveState(
                            id=f"detour_{best.blocker_id}_{current_tick}",
                            kind=best.objective_kind,
                            target=best.target,
                            status=ObjectiveStatus.ACTIVE
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
                            if boredom_upd:
                                detour_up = replace(detour_up, boredom_delta=boredom_upd)
                            return detour_up
        
        from src.ai.goals import GoalRegistry
        from src.ai.score_modifiers import ScoreModifierSystem
        all_scores = GoalRegistry.get_all_scores(entity, state)
        
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
                    if boredom_upd:
                        resumed_up = replace(resumed_up, boredom_delta=boredom_upd)
                    return resumed_up
            
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
                if boredom_upd:
                    switch_up = replace(switch_up, boredom_delta=boredom_upd)
                return switch_up

        if boredom_upd:
            return StrategicUpdate(boredom_delta=boredom_upd)
            
        return StrategicUpdate()

    @staticmethod
    def derive_cognition_profile(entity: EntityState) -> CognitionProfile:
        return CapacityService.derive_profile(entity)
