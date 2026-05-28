"""
src/domains/information/bridge.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — ObservationBeliefBridge

Converts raw observation events into subjective high-certainty beliefs.
"""

from __future__ import annotations
from typing import Dict, Any

from src.core.state import EntityState, AuthoritativeState
from src.domains.information.schema import InformationAssimilationResult, NormalizedInformationResponse, InformationQuery
from src.domains.information.normalizer import InformationResponseNormalizer


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

        q = InformationQuery(subject=subj, kind="material_source")
        
        # 1. Direct observations yield KNOWN_FACT with max certainty (1.0)
        raw_res = {
            "answer_kind": "KNOWN_FACT",
            "certainty": 1.0,
            "details": details,
        }

        # Handle failed search search as contradiction triggers
        if obs_kind == "claim_failed_search":
            raw_res = {
                "answer_kind": "CONTRADICTION",
                "certainty": 0.0,
                "contradiction_targets": [event.get("lead_id", "")],
            }

        response = InformationResponseNormalizer.normalize(q, "observation_self", raw_res, current_tick=state.tick)

        from src.domains.information.assimilation import InformationAssimilationService
        return InformationAssimilationService.assimilate(entity, response, state.tick)
