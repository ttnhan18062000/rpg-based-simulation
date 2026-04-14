from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.core.models.strategy import LeadRecord, StrategicStatus
from src.actions.base import StrategicUpdate

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.ai.cognition_capacity import CognitionCapacityProfile

logger = logging.getLogger(__name__)

class StrategicLearningService:
    """Handles trust recalibration and lead confidence updates based on outcomes. [phase_3_task_1]"""

    @staticmethod
    def process_lead_outcome(ctx: AIContext, lead: LeadRecord, success: bool, profile: CognitionCapacityProfile) -> StrategicUpdate:
        """Updates lead certainty and source trust based on a tested outcome."""
        actor = ctx.actor
        strat = actor.mind.strategic
        up = StrategicUpdate(target_id=actor.id)
        
        # 1. Update Lead Certainty
        # Contradiction sensitivity scales how much we drop certainty on failure
        # and how much we gain on success.
        delta = 0.2 + (profile.contradiction_sensitivity * 0.4)
        if not success:
            new_certainty = max(0.0, lead.certainty - delta)
            new_contradictions = lead.contradiction_count + 1
            logger.info("Lead %s refuted. Certainty: %.2f -> %.2f", lead.lead_id, lead.certainty, new_certainty)
        else:
            new_certainty = min(1.0, lead.certainty + (delta * 0.5))
            new_contradictions = lead.contradiction_count
            logger.info("Lead %s confirmed. Certainty: %.2f -> %.2f", lead.lead_id, lead.certainty, new_certainty)
            
        updated_lead = lead.model_copy(update={
            "certainty": new_certainty,
            "contradiction_count": new_contradictions,
            "tested": True,
            "is_exhausted": not success # If it failed, it's exhausted. If success, it might still have more? 
                                        # Usually success means the objective is done.
        })
        # Update the lead in strategic updates
        up.leads_add_or_update.append(updated_lead)
        up.tested_lead_ids.append(lead.lead_id)
        
        # Recalibrate Source Trust
        source_id = lead.source_id
        if source_id:
            current_trust = ctx.strategic.source_trust.get(source_id, 0.5)
            if success:
                # Success: Boost trust based on learning rate (max 1.0)
                new_trust = min(1.0, current_trust + (1.0 - current_trust) * profile.source_trust_learning_rate)
            else:
                # Failure: Penalize trust based on learning rate AND contradiction sensitivity
                penalty = profile.source_trust_learning_rate * profile.contradiction_sensitivity
                new_trust = max(0.0, current_trust - penalty)
            
            up.source_trust_updates[source_id] = new_trust
            
        return up
