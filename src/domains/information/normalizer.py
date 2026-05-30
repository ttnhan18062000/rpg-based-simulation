"""
src/domains/information/normalizer.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — InformationResponseNormalizer

Normalizes distinct response schemas into a standard format containing
KnowledgeFact, LeadState, UnknownFact, or contradictions.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any

from src.core.self_model import KnowledgeFact, UnknownFact
from src.core.strategic import LeadState, LeadCertainty
from src.domains.information.schema import (
    InformationQuery,
    NormalizedInformationResponse,
)


class InformationResponseNormalizer:
    """
    Standardizes information responses into standard types.
    """

    @staticmethod
    def normalize(
        query: InformationQuery,
        source_id: str | int,
        raw_response: Dict[str, Any],
        cost_paid: int = 0,
        current_tick: int = 0,
    ) -> NormalizedInformationResponse:
        """
        Produce a NormalizedInformationResponse from the raw response structure.
        """
        answer_kind = raw_response.get("answer_kind", "UNKNOWN")
        certainty = float(raw_response.get("certainty", 0.0))
        details = raw_response.get("details", {}) or {}
        reason = raw_response.get("reason")

        facts: List[KnowledgeFact] = []
        leads: List[LeadState] = []
        unknowns: List[UnknownFact] = []
        contradiction_targets: List[str] = []

        if answer_kind == "KNOWN_FACT":
            facts.append(
                KnowledgeFact(
                    subject=query.subject,
                    fact_type=query.kind,
                    details=details,
                    certainty=certainty,
                    source_id=str(source_id),
                    recorded_tick=current_tick,
                )
            )

        elif answer_kind == "PARTIAL_LEAD":
            lead_id = f"lead_{query.subject}_{current_tick}"
            leads.append(
                LeadState(
                    id=lead_id,
                    kind="location",
                    subject=query.subject,
                    detail=details.get("clue_location", ""),
                    discovered_tick=current_tick,
                    certainty=LeadCertainty.APPROXIMATE,
                    source_entity_id=source_id if isinstance(source_id, int) else None,
                )
            )

        elif answer_kind == "RUMOR":
            lead_id = f"rumor_{query.subject}_{current_tick}"
            leads.append(
                LeadState(
                    id=lead_id,
                    kind="location",
                    subject=query.subject,
                    detail=details.get("clue_location", ""),
                    discovered_tick=current_tick,
                    certainty=LeadCertainty.VAGUE,
                    source_entity_id=source_id if isinstance(source_id, int) else None,
                )
            )

        elif answer_kind == "CONTRADICTION":
            contradiction_targets = list(raw_response.get("contradiction_targets", []) or [])

        else:
            unknowns.append(
                UnknownFact(
                    subject=query.subject,
                    reason=reason or "never_queried",
                    recorded_tick=current_tick,
                )
            )

        return NormalizedInformationResponse(
            query=query,
            source_id=source_id,
            answer_kind=answer_kind,
            facts=tuple(facts),
            leads=tuple(leads),
            unknowns=tuple(unknowns),
            certainty=round(certainty, 2),
            contradiction_targets=tuple(contradiction_targets),
            cost_paid_gold=cost_paid,
            reason=reason,
        )
