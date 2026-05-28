"""
src/domains/information/contradiction.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — BeliefContradictionService

Detects matched claims vs direct world observations, weakening certainty factor
on mismatch.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import LeadCertainty

@dataclass(frozen=True, slots=True)
class BeliefContradictionResult:
    contradiction_detected: bool
    lead_id: Optional[str]
    old_certainty: Optional[LeadCertainty]
    new_certainty: Optional[LeadCertainty]
    reason: Optional[str]


class BeliefContradictionService:
    """
    Evaluates claims vs direct observation events.
    """

    @staticmethod
    def detect(
        entity: EntityState,
        observation: Dict[str, Any],
        state: AuthoritativeState,
    ) -> BeliefContradictionResult:
        """
        Check if observation contradicts any active strategic lead.
        """
        obs_kind = observation.get("kind")
        subj = observation.get("subject")
        pos = observation.get("position")

        strat = getattr(entity, "strategic", None)
        leads = getattr(strat, "leads", {}) or {}

        for lead in leads.values():
            if lead.subject == subj and lead.certainty != LeadCertainty.EXHAUSTED:
                # Direct check: if search failed
                if obs_kind == "claim_failed_search" and lead.detail == observation.get("location_searched"):
                    return BeliefContradictionResult(
                        contradiction_detected=True,
                        lead_id=lead.id,
                        old_certainty=lead.certainty,
                        new_certainty=LeadCertainty.EXHAUSTED,
                        reason=f"Failed search in {lead.detail} contradicted lead {lead.id}.",
                    )

                # Direct check: safe rumor observed dangerous
                if obs_kind == "region_danger_seen" and lead.detail == observation.get("region_id"):
                    if lead.certainty in (LeadCertainty.VAGUE, LeadCertainty.APPROXIMATE):
                        return BeliefContradictionResult(
                            contradiction_detected=True,
                            lead_id=lead.id,
                            old_certainty=lead.certainty,
                            new_certainty=LeadCertainty.EXHAUSTED,
                            reason="Observed danger contradicted safe rumors.",
                        )

        return BeliefContradictionResult(
            contradiction_detected=False,
            lead_id=None,
            old_certainty=None,
            new_certainty=None,
            reason=None,
        )
