from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from src.core.models.strategy import StrategicStatus, ProjectRecord, ConcernRecord
from src.actions.base import StrategicUpdate

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.ai.strategy.candidate_builder import StrategicCandidate

logger = logging.getLogger(__name__)

@dataclass
class StrategicDecision:
    """The result of a strategic evaluation pass."""
    selected_id: str
    selected_kind: str # "project" or "concern"
    reason: str
    updates: StrategicUpdate = field(default_factory=StrategicUpdate)
    
    # Traceability
    scores: dict[str, float] = field(default_factory=dict)
    interrupted_id: Optional[str] = None

class StrategicEvaluator:
    """Refined strategic appraisal logic using decomposed service topology.
    
    This implements phase_2_stage_2. It orchestrates candidate selection,
    interruption analysis, and objective derivation.
    """

    def __init__(self):
        # We will inject these or instantiate them as needed [phase_2_stage_2]
        from src.ai.strategy.interruption import StrategicInterruptionService
        from src.ai.strategy.objective_derivation import ObjectiveDerivationService
        from src.ai.strategy.blocker_inference import BlockerInferenceService
        from src.ai.strategy.detour_suggestion import DetourSuggestionService
        
        self.interruption_service = StrategicInterruptionService()
        self.blocker_inference = BlockerInferenceService()
        self.detour_suggestion = DetourSuggestionService()
        self.objective_service = ObjectiveDerivationService(
            self.blocker_inference, 
            self.detour_suggestion
        )

    def evaluate(self, ctx: AIContext, candidates: list[StrategicCandidate]) -> StrategicDecision:
        """Evaluate the active decision slice and determine the core commitment."""
        if not candidates:
            return StrategicDecision(selected_id="", selected_kind="none", reason="No candidates surfaced")

        # 1. Score Interruption [phase_2_stage_7]
        # Compare current project commitment against incoming concern pressure.
        best_candidate = self.interruption_service.find_best_commitment(ctx, candidates)
        
        if not best_candidate:
            return StrategicDecision(selected_id="", selected_kind="none", reason="No suitable candidate after interruption check")

        # 2. Derive Update Basics
        selected_id = getattr(best_candidate, "project_id", None) or getattr(best_candidate, "concern_id", None)
        selected_kind = "project" if isinstance(best_candidate, ProjectRecord) else "concern"
        
        decision = StrategicDecision(
            selected_id=selected_id or "",
            selected_kind=selected_kind,
            reason=f"Selected {selected_kind} {selected_id} via interruption appraisal."
        )

        # 2.2 Handle Project Interruption semantics [PHASE 5]
        if ctx.current_project and selected_id != ctx.current_project.project_id:
             old_prj = ctx.current_project
             # We mark the old project as suspended if we are switching to something else
             suspended_prj = old_prj.model_copy(update={
                 "status": StrategicStatus.SUSPENDED,
                 "suspension_reason": decision.reason,
                 "interrupted_by_event_ids": [getattr(best_candidate, "source_event_id", "external")] if hasattr(best_candidate, "source_event_id") else ["external"]
             })
             decision.updates.projects_add_or_update.append(suspended_prj)
             decision.updates.interrupted_project_id = old_prj.project_id
             logger.info("StrategicEvaluator: Interrupting project %s in favor of %s", old_prj.project_id, selected_id)

        # 2.5 Persist new concerns [STAGE 4 RESTORATION]
        # Any concern that was sensed but isn't in state needs to be added to the update
        current_concern_ids = {c.concern_id for c in ctx.strategic.concerns}
        for cand in candidates:
            if isinstance(cand, ConcernRecord) and cand.concern_id not in current_concern_ids:
                decision.updates.concerns_add_or_update.append(cand)

        # 3. Objective Derivation [phase_2_stage_5]
        # This will populate decision.updates and ensure project/objective ids are sent correctly.
        self.objective_service.apply_derivation(ctx, best_candidate, decision)

        # 4. Cleanup Resolved Concerns & Objectives [STAGE 4 RESTORATION]
        self._cleanup_strategic_state(ctx, candidates, decision)
        
        # 5. Finalize finish-markers
        if ctx.current_objective and ctx.current_objective.status == StrategicStatus.RESOLVED:
             # If we haven't already updated current_objective_id, clearing it will trigger 
             # the derivation service to pick the next one in the next tick.
             if not decision.updates.current_objective_id:
                  decision.updates.current_objective_id = ""

        return decision

    def _cleanup_strategic_state(self, ctx: AIContext, candidates: list[StrategicCandidate], decision: StrategicDecision):
        """Resolves strategic elements that are no longer valid."""
        # 1. Concern Cleanup (World Events) [STAGE 4 RESTORATION]
        # We look for concerns that are active in state but no longer sensed
        # by the world-tier sensing logic.
        
        # Re-sense world events (or we could have passed them in)
        from src.ai.strategy.candidate_builder import StrategicCandidateBuilder
        sensed = StrategicCandidateBuilder._sense_world_events(ctx)
        sensed_ids = {c.concern_id for c in sensed}
        
        # Monitor specific world-tier concerns
        managed_concern_ids = {"concern_regional_threat", "concern_nearby_scar"}
        
        for active_c in ctx.active_concerns:
            if active_c.concern_id in managed_concern_ids:
                if active_c.concern_id not in sensed_ids:
                    # Condition no longer met (e.g. moved away from scar, or danger low)
                    decision.updates.concerns_remove.append(active_c.concern_id)
                    
                    # If this was our current project (via promotion), we might need to clear it
                    if ctx.strategic.current_project_id == f"project_stabilization" and active_c.concern_id == "concern_regional_threat":
                         # The project will likely be swapped in the next tick anyway
                         # but we can be proactive.
                         pass
