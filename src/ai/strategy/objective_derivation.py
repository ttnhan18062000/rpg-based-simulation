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
    from src.ai.strategy.blocker_inference import BlockerInferenceService
    from src.ai.strategy.detour_suggestion import DetourSuggestionService

logger = logging.getLogger(__name__)

class ObjectiveDerivationService:
    """Derives actionable objectives from projects and handles concern promotion. [phase_2_stage_5]"""

    def __init__(self, blocker_inference: BlockerInferenceService, detour_suggestion: DetourSuggestionService):
        self.blocker_inference = blocker_inference
        self.detour_suggestion = detour_suggestion

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
            decision.updates.project_lock_until = current_tick + 50
            if ctx.strategic.current_project_id:
                decision.updates.interrupted_project_id = ctx.strategic.current_project_id
            
            decision.updates.projects_add_or_update.append(prj.model_copy(update={
                "committed_at": current_tick
            }))

        # 2. Find or derive active objective
        active_obj = None
        if prj.active_objective_id:
            active_obj = next((o for o in prj.objectives if o.objective_id == prj.active_objective_id), None)
            
        # 2.5 Automated Blocker Inference & Detour Spawning [phase_3_task_7]
        if active_obj and active_obj.status == StrategicStatus.ACTIVE:
            # Check for structural blockers (Knowledge, Capability, etc.)
            inferred = self.blocker_inference.infer_blockers(ctx, active_obj)
            
            # Combine with existing blockers in the objective
            all_blockers = list(active_obj.blockers)
            was_updated = False
            for b in inferred:
                 if not any(eb.kind == b.kind for eb in all_blockers):
                      all_blockers.append(b)
                      was_updated = True
            
            if was_updated:
                 # Proactively update the objective with new blockers
                 active_obj = active_obj.model_copy(update={"blockers": all_blockers})
            
            # Check if any blocker needs a detour (newly found or existing)
            for blocker in all_blockers:
                 if blocker.resolved: continue
                 
                 detours = self.detour_suggestion.suggest_detours(ctx, blocker, prj.project_id)
                 if detours:
                      # We found a detour! Check if it's already in the project and active.
                      detour = detours[0]
                      existing_detour = next((o for o in prj.objectives if o.objective_id == detour.objective_id), None)
                      
                      if existing_detour and existing_detour.status == StrategicStatus.ACTIVE:
                           # Already pursuing this detour. Just make sure it's current.
                           if ctx.strategic.current_objective_id != existing_detour.objective_id:
                                decision.updates.current_objective_id = existing_detour.objective_id
                           return
                      
                      # Propose project update with new/reactivated detour
                      updated_prj = prj.model_copy()
                      # Synch the blocked objective (if it was updated)
                      for i, o in enumerate(updated_prj.objectives):
                           if o.objective_id == active_obj.objective_id:
                                updated_prj.objectives[i] = active_obj
                                break
                      
                      # Add/Reactivate the detour
                      updated_prj.objectives = [o for o in updated_prj.objectives if o.objective_id != detour.objective_id]
                      updated_prj.objectives.append(detour)
                      updated_prj.active_objective_id = detour.objective_id
                      
                      decision.updates.projects_add_or_update.append(updated_prj)
                      decision.updates.current_objective_id = detour.objective_id
                      return # Detour created, move to next tick

        # If no active objective or the active one is resolved/abandoned, find the next one
        if not active_obj or active_obj.status != StrategicStatus.ACTIVE:
            next_obj = next((o for o in prj.objectives if o.status == StrategicStatus.ACTIVE), None)
            
            if next_obj:
                decision.updates.current_objective_id = next_obj.objective_id
            else:
                if prj.status == StrategicStatus.ACTIVE:
                     # Project cleanup/fallback could go here
                     pass
        else:
            if ctx.strategic.current_objective_id != active_obj.objective_id:
                 decision.updates.current_objective_id = active_obj.objective_id
