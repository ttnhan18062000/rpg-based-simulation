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
from typing import Dict, List, Optional

from src_legacy.core.state import EntityState, AuthoritativeState
from src_legacy.core.updates import (
    StrategicUpdate, InventoryUpdate, EntityUpdate, StateUpdate,
    CombatUpdate, BiologicalUpdate
)
from src_legacy.core.strategic import (
    BlockerState, LeadState, LeadCertainty,
    ProjectState, ProjectStatus, ObjectiveState,
    CognitionProfile
)
from src_legacy.strategy.cognition_capacity import CapacityService


class StrategicIntelligenceSystem:
    """
    Analyzes character outcomes to generate or resolve strategic markers.
    Phase 9: Full strategic lifecycle management.
    """

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

        # 1. Look for missing materials
        for mat_id, needed in recipe_mats.items():
            have = sum((s.quantity if hasattr(s, "quantity") else 1) for s in inv.items if (s.item_id if hasattr(s, "item_id") else s) == mat_id)
            if have < needed:
                blockers.append(BlockerState(
                    id=f"blocker_mat_{mat_id}",
                    kind="material",
                    subject=mat_id,
                    severity=min(1.0, (needed - have) / needed)
                ))

        # 2. Look for missing gold
        if inv.gold < gold_cost:
            blockers.append(BlockerState(
                id="blocker_gold",
                kind="material",
                subject="gold",
                severity=min(1.0, (gold_cost - inv.gold) / gold_cost)
            ))

        return StrategicUpdate(blockers_add_or_update=blockers)

    @staticmethod
    def validate_leads(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        Phase 9: Strategic Lead Validation.
        If an entity reached a lead's target position but the blocker remains, 
        mark lead as tested/failed.
        """
        refined_entity_updates = dict(update.entity_updates)

        for e_id, ent_upd in update.entity_updates.items():
            if e_id not in state.entities:
                continue

            entity = state.entities[e_id]
            
            # Check if reached navigation target this tick
            reached = False
            # Check if current pos or new pos matches navigation target
            nav_target = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set is not None:
                nav_target = ent_upd.navigation.target_set
            
            final_pos = ent_upd.new_position or entity.position
            if nav_target and final_pos == nav_target:
                reached = True
            
            leads_to_update = []
            # PH6: Objective-based Lead Validation
            current_obj_id = entity.strategic.current_objective_id
            if not current_obj_id:
                continue

            # Find the objective
            project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
            if not project:
                continue
                
            objective = next((o for o in project.objectives if o.id == current_obj_id), None)
            if not objective or not objective.lead_id:
                continue
                
            lead_id = objective.lead_id
            lead = entity.strategic.leads.get(lead_id)
            if not lead or lead.tested:
                continue

            # Check if reached target
            # For simplicity, if objective.kind is 'reach_location', we check if we are at the target
            # Actually, if the objective is COMPLETED (which we can check if the system COMPLETED it this tick)
            # OR if we are AT the location and nothing happened.
            
            # If the entity is at the target of the 'reach_location' objective
            is_at_target = False
            if objective.kind == "reach_location" and objective.target:
                # Resolve target to position (if it's a node id)
                try:
                    target_id = int(objective.target)
                    node = state.resource_nodes.get(target_id)
                    if node:
                        final_pos = ent_upd.new_position or entity.position
                        if final_pos == node.position:
                            is_at_target = True
                except ValueError:
                    pass
            
            if is_at_target:
                # Check if the associated blocker was NOT resolved
                blocker_id = f"blocker_mat_{lead.subject}"
                is_resolved = False
                if ent_upd.strategic and blocker_id in ent_upd.strategic.blockers_remove:
                    is_resolved = True
                
                # Also check if it was resolved in a previous tick (though unlikely if lead is still active)
                if not is_resolved:
                    # Lead FAILED
                    leads_to_update.append(replace(lead, tested=True, test_outcome='FAILURE'))

            if leads_to_update:
                strat_up = ent_upd.strategic or StrategicUpdate()
                new_strat_up = replace(
                    strat_up,
                    leads_add_or_update=strat_up.leads_add_or_update + leads_to_update
                )
                refined_entity_updates[e_id] = replace(ent_upd, strategic=new_strat_up)

        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def resolve_blockers(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        State-wide resolution of material blockers based on inventory additions.
        Called by the Kernel in Phase 4 (Resolution).
        """
        refined_entity_updates = dict(update.entity_updates)

        for e_id, ent_upd in update.entity_updates.items():
            if e_id not in state.entities:
                continue

            entity = state.entities[e_id]

            # Identify added items
            items_added = []
            if ent_upd.inventory:
                items_added.extend(ent_upd.inventory.items_add)

            if not items_added:
                continue

            # Scan for material blockers matching added items
            resolved_ids = []

            # Combine current blockers and proposed additions for resolution check
            active_blocker_ids = set(entity.strategic.blockers.keys())
            if ent_upd.strategic:
                active_blocker_ids.update(b.id for b in ent_upd.strategic.blockers_add_or_update)

            for item in items_added:
                item_id = item.item_id if hasattr(item, "item_id") else item
                blocker_id = f"blocker_mat_{item_id}"
                if blocker_id in active_blocker_ids:
                    resolved_ids.append(blocker_id)

            if resolved_ids:
                # Merge into existing entity update
                strat_up = ent_upd.strategic or StrategicUpdate()

                # Filter out newly added blockers if they match resolved_ids
                new_additions = [
                    b for b in strat_up.blockers_add_or_update
                    if b.id not in resolved_ids
                ]

                # Resolve leads as well
                resolved_leads = []
                active_lead_ids = set(entity.strategic.leads.keys())
                for item in items_added:
                    item_id = item.item_id if hasattr(item, "item_id") else item
                    # Find any lead with this subject
                    for l_id, lead in entity.strategic.leads.items():
                         if lead.subject == item_id:
                             resolved_leads.append(l_id)

                new_strat_up = replace(
                    strat_up,
                    blockers_add_or_update=new_additions,
                    blockers_remove=list(set(strat_up.blockers_remove + resolved_ids)),
                    leads_remove=list(set(strat_up.leads_remove + resolved_leads))
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
        Applies biological pressure to strategic concerns.
        """
        from src_legacy.systems.routine import RoutineService
        
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            # Get current/proposed biological state
            # (Decay is applied in apply_generation, so we look at current state)
            concerns = RoutineService.evaluate_biological_needs(entity, state.world_time)
            
            # Phase 9: Anchored-World Behavior
            anchored_concerns = RoutineService.evaluate_anchored_behavior(entity, state)
            concerns.extend(anchored_concerns)
            
            if concerns:
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                strat_up = ent_upd.strategic or StrategicUpdate()
                
                new_strat_up = replace(
                    strat_up,
                    concerns_add_or_update=list(set(strat_up.concerns_add_or_update + concerns))
                )
                refined_entity_updates[e_id] = replace(ent_upd, strategic=new_strat_up)
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def apply_routine_biasing(
        entity: EntityState,
        world_time: int,
        projects: List[ProjectState]
    ) -> List[ProjectState]:
        """
        Applies utility boosts based on routine and biological needs.
        """
        from src_legacy.systems.routine import RoutineService
        return RoutineService.apply_role_based_biasing(entity, projects, world_time)

    @staticmethod
    def evaluate_project_switch(
        entity: EntityState,
        candidate_project: ProjectState,
        current_tick: int
    ) -> Optional[StrategicUpdate]:
        """
        Part 1 §Strategic: Project switching uses interruption resistance / margin logic.

        Returns a StrategicUpdate only if the switch should happen.
        The current project gets a retention bonus proportional to interruption_resistance.
        """
        profile = entity.strategic.profile
        current_id = entity.strategic.current_project_id

        if not current_id:
            # No current project — always switch
            return StrategicUpdate(
                projects_add_or_update=[candidate_project],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        current = entity.strategic.projects.get(current_id)
        if not current or current.status != ProjectStatus.ACTIVE:
            # Current project is gone or not active — switch
            return StrategicUpdate(
                projects_add_or_update=[candidate_project],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        # Check lock
        if current.lock_until_tick > current_tick:
            return None  # Locked, cannot switch

        # Retention margin: current gets a bonus from interruption_resistance
        retention_bonus = profile.interruption_resistance * 30
        effective_current_score = current.score + retention_bonus

        if candidate_project.score > effective_current_score:
            # Switch: suspend current, activate candidate
            return StrategicUpdate(
                projects_add_or_update=[
                    replace(current, status=ProjectStatus.SUSPENDED),
                    candidate_project
                ],
                current_project_id_set=candidate_project.id,
                current_objective_id_set=candidate_project.active_objective_id
            )

        return None  # Current project retained

    @staticmethod
    def resume_project(
        entity: EntityState,
        project_id: str
    ) -> Optional[StrategicUpdate]:
        """
        Resume a previously suspended project.
        Restores its last active objective.
        """
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
        """
        Processes a strategic outcome (e.g. lead resolution) and triggers social feedback.
        Legacy parity: test_source_trust_recalibration.
        """
        from src_legacy.systems.social_legacy import SocialAppraisalSystem

        outcome_quality = 1.0 if success else -1.0
        social_up = SocialAppraisalSystem.recalibrate_trust(observer, subject_id, outcome_quality)

        # In a real integration, this would be part of a larger resolution update.
        # For Milestone 7, we return the social update wrapped in a generic update container.
        return social_up

    @staticmethod
    def evaluate_strategic_intent(
        state: AuthoritativeState,
        entity: EntityState
    ) -> StrategicUpdate:
        """
        Pillar 5.1: Strategic Redirection.
        Evaluates environment to propose or resume long-term projects.
        """
        current_tick = state.tick
        strat = entity.strategic
        
        # PH6: Clear exhausted leads from memory
        from src_legacy.systems.detour import DetourSuggestionSystem
        exhaust_up = DetourSuggestionSystem.suppress_exhausted_leads(entity)
        
        # 0. Boredom Increment (Always happens if active)
        boredom_upd = {}
        if strat.current_project_id:
            proj = strat.projects.get(strat.current_project_id)
            if proj and proj.status == ProjectStatus.ACTIVE:
                # Ticking an active project increases boredom by 0.1
                boredom_upd[proj.kind] = 0.1
        
        # 1. Check for project completion or failure
        if strat.current_project_id:
            project = strat.projects.get(strat.current_project_id)
            if project and project.status == ProjectStatus.ACTIVE:
                # If harvesting and node is gone, complete it
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
        
        # 2. Strategic Scoring (Always evaluate to allow switching)
        from src_legacy.ai.goals import GoalRegistry
        from src_legacy.ai.score_modifiers import ScoreModifierSystem
        from src_legacy.systems.detour import DetourSuggestionSystem
        
        all_scores = GoalRegistry.get_all_scores(entity, state)
        
        # PH5 M2: Apply Modifiers
        modified_scores = ScoreModifierSystem.apply_modifiers(entity, state, all_scores)
        
        # PH6: Detour Integration
        detours = DetourSuggestionSystem.suggest_detours(entity, current_tick)
        for detour in detours:
             # Convert detour to a goal-like score for comparison
             from src_legacy.ai.goals import GoalScore
             # We give detours a slight priority if they are relevant to a high-severity blocker
             modified_scores.append(GoalScore(
                 kind=detour.objective_kind,
                 utility=detour.score,
                 target_id=detour.target,
                 metadata={"lead_id": detour.lead_id}
             ))

        modified_scores.sort(key=lambda x: x.utility, reverse=True)
        
        best_candidate = None
        for g_score in modified_scores:
            if g_score.utility < 20.0 or g_score.target_id is None:
                continue
            best_candidate = g_score
            break
            
        if best_candidate:
            # Check if we already have this kind of project
            existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)
            
            if existing and existing.status == ProjectStatus.SUSPENDED:
                # Resume logic
                resumed_up = StrategicIntelligenceSystem.resume_project(entity, existing.id)
                if resumed_up:
                    final_resumed = replace(resumed_up, boredom_delta=boredom_upd)
                    return replace(final_resumed, 
                        leads_add_or_update=final_resumed.leads_add_or_update + exhaust_up.leads_add_or_update
                    )
            
            # Create a candidate project object for evaluation
            from src_legacy.core.strategic import ObjectiveState, ObjectiveStatus
            lead_id = best_candidate.metadata.get("lead_id") if hasattr(best_candidate, "metadata") and best_candidate.metadata else None
            
            obj = ObjectiveState(
                id=f"{best_candidate.kind}_{best_candidate.target_id}",
                kind=best_candidate.kind if lead_id else "reach_location", # Detours use their own kind
                target=best_candidate.target_id,
                status=ObjectiveStatus.ACTIVE,
                lead_id=lead_id
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
            
            # Check for switch
            at_capacity = len(strat.projects) >= strat.profile.max_active_projects
            if at_capacity and not existing:
                # Still merge boredom and exhaust if we can't switch
                return replace(exhaust_up, boredom_delta=boredom_upd)

            switch_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate_proj, current_tick)
            if switch_up:
                final_switch = replace(switch_up, boredom_delta=boredom_upd)
                return replace(final_switch,
                    leads_add_or_update=final_switch.leads_add_or_update + exhaust_up.leads_add_or_update
                )

        # Fallback return: Merge boredom and lead suppression
        return replace(exhaust_up, boredom_delta=boredom_upd)

    @staticmethod
    def derive_cognition_profile(entity: EntityState) -> CognitionProfile:
        """
        Derive cognition profile from entity attributes.
        Deterministic: same entity state always produces the same profile.
        """
        return CapacityService.derive_profile(entity)
