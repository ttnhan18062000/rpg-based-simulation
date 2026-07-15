from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class CognitionScorer(PillarScorer):
    """Scores Cognition pillar: SQ-21 (primary), SQ-01/SQ-02 (secondary via goal-lock)."""

    PILLAR_ID = PillarId.COGNITION

    EVENT_TYPES = (
        "belief_updated",
        "lead_certainty_changed",
        "strategic_goal_changed",
        "self_model_updated",
        "decision_divergence_detected",
        "knowledge_default_fallback",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._belief_dormant_fired: bool = False
        self._omniscience_fired: bool = False

    def score(
        self,
        envelope: ObservabilityEventEnvelope,
        context: ScoringContext,
    ) -> Optional[ScoreRecord]:
        et = envelope.event_type
        tick = envelope.tick
        payload = envelope.payload or {}

        def _rec(delta: float, reason: str, tags: tuple[str, ...]) -> ScoreRecord:
            return ScoreRecord(
                tick=tick,
                event_id=envelope.event_id,
                pillar=PillarId.COGNITION,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        if et == "belief_updated":
            # Check for belief system dormancy: zero updates in last 100-tick window
            window_tags = context.window_tag_counts.get(PillarId.COGNITION, {})
            dormant_gate = self.weights.int_param("belief_dormant_window")
            if (
                not self._belief_dormant_fired
                and tick > dormant_gate
                and window_tags.get("belief_active", 0) == 0
                and window_tags.get("knowledge_sharpening", 0) == 0
            ):
                self._belief_dormant_fired = True
                return _rec(
                    self.weights["belief_system_dormant"],
                    "zero belief updates in 100-tick window",
                    ("belief_system_dormant",),
                )
            return _rec(self.weights["belief_active"], "entity belief updated from event", ("belief_active",))

        if et == "lead_certainty_changed":
            delta = payload.get("certainty_delta", 0.0)
            if delta > 0:
                return _rec(self.weights["knowledge_sharpening"], "lead certainty increased", ("knowledge_sharpening",))
            if delta < 0 and payload.get("lead_active", False):
                return _rec(self.weights["knowledge_rot"], "lead certainty decayed to zero on active lead", ("knowledge_rot",))
            return None

        if et == "strategic_goal_changed":
            if payload.get("reason") == "rescoring":
                return _rec(self.weights["cognition_replan"], "goal changed by internal re-scoring", ("cognition_replan",))
            window_tags = context.window_tag_counts.get(PillarId.COGNITION, {})
            consecutive = window_tags.get("cognition_replan", 0) + window_tags.get("goal_lock_no_cognition", 0)
            gate = self.weights.int_param("stasis_gate_ticks")
            if consecutive > gate:
                return _rec(
                    self.weights["goal_lock_no_cognition"],
                    "same goal re-selected with no cognition update",
                    ("goal_lock_no_cognition",),
                )
            return None

        if et == "self_model_updated":
            return _rec(self.weights["self_model_active"], "self-model updated reflecting vital state", ("self_model_active",))

        if et == "decision_divergence_detected":
            # Check for omniscience collapse (all entities identical certainty)
            if payload.get("is_collapse", False):
                if not self._omniscience_fired:
                    self._omniscience_fired = True
                    return _rec(
                        self.weights["omniscience_collapse"],
                        "all entities share identical lead certainty distributions",
                        ("omniscience_collapse",),
                    )
                return None
            return _rec(
                self.weights["subjective_divergence"],
                "entities in same region diverged on route choice",
                ("subjective_divergence",),
            )

        if et == "knowledge_default_fallback":
            return _rec(
                self.weights["zero_knowledge_decision"],
                "entity decision on zero knowledge (default fallback path)",
                ("zero_knowledge_decision",),
            )

        return None
