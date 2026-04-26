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
        from src.systems.routine import RoutineService
        
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
        from src.systems.routine import RoutineService
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
        from src.systems.social import SocialAppraisalSystem

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
        
        # PH5 M2: Boredom Increment (Always happens if active)
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
                
                # Phase 6: Blocker & Detour Check
                # If current project has any blockers, look for detours
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
                            score=best.score + 50.0 # High priority for detours
                        )
                        detour_up = StrategicIntelligenceSystem.evaluate_project_switch(entity, detour_proj, current_tick)
                        if detour_up:
                            if boredom_upd:
                                detour_up = replace(detour_up, boredom_delta=boredom_upd)
                            return detour_up
        
        # 2. Strategic Scoring (Always evaluate to allow switching)
        from src.ai.goals import GoalRegistry
        from src.ai.score_modifiers import ScoreModifierSystem
        all_scores = GoalRegistry.get_all_scores(entity, state)
        
        # PH5 M2: Apply Modifiers
        modified_scores = ScoreModifierSystem.apply_modifiers(entity, state, all_scores)
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
                    if boredom_upd:
                        resumed_up = replace(resumed_up, boredom_delta=boredom_upd)
                    return resumed_up
            
            # Create a candidate project object for evaluation
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
            
            # Check for switch
            # Capacity Check: If already at max projects, only allow switching if existing
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

        return StrategicUpdate()

    @staticmethod
    def derive_cognition_profile(entity: EntityState) -> CognitionProfile:
        """
        Derive cognition profile from entity attributes.
        Deterministic: same entity state always produces the same profile.
        """
        return CapacityService.derive_profile(entity)
