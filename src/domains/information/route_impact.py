"""
src/domains/information/route_impact.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — BeliefRouteImpactService

Connects updated knowledge facts or contradicted leads back to route family scoring
to naturally redirect adventure choices.
"""

from __future__ import annotations
from typing import Dict, Any, Optional

from src.core.state import EntityState
from src.core.strategic import BlockerState, BlockerKind
from src.domains.information.schema import InformationAssimilationResult, RouteImpactHint


class BeliefRouteImpactService:
    """
    Connects updated beliefs to score triggers for Phase 3 Route generators.
    """

    @staticmethod
    def evaluate_impact(
        entity_before: EntityState,
        entity_after: EntityState,
        assimilation_result: InformationAssimilationResult,
    ) -> RouteImpactHint:
        """
        Produce route family boost or invalidation flags based on new knowledge.
        """
        invalidated: list[str] = []
        boosted: list[str] = []
        new_blockers: list[BlockerState] = []
        resolved_blockers: list[str] = []

        trace = assimilation_result.trace
        answer_kind = trace.get("answer_kind")

        # 1. If we successfully resolved a material blocker by learning its source
        if answer_kind == "KNOWN_FACT":
            boosted.append("gather_resource")
            boosted.append("reach_location")
            resolved_blockers.append("unknown_material_source")

        # 2. If we recorded a partial clue lead, boost scout routes instead of direct gather
        elif answer_kind == "PARTIAL_LEAD" or answer_kind == "RUMOR":
            boosted.append("scout_location")
            boosted.append("investigate")
            new_blockers.append(
                BlockerState(
                    id="unverified_lead_blocker",
                    kind=BlockerKind.ACCESS,
                    subject="unverified_lead",
                )
            )

        # 3. If a lead was contradicted (failed search), weaken or invalidate that scout family
        elif answer_kind == "CONTRADICTION":
            invalidated.append("scout_location")
            resolved_blockers.append("unverified_lead_blocker")

        return RouteImpactHint(
            invalidated_route_families=tuple(invalidated),
            boosted_route_families=tuple(boosted),
            new_blockers=tuple(new_blockers),
            resolved_blockers=tuple(resolved_blockers),
            reason=f"Route choices adapted based on {answer_kind} belief update.",
        )
