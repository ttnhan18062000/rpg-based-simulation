from __future__ import annotations
from typing import Optional
from src_legacy.core.state import EntityState
from src_legacy.core.strategic import LeadState, LeadCertainty


class LeadService:
    """
    Authoritative management of strategic leads and uncertainty.
    """

    @staticmethod
    def create_lead(
        entity: EntityState,
        kind: str,
        subject: str,
        detail: str = "",
        source_id: Optional[int] = None,
        tick: int = 0
    ) -> Optional[LeadState]:
        """
        Create a new lead if within capacity limits.
        Certainty is derived from source trust.
        """
        strat = entity.strategic
        profile = strat.profile
        
        if len(strat.leads) >= profile.max_leads:
            return None
            
        # Determine certainty from source trust
        certainty = LeadCertainty.VAGUE
        if source_id is not None:
            trust_entry = strat.source_trust.get(source_id)
            if trust_entry:
                if trust_entry.trust > 0.8:
                    certainty = LeadCertainty.PRECISE
                elif trust_entry.trust > 0.4:
                    certainty = LeadCertainty.APPROXIMATE
        
        return LeadState(
            id=f"lead_{kind}_{subject}_{tick}",
            kind=kind,
            subject=subject,
            detail=detail,
            discovered_tick=tick,
            certainty=certainty,
            source_entity_id=source_id
        )

    @staticmethod
    def evaluate_lead_outcome(lead: LeadState, success: bool) -> LeadState:
        """Update lead state based on a test/investigation outcome."""
        return LeadState(
            id=lead.id,
            kind=lead.kind,
            subject=lead.subject,
            detail=lead.detail,
            discovered_tick=lead.discovered_tick,
            certainty=LeadCertainty.EXHAUSTED if not success else lead.certainty,
            source_entity_id=lead.source_entity_id,
            tested=True,
            test_outcome="SUCCESS" if success else "FAILURE"
        )
