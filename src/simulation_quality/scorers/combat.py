from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class CombatScorer(PillarScorer):
    """Scores Combat pillar: SQ-03, SQ-04 (primary)."""

    EVENT_TYPES = (
        "combat_initiated",
        "combat_resolved",
        "combat_damage",
        "entity_killed",
        "near_death_survival",
        "combat_hard_law_violation",
        "attrition_threshold_crossed",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._seen_modifiers: set[str] = set()
        self._early_ext_fired: bool = False
        self._dormant_fired: bool = False

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
                pillar=PillarId.COMBAT,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        # Check time-gated dormant penalty on any combat event
        zero_combat_gate = self.weights.int_param("zero_combat_by_tick")
        if (
            not self._dormant_fired
            and tick > zero_combat_gate
            and context.pillar_event_counts.get(PillarId.COMBAT, 0) == 0
        ):
            self._dormant_fired = True
            return _rec(
                self.weights["combat_dormant"],
                "zero combat events in hostile world by tick threshold",
                ("combat_dormant",),
            )

        if et == "combat_initiated":
            return _rec(self.weights["combat_active"], "combat engagement initiated", ("combat_active",))

        if et == "combat_resolved":
            return _rec(self.weights["combat_resolved"], "combat resolved with clear outcome", ("combat_resolved",))

        if et == "near_death_survival":
            return _rec(self.weights["survival_tension"], "entity survived near-death", ("survival_tension",))

        if et == "combat_damage":
            modifier = payload.get("tactical_modifier")
            if modifier and modifier not in self._seen_modifiers:
                self._seen_modifiers.add(modifier)
                return _rec(self.weights["tactical_variety"], f"new tactical modifier: {modifier}", ("tactical_variety",))
            return None

        if et == "entity_killed":
            early_gate = self.weights.int_param("early_extinction_before_tick")
            if tick < early_gate and not self._early_ext_fired:
                self._early_ext_fired = True
                return _rec(
                    self.weights["early_extinction"],
                    "entity death before tick threshold (early extinction)",
                    ("early_extinction",),
                )
            return _rec(self.weights["attrition"], "entity killed in combat", ("attrition",))

        if et == "attrition_threshold_crossed":
            threshold = payload.get("threshold", 0.0)
            gate_90 = self.weights.int_param("attrition_90pct_by_tick")
            gate_50 = self.weights.int_param("attrition_50pct_by_tick")
            if threshold >= 0.9 and tick <= gate_90:
                return _rec(
                    self.weights["extinction_degenerate"],
                    "90% population attrition by tick threshold",
                    ("extinction_degenerate",),
                )
            if threshold >= 0.5 and tick <= gate_50:
                return _rec(
                    self.weights["attrition_spiral"],
                    "50% population attrition by tick threshold",
                    ("attrition_spiral",),
                )
            return None

        if et == "combat_hard_law_violation":
            return _rec(self.weights["combat_hard_law"], "hard law violated in combat pipeline", ("combat_hard_law",))

        return None
