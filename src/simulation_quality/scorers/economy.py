from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class EconomyScorer(PillarScorer):
    """Scores Economy pillar: SQ-07, SQ-09 (primary), SQ-16 (secondary).

    NOTE: ecology_cycle_completed is intentionally NOT scored here.
    That event is owned by WorldDynamicsScorer (E4) per SQ-08 conflict notes.
    """

    EVENT_TYPES = (
        "resource_harvested",
        "item_crafted",
        "trade_executed",
        "shop_transaction",
        "gold_transferred",
        "resource_node_depleted",
        # ecology_cycle_completed is EXCLUDED — owned by WorldDynamicsScorer
        "gold_sink_fired",
        "conservation_law_verified",
        "conservation_law_violated",
        "paid_info_transaction",
        "quest_reward_dispensed",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._zero_harvest_fired: bool = False
        self._zero_crafting_fired: bool = False
        self._zero_trade_fired: bool = False
        self._ecology_broken_fired: bool = False
        self._monetary_paralysis_fired: bool = False

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
                pillar=PillarId.ECONOMY,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        window_tags = context.window_tag_counts.get(PillarId.ECONOMY, {})
        harvest_gate = self.weights.int_param("zero_harvest_after_tick")
        craft_gate = self.weights.int_param("zero_crafting_after_tick")
        trade_gate = self.weights.int_param("zero_trade_after_tick")

        if et == "resource_harvested":
            # Time-gated: if we're past the gate and no harvesting was happening, score dormant first
            if (
                not self._zero_harvest_fired
                and tick > harvest_gate
                and window_tags.get("harvest_active", 0) == 0
            ):
                self._zero_harvest_fired = True
                return _rec(
                    self.weights["zero_harvest"],
                    "zero harvesting events after tick gate",
                    ("zero_harvest",),
                )
            return _rec(self.weights["harvest_active"], "entity harvested resources", ("harvest_active",))

        if et == "item_crafted":
            if (
                not self._zero_crafting_fired
                and tick > craft_gate
                and window_tags.get("crafting_active", 0) == 0
            ):
                self._zero_crafting_fired = True
                return _rec(
                    self.weights["zero_crafting"],
                    "zero crafting events after tick gate",
                    ("zero_crafting",),
                )
            return _rec(self.weights["crafting_active"], "item crafted", ("crafting_active",))

        if et in ("trade_executed", "shop_transaction"):
            if (
                not self._zero_trade_fired
                and tick > trade_gate
                and window_tags.get("trade_active", 0) == 0
            ):
                self._zero_trade_fired = True
                return _rec(
                    self.weights["zero_trade"],
                    "zero trade events after tick gate",
                    ("zero_trade",),
                )
            return _rec(self.weights["trade_active"], "trade or shop transaction executed", ("trade_active",))

        if et == "gold_transferred":
            return _rec(self.weights["gold_flow"], "gold changed hands", ("gold_flow",))

        if et == "resource_node_depleted":
            return _rec(self.weights["scarcity_active"], "resource node depleted (real scarcity)", ("scarcity_active",))

        if et == "gold_sink_fired":
            return _rec(self.weights["inflation_controlled"], "gold sink fired on inflation pressure", ("inflation_controlled",))

        if et == "conservation_law_verified":
            return _rec(self.weights["conservation_valid"], "conservation law verification passed", ("conservation_valid",))

        if et == "conservation_law_violated":
            return _rec(
                self.weights["conservation_violated"],
                "conservation law violated — atomic conservation broken",
                ("conservation_violated",),
            )

        if et == "paid_info_transaction":
            return _rec(
                self.weights["knowledge_economy_active"],
                "paid information transaction",
                ("knowledge_economy_active",),
            )

        if et == "quest_reward_dispensed":
            return _rec(self.weights["quest_economy_coupling"], "quest reward dispensed", ("quest_economy_coupling",))

        return None
