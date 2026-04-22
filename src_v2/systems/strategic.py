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
from dataclasses import replace
from typing import Dict, List, Optional

from src_v2.core.state import EntityState, AuthoritativeState
from src_v2.core.updates import (
    StrategicUpdate, InventoryUpdate, EntityUpdate, StateUpdate
)
from src_v2.core.strategic import (
    BlockerState, LeadState, LeadCertainty,
    ProjectState, ProjectStatus, ObjectiveState,
    CognitionProfile
)


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
            have = inv.items.count(mat_id)
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
                items_added.extend(ent_upd.inventory.items_added)

            if not items_added:
                continue

            # Scan for material blockers matching added items
            resolved_ids = []

            # Combine current blockers and proposed additions for resolution check
            active_blocker_ids = set(entity.strategic.blockers.keys())
            if ent_upd.strategic:
                active_blocker_ids.update(b.id for b in ent_upd.strategic.blockers_add_or_update)

            for item in items_added:
                blocker_id = f"blocker_mat_{item}"
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
                    # Find any lead with this subject
                    for l_id, lead in entity.strategic.leads.items():
                         if lead.subject == item:
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
        from src_v2.systems.routine import RoutineService
        from src_v2.core.updates import StrategicUpdate, EntityUpdate
        
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
                    concerns_add_or_update=strat_up.concerns_add_or_update + concerns
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
        from src_v2.systems.routine import RoutineService
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
        from src_v2.systems.social import SocialAppraisalSystem
        from src_v2.core.updates import EntityUpdate, StateUpdate

        outcome_quality = 1.0 if success else -1.0
        social_up = SocialAppraisalSystem.recalibrate_trust(observer, subject_id, outcome_quality)

        # In a real integration, this would be part of a larger resolution update.
        # For Milestone 7, we return the social update wrapped in a generic update container.
        return social_up

    @staticmethod
    def derive_cognition_profile(entity: EntityState) -> CognitionProfile:
        """
        Derive cognition profile from entity attributes.
        Deterministic: same entity state always produces the same profile.

        Uses properties dict for WIS/INT if available, otherwise defaults.
        """
        wis = entity.properties.get("wis", 10)
        int_stat = entity.properties.get("int", 10)
        level = entity.identity.evolution_level

        # Scale capacities with attributes
        base_projects = 2 + (int_stat // 10)
        base_leads = 5 + (wis // 5)
        base_concerns = 3 + (wis // 8)
        base_zones = 3 + (int_stat // 12)
        base_hypotheses = 2 + (int_stat // 15)

        # Interruption resistance scales with wisdom and level
        resistance = min(0.8, 0.2 + (wis * 0.01) + (level * 0.02))

        # Detour limits scale with intelligence
        breadth = max(1, 2 + (int_stat // 15))
        depth = max(1, 1 + (int_stat // 20))

        return CognitionProfile(
            max_active_projects=min(6, base_projects),
            max_leads=min(15, base_leads),
            max_concerns=min(8, base_concerns),
            max_candidate_zones=min(8, base_zones),
            max_hypotheses=min(6, base_hypotheses),
            interruption_resistance=resistance,
            detour_breadth=min(5, breadth),
            detour_depth=min(3, depth)
        )
