from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class InformationScorer(PillarScorer):
    """Scores Information & Belief pillar: SQ-15, SQ-16 (primary).

    paid_information_transaction is scored here as primary (not in EconomyScorer).
    """

    EVENT_TYPES = (
        "belief_assimilated",
        "lead_certainty_updated",
        "lead_contradiction_resolved",
        "paid_information_transaction",
        "paid_info_changed_goal",
        "belief_stale",
        "decision_diverged_by_belief",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._knowledge_economy_dormant_fired: bool = False
        self._belief_silent_fired: bool = False
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
                pillar=PillarId.INFORMATION,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        if et == "belief_assimilated":
            # Check belief system silence
            dormant_gate = self.weights.int_param("belief_dormant_window")
            window_tags = context.window_tag_counts.get(PillarId.INFORMATION, {})
            if (
                not self._belief_silent_fired
                and tick > dormant_gate
                and window_tags.get("belief_active", 0) == 0
            ):
                self._belief_silent_fired = True
                return _rec(
                    self.weights["belief_system_silent"],
                    "zero belief updates population-wide for 100 ticks",
                    ("belief_system_silent",),
                )
            return _rec(self.weights["belief_active"], "belief assimilated from information event", ("belief_active",))

        if et == "lead_certainty_updated":
            delta_val = payload.get("certainty_delta", 0.0)
            if delta_val > 0:
                return _rec(self.weights["intel_quality_up"], "lead certainty increased from new information", ("intel_quality_up",))
            if delta_val < 0 and payload.get("lead_active", False):
                return _rec(self.weights["knowledge_rot"], "lead certainty decayed to zero on active lead", ("knowledge_rot",))
            return None

        if et == "lead_contradiction_resolved":
            return _rec(
                self.weights["intel_complexity"],
                "entity replanned from conflicting intel (contradiction resolved)",
                ("intel_complexity",),
            )

        if et == "paid_information_transaction":
            # Check knowledge economy dormancy
            zero_gate = self.weights.int_param("zero_diplomacy_by_tick")
            if (
                not self._knowledge_economy_dormant_fired
                and tick > zero_gate
                and context.pillar_event_counts.get(PillarId.INFORMATION, 0) == 0
            ):
                self._knowledge_economy_dormant_fired = True
                return _rec(
                    self.weights["knowledge_economy_dormant"],
                    "zero paid info transactions in world with info NPCs after gate",
                    ("knowledge_economy_dormant",),
                )
            return _rec(
                self.weights["knowledge_economy_active"],
                "entity paid for information",
                ("knowledge_economy_active",),
            )

        if et == "paid_info_changed_goal":
            return _rec(
                self.weights["info_has_impact"],
                "paid information changed entity goal within 5 ticks",
                ("info_has_impact",),
            )

        if et == "belief_stale":
            return _rec(
                self.weights["belief_pipeline_deaf"],
                "belief unchanged after information response received",
                ("belief_pipeline_deaf",),
            )

        if et == "decision_diverged_by_belief":
            # Check omniscience collapse
            if payload.get("is_collapse", False):
                if not self._omniscience_fired:
                    self._omniscience_fired = True
                    return _rec(
                        self.weights["omniscience_collapse"],
                        "all entities share identical lead certainty distributions",
                        ("omniscience_collapse",),
                    )
                return None
            # Check paid info memory failure
            if payload.get("repeat_tip_count", 0) > 3:
                return _rec(
                    self.weights["paid_info_memory_failure"],
                    "entity purchased same lead tip >3 times with no certainty gain",
                    ("paid_info_memory_failure",),
                )
            return _rec(
                self.weights["subjective_divergence"],
                "two entities diverged on route choice due to belief difference",
                ("subjective_divergence",),
            )

        return None
