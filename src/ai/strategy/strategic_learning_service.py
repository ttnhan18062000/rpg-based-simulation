from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.core.models.strategy import LeadRecord, StrategicStatus
from src.actions.base import StrategicUpdate, SocialEventUpdate
from src.core.logic.event_interpreter import EventInterpreterService

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.ai.cognition_capacity import CognitionCapacityProfile

logger = logging.getLogger(__name__)

class StrategicLearningService:
    """Handles trust recalibration and lead confidence updates based on outcomes. [phase_3_task_1]"""

    @staticmethod
    def process_lead_outcome(ctx: AIContext, lead: LeadRecord, success: bool, profile: CognitionCapacityProfile) -> list:
        """Updates lead certainty and source trust based on a tested outcome, generating social events. [PHASE 3]"""
        actor = ctx.actor
        strat = actor.mind.strategic
        up = StrategicUpdate(target_id=actor.id)
        updates = [up]
        
        # 1. Update Lead Certainty
        delta = 0.2 + (profile.contradiction_sensitivity * 0.4)
        if not success:
            new_certainty = max(0.0, lead.certainty - delta)
            new_contradictions = lead.contradiction_count + 1
        else:
            new_certainty = min(1.0, lead.certainty + (delta * 0.5))
            new_contradictions = lead.contradiction_count
            
        updated_lead = lead.model_copy(update={
            "certainty": new_certainty,
            "contradiction_count": new_contradictions,
            "tested": True,
            "is_exhausted": True
        })
        up.leads_add_or_update.append(updated_lead)
        up.tested_lead_ids.append(lead.lead_id)
        
        # 2. Recalibrate Source Trust & Social Events
        source_id = lead.source_id
        if source_id:
            current_trust = ctx.strategic.source_trust.get(source_id, 0.5)
            if success:
                new_trust = min(1.0, current_trust + (1.0 - current_trust) * profile.source_trust_learning_rate)
                # Success Event
                evt = EventInterpreterService.interpret_intel_confirmation(actor, source_id, ctx.snapshot.tick, ctx.rng)
                updates.append(SocialEventUpdate(events_add=[evt]))
            else:
                penalty = profile.source_trust_learning_rate * profile.contradiction_sensitivity
                new_trust = max(0.0, current_trust - penalty)
                # Refutation Event
                evt = EventInterpreterService.interpret_intel_refutation(actor, source_id, ctx.snapshot.tick, ctx.rng)
                updates.append(SocialEventUpdate(events_add=[evt]))
            
            up.source_trust_updates[source_id] = new_trust
            
        return updates
