from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class FactionScorer(PillarScorer):
    """Scores Faction & Military pillar: SQ-05, SQ-06 (primary)."""

    PILLAR_ID = PillarId.FACTION

    EVENT_TYPES = (
        "diplomatic_transition",
        "alliance_proposed",
        "alliance_accepted",
        "war_declared",
        "military_conflict_resolved",
        "territory_ownership_changed",
        "resource_seized",
        "faction_tension_delta",
        "faction_extinct",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._diplomacy_dormant_fired: bool = False
        self._all_neutral_fired: bool = False
        self._war_tick: dict[str, int] = {}  # war_id → tick when war_declared

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
                pillar=PillarId.FACTION,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        if et == "diplomatic_transition":
            # Check diplomacy dormancy before scoring
            zero_gate = self.weights.int_param("zero_diplomacy_by_tick")
            if (
                not self._diplomacy_dormant_fired
                and tick > zero_gate
                and context.pillar_event_counts.get(PillarId.FACTION, 0) == 0
            ):
                self._diplomacy_dormant_fired = True
                return _rec(
                    self.weights["diplomacy_dormant"],
                    "zero diplomatic transitions in multi-faction world by tick gate",
                    ("diplomacy_dormant",),
                )
            return _rec(self.weights["diplomacy_active"], "diplomatic state transition fired", ("diplomacy_active",))

        if et == "alliance_proposed":
            return _rec(self.weights["coalition_forming"], "alliance proposal generated (common-enemy pair)", ("coalition_forming",))

        if et == "alliance_accepted":
            return _rec(self.weights["alliance_formed"], "alliance accepted between factions", ("alliance_formed",))

        if et == "war_declared":
            war_id = payload.get("war_id") or payload.get("faction_pair", f"{tick}")
            self._war_tick[str(war_id)] = tick
            return None  # war_declared itself has no delta; tracked for war_without_conflict check

        if et == "military_conflict_resolved":
            return _rec(self.weights["military_active"], "military conflict resolved", ("military_active",))

        if et == "territory_ownership_changed":
            # Check for faction monopoly / conquest
            territory_pct = payload.get("faction_territory_pct", 0.0)
            monopoly_gate = self.weights.int_param("faction_monopoly_by_tick")
            if territory_pct >= 1.0:
                return _rec(
                    self.weights["faction_conquest_degenerate"],
                    "single faction controls 100% of territory",
                    ("faction_conquest_degenerate",),
                )
            if territory_pct > 0.8 and tick > monopoly_gate:
                return _rec(
                    self.weights["faction_monopoly"],
                    "single faction controls >80% of territory after tick gate",
                    ("faction_monopoly",),
                )
            return _rec(self.weights["territory_shifted"], "territory ownership transition", ("territory_shifted",))

        if et == "resource_seized":
            return _rec(self.weights["economic_military_coupling"], "faction seized contested resource", ("economic_military_coupling",))

        if et == "faction_tension_delta":
            threshold = payload.get("threshold", 0.0)
            delta_val = payload.get("delta", 0.0)
            # Check tension oscillation
            window_tags = context.window_tag_counts.get(PillarId.FACTION, {})
            oscillation_count = window_tags.get("tension_oscillation", 0)
            if oscillation_count > 5:
                return _rec(
                    self.weights["tension_oscillation"],
                    "tension oscillating between same two values without threshold crossing",
                    ("tension_oscillation",),
                )
            if abs(delta_val) > 0 and payload.get("threshold_crossed", False):
                return _rec(self.weights["tension_active"], "faction tension delta exceeds threshold", ("tension_active",))
            # score all_factions_neutral on any tension event if all remain neutral
            if not self._all_neutral_fired and payload.get("all_neutral", False):
                self._all_neutral_fired = True
                return _rec(
                    self.weights["all_factions_neutral"],
                    "all factions remain NEUTRAL for entire run",
                    ("all_factions_neutral",),
                )
            return None

        if et == "faction_extinct":
            early_gate = self.weights.int_param("faction_early_extinction_by_tick")
            if tick <= early_gate:
                return _rec(
                    self.weights["faction_early_extinction"],
                    "faction extinct within gate ticks of run start",
                    ("faction_early_extinction",),
                )
            return None

        return None
