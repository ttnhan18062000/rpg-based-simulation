from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class AgencyScorer(PillarScorer):
    """Scores Agency & Action pillar: SQ-01, SQ-02 (primary), SQ-12 (secondary)."""

    EVENT_TYPES = (
        "action_executed",
        "route_selected",
        "defer_with_reason",
        "project_started",
        "project_completed",
        "project_abandoned",
        "commitment_abandoned",
        "rejection_cascade_tick",
        "route_family_first_use",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._last_abandoned: dict[int, str] = {}
        self._pop_stasis_fired: bool = False
        self._entity_defer_streak: dict[int, int] = {}
        self._entity_stasis_fired: dict[int, bool] = {}

    def _reset_entity_stasis(self, entity_id: Optional[int]) -> None:
        if entity_id is not None:
            self._entity_defer_streak.pop(entity_id, None)
            self._entity_stasis_fired.pop(entity_id, None)

    def score(
        self,
        envelope: ObservabilityEventEnvelope,
        context: ScoringContext,
    ) -> Optional[ScoreRecord]:
        et = envelope.event_type
        tick = envelope.tick
        payload = envelope.payload or {}
        entity_id = envelope.entity_id

        def _rec(delta: float, reason: str, tags: tuple[str, ...]) -> ScoreRecord:
            return ScoreRecord(
                tick=tick,
                event_id=envelope.event_id,
                pillar=PillarId.AGENCY,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        if et == "action_executed":
            self._reset_entity_stasis(entity_id)
            return _rec(self.weights["action_taken"], "non-defer action", ("action_taken",))

        if et == "route_family_first_use":
            self._reset_entity_stasis(entity_id)
            delta = self.weights["route_novelty"] + self.weights["entropy_reward"]
            return _rec(delta, "novel route family used", ("route_novelty", "entropy_reward"))

        if et == "route_selected":
            self._reset_entity_stasis(entity_id)
            return _rec(self.weights["navigation_active"], "entity navigating toward goal", ("navigation_active",))

        if et == "project_completed":
            self._reset_entity_stasis(entity_id)
            if payload.get("is_commitment"):
                return _rec(self.weights["commitment_complete"], "commitment completed", ("commitment_complete",))
            return _rec(self.weights["project_done"], "project completed", ("project_done",))

        if et == "project_abandoned":
            if entity_id is not None:
                project_type = payload.get("project_type", "")
                self._last_abandoned[entity_id] = project_type
            return None

        if et == "commitment_abandoned":
            return None

        if et == "project_started":
            if entity_id is not None:
                project_type = payload.get("project_type", "")
                if self._last_abandoned.get(entity_id) == project_type and project_type:
                    self._last_abandoned.pop(entity_id, None)
                    return _rec(self.weights["project_cycle"], "project abandoned and immediately restarted", ("project_cycle",))
                self._last_abandoned.pop(entity_id, None)
            return None

        if et == "defer_with_reason":
            stasis_gate = self.weights.int_param("stasis_gate_ticks")
            window_tags = context.window_tag_counts.get(PillarId.AGENCY, {})
            pop_defer_count = window_tags.get("defer_idle", 0)  # population_stasis check only, unchanged

            # population stasis: zero action_taken in window, past gate
            if (
                not self._pop_stasis_fired
                and tick > stasis_gate
                and window_tags.get("action_taken", 0) == 0
                and pop_defer_count > 0
            ):
                self._pop_stasis_fired = True
                return _rec(
                    self.weights["population_stasis"],
                    "population-wide stasis: zero non-defer actions in window",
                    ("population_stasis",),
                )

            streak = self._entity_defer_streak.get(entity_id, 0) + 1
            if entity_id is not None:
                self._entity_defer_streak[entity_id] = streak

            cap = self.weights.int_param("stasis_extra_ticks_cap")
            delta = self.weights["defer_idle"]
            tags = ["defer_idle"]
            if streak > stasis_gate:
                tags.append("stasis_N")
                extra = streak - stasis_gate
                already_fired = self._entity_stasis_fired.get(entity_id, False) if entity_id is not None else False
                # Fire the one-shot escalation only once the streak has ACTUALLY REACHED the
                # full cap threshold (extra >= cap), NOT at the first post-gate tick (extra == 1).
                # Firing at extra == 1 would always add stasis_per_tick * 1 regardless of `cap`,
                # since streak increments by exactly 1 per event -- this was the original defect
                # (architecture review, TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE plan review):
                # `min(streak - stasis_gate, cap)` evaluated to 1 at the very first breach, every
                # time, making the escalation permanently -3.0 instead of the intended -15.0.
                if not already_fired and extra >= cap:
                    capped_extra = min(extra, cap)  # defensive; extra == cap at the firing point by construction
                    delta += self.weights["stasis_per_tick"] * capped_extra
                    if entity_id is not None:
                        self._entity_stasis_fired[entity_id] = True
            return _rec(delta, "entity deferred action", tuple(tags))

        if et == "rejection_cascade_tick":
            count = payload.get("count", 0)
            if count > 500:
                return _rec(
                    self.weights["rejection_cascade_sustained"],
                    "sustained population-wide rejection cascade >500/tick",
                    ("rejection_cascade_sustained",),
                )
            if count > 100:
                return _rec(
                    self.weights["rejection_cascade"],
                    "population-wide rejection cascade >100/tick",
                    ("rejection_cascade",),
                )
            return None

        return None
