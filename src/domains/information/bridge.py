"""
src/domains/information/bridge.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — ObservationBeliefBridge

Converts raw observation events into subjective high-certainty beliefs.
"""

from __future__ import annotations
from dataclasses import replace as _replace
from typing import Dict, Any

from src.core.state import EntityState, AuthoritativeState
from src.core.updates import StrategicUpdate
from src.domains.information.schema import InformationAssimilationResult, NormalizedInformationResponse, InformationQuery
from src.domains.information.normalizer import InformationResponseNormalizer
from src.domains.information.contradiction import BeliefContradictionService


class ObservationBeliefBridge:
    """
    Translates observed resource or event parameters to subjective beliefs.
    """

    @staticmethod
    def process_observation(
        entity: EntityState,
        event: Dict[str, Any],
        state: AuthoritativeState,
    ) -> InformationAssimilationResult:
        """
        Produce updated Knowledge facts or leads corresponding to the observation.
        """
        obs_kind = event.get("kind")
        subj = event.get("subject")
        details = event.get("details", {}) or {}

        if obs_kind in ("claim_failed_search", "region_danger_seen"):
            result = BeliefContradictionService.detect(entity, event, state)
            if not result.contradiction_detected:
                return InformationAssimilationResult()

            lead = entity.strategic.leads.get(result.lead_id)
            failed_lead = _replace(
                lead,
                certainty=result.new_certainty,
                tested=True,
                test_outcome="FAILURE",
                failure_count=lead.failure_count + 1,
            )
            return InformationAssimilationResult(
                strategic_update=StrategicUpdate(leads_add_or_update=[failed_lead]),
                trace={"reason": result.reason, "observation_kind": obs_kind},
            )

        q = InformationQuery(subject=subj, kind="material_source")

        # 1. Direct observations yield KNOWN_FACT with max certainty (1.0)
        raw_res = {
            "answer_kind": "KNOWN_FACT",
            "certainty": 1.0,
            "details": details,
        }

        response = InformationResponseNormalizer.normalize(q, "observation_self", raw_res, current_tick=state.tick)

        from src.domains.information.assimilation import InformationAssimilationService
        return InformationAssimilationService.assimilate(entity, response, state.tick)
