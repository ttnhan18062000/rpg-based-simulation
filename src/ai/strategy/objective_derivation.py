from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from src.core.models.strategy import (
    ProjectRecord, ConcernRecord, ObjectiveRecord, 
    StrategicStatus, ProjectKind, ObjectiveKind, ConcernKind
)

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.ai.strategy.strategic_evaluator import StrategicDecision

logger = logging.getLogger(__name__)

class ObjectiveDerivationService:
    """Derives actionable objectives from projects and handles concern promotion.
    
    This implements phase_2_stage_5. It ensures the strategic layer always
    outputs something the tactical layer can understand.
    """

    def apply_derivation(self, ctx: AIContext, winner: ProjectRecord | ConcernRecord, decision: StrategicDecision):
        """Ensures the selected commitment is actionable."""
        if isinstance(winner, ConcernRecord):
            self._handle_concern_promotion(ctx, winner, decision)
        else:
            self._handle_project_objectives(ctx, winner, decision)

    def _handle_concern_promotion(self, ctx: AIContext, concern: ConcernRecord, decision: StrategicDecision):
        """Converts an immediate concern into a temporary project."""
        current_tick = ctx.snapshot.tick
        
        if ctx.strategic.current_project_id:
            decision.updates.interrupted_project_id = ctx.strategic.current_project_id
            
        # Survival Concern
        if "survival" in concern.concern_id:
            prj_id = "project_survival"
            decision.selected_id = prj_id
            decision.selected_kind = "project"
            
            # Create survival project if it doesn't exist
            if not any(p.project_id == prj_id for p in ctx.strategic.projects):
                prj = ProjectRecord(
                    project_id=prj_id,
                    kind=ProjectKind.SOCIAL,
                    label="Ensure Survival",
                    priority=5.0,
                    urgency=1.0,
                    created_tick=current_tick
                )
                obj = ObjectiveRecord(
                    objective_id="obj_satisfy_needs",
                    project_id=prj_id,
                    kind=ObjectiveKind.INTERACT,
                    label="Find food or rest",
                    priority=5.0,
                    created_tick=current_tick
                )
                prj.objectives.append(obj)
                prj.active_objective_id = obj.objective_id
                decision.updates.projects_add_or_update.append(prj)
                
            decision.updates.current_project_id = prj_id
            decision.updates.current_objective_id = "obj_satisfy_needs"
            # Note: We let _handle_project_objectives handle the active_objective_id if prj already exists
            # but for a new one we set it here.
            
        # Regional Threat
        elif "regional_threat" in concern.concern_id:
            prj_id = "project_stabilization"
            decision.selected_id = prj_id
            decision.selected_kind = "project"
            
            if not any(p.project_id == prj_id for p in ctx.strategic.projects):
                prj = ProjectRecord(
                    project_id=prj_id,
                    kind=ProjectKind.SOCIAL,
                    label="Restore Regional Order",
                    priority=5.0,
                    urgency=0.9,
                    created_tick=current_tick
                )
                obj = ObjectiveRecord(
                    objective_id="obj_stabilize_region",
                    project_id=prj_id,
                    kind=ObjectiveKind.INTERACT,
                    label="Address Crisis",
                    priority=5.0,
                    created_tick=current_tick
                )
                prj.objectives.append(obj)
                prj.active_objective_id = obj.objective_id
                decision.updates.projects_add_or_update.append(prj)
                
            decision.updates.current_project_id = prj_id
            decision.updates.current_objective_id = "obj_stabilize_region"

    def _handle_project_objectives(self, ctx: AIContext, prj: ProjectRecord, decision: StrategicDecision):
        """Ensures a project has an active and valid objective."""
        current_tick = ctx.snapshot.tick
        
        # 1. Update project selection in strat state if needed
        if ctx.strategic.current_project_id != prj.project_id:
            decision.updates.current_project_id = prj.project_id
            
            # Start continuity lock [phase_2_stage_3]
            # Lock the project for 50 ticks to prevent flip-flopping
            decision.updates.project_lock_until = current_tick + 50
            
            # Record that we interrupted something if applicable
            if ctx.strategic.current_project_id:
                decision.updates.interrupted_project_id = ctx.strategic.current_project_id
            
            # Initialize commitment timestamp
            decision.updates.projects_add_or_update.append(prj.model_copy(update={
                "committed_at": current_tick
            }))

        # 2. Find or derive active objective
        active_obj = None
        if prj.active_objective_id:
            active_obj = next((o for o in prj.objectives if o.objective_id == prj.active_objective_id), None)
            
        # 2.5 Detour Logic [phase_2_stage_5]
        # If the active objective is blocked, we might need a detour.
        if active_obj and active_obj.status == StrategicStatus.ACTIVE:
            blocker = next((b for b in active_obj.blockers), None)
            if blocker:
                # If blocked by knowledge, look for a lead (rumor/hint)
                from src.core.models.strategy import BlockerKind
                if blocker.kind == BlockerKind.KNOWLEDGE:
                    best_lead = self._find_best_lead(ctx)
                    if best_lead:
                        # Found a lead! Propose a detour investigation objective.
                        self._create_investigation_detour(ctx, prj, best_lead, decision)
                        return # Detour created, we are done for this tick

        # If no active objective or the active one is resolved/abandoned, find the next one
        if not active_obj or active_obj.status != StrategicStatus.ACTIVE:
            next_obj = next((o for o in prj.objectives if o.status == StrategicStatus.ACTIVE), None)
            
            if next_obj:
                decision.updates.current_objective_id = next_obj.objective_id
            else:
                # Task 5: Fallback objective derivation
                # If project is empty, we must resolve it or add a generic objective
                # For now, let's just log it and potentially resolve the project
                if prj.status == StrategicStatus.ACTIVE:
                     # This is where we would add logical next steps (VISIT town, etc.)
                     # For now, we'll just keep it simple.
                     pass
        else:
            # Objective exists and is active. Ensure the brain knows about it.
            if ctx.strategic.current_objective_id != active_obj.objective_id:
                 decision.updates.current_objective_id = active_obj.objective_id

    def _find_best_lead(self, ctx: AIContext):
        """Finds the most salient lead available. [phase_2_stage_5]"""
        leads = [l for l in ctx.strategic.leads if not l.is_exhausted]
        if not leads:
            return None
        # Simply pick the newest or highest priority
        return sorted(leads, key=lambda l: l.discovered_tick, reverse=True)[0]

    def _create_investigation_detour(self, ctx: AIContext, prj: ProjectRecord, lead: LeadRecord, decision: StrategicDecision):
        """Spawns an investigative detour objective. [phase_2_stage_5]"""
        current_tick = ctx.snapshot.tick
        detour_id = f"detour_investigate_{lead.lead_id}"
        
        # Check if already exists in project
        existing = next((o for o in prj.objectives if o.objective_id == detour_id), None)
        if existing:
            if existing.status != StrategicStatus.ACTIVE:
                 # Reactivate if needed
                 existing.status = StrategicStatus.ACTIVE
            decision.updates.current_objective_id = detour_id
            return

        # Create new detour objective
        detour = ObjectiveRecord(
            objective_id=detour_id,
            project_id=prj.project_id,
            kind=ObjectiveKind.INVESTIGATE,
            label=f"Investigate Lead: {lead.label}",
            priority=prj.priority + 1.0,
            target_pos=lead.target_coords,
            created_tick=current_tick
        )
        
        # Clone project to add objective (AOA Authoritative Update pattern)
        new_prj = prj.model_copy()
        new_prj.objectives.append(detour)
        new_prj.active_objective_id = detour_id
        
        decision.updates.projects_add_or_update.append(new_prj)
        decision.updates.current_objective_id = detour_id
