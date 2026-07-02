from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class NarrativeScorer(PillarScorer):
    """Scores Narrative pillar: SQ-19, SQ-20, SQ-22 (primary).

    chronicle_entry_created events emitted as disk JSONL only (not event bus) are a known
    gap; this scorer only receives bus-emitted chronicle events.

    Does NOT duplicate FactionScorer signals (alliance/war events).
    """

    EVENT_TYPES = (
        "quest_started",
        "quest_completed",
        "quest_failed",
        "chronicle_entry_created",
        "world_emergence_event",
        "narrative_milestone",
        "scenario_objective_progressed",
        "scenario_objective_completed",
        "scenario_stalled",
        "hero_death_unrecorded",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._quest_dormant_fired: bool = False
        self._narrative_silent_fired: bool = False
        self._scenario_broken_fired: bool = False

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
                pillar=PillarId.NARRATIVE,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        window_tags = context.window_tag_counts.get(PillarId.NARRATIVE, {})

        if et == "quest_started":
            # Check quest dormancy: no quests started after gate
            zero_gate = self.weights.int_param("zero_quests_after_tick")
            if (
                not self._quest_dormant_fired
                and tick > zero_gate
                and window_tags.get("quest_active", 0) == 0
            ):
                self._quest_dormant_fired = True
                return _rec(
                    self.weights["quest_system_dormant"],
                    "zero quest starts in run after tick gate (unconditional: fires even if quest config is empty — check §5 NARRATIVE traceability)",
                    ("quest_system_dormant",),
                )
            return _rec(self.weights["quest_active"], "quest started", ("quest_active",))

        if et == "quest_completed":
            return _rec(self.weights["quest_resolved"], "quest completed", ("quest_resolved",))

        if et == "quest_failed":
            return _rec(self.weights["quest_failed"], "quest failed (creates narrative tension)", ("quest_failed",))

        if et == "chronicle_entry_created":
            # Check narrative silence
            narrative_gate = self.weights.int_param("zero_chronicle_after_tick")
            if (
                not self._narrative_silent_fired
                and tick > narrative_gate
                and window_tags.get("narrative_event", 0) == 0
            ):
                self._narrative_silent_fired = True
                return _rec(
                    self.weights["history_silent"],
                    "zero chronicle or narrative events in long run",
                    ("history_silent",),
                )
            return _rec(self.weights["history_forming"], "chronicle entry created from significant world event", ("history_forming",))

        if et == "world_emergence_event":
            return _rec(self.weights["emergence_active"], "unscripted world emergence event fired", ("emergence_active",))

        if et == "narrative_milestone":
            return _rec(self.weights["history_forming"], "named narrative milestone reached", ("narrative_milestone",))

        if et == "scenario_objective_progressed":
            return _rec(self.weights["scenario_advancing"], "scenario objective progressed", ("scenario_advancing",))

        if et == "scenario_objective_completed":
            return _rec(self.weights["scenario_resolved"], "scenario objective completed", ("scenario_resolved",))

        if et == "scenario_stalled":
            if not self._scenario_broken_fired:
                self._scenario_broken_fired = True
                return _rec(
                    self.weights["scenario_stalled"],
                    "scenario objectives stalled for too long — likely misconfigured or unreachable",
                    ("scenario_stalled",),
                )
            return None

        if et == "hero_death_unrecorded":
            return _rec(
                self.weights["hero_death_unrecorded"],
                "hero died but no chronicle entry or narrative event emitted",
                ("hero_death_unrecorded",),
            )

        return None
