"""Unit tests for EconomyScorer — SQ-07, SQ-09. Verifies ecology_cycle_completed is NOT scored."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.economy import EconomyScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, window_tags: dict | None = None) -> ScoringContext:
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: (window_tags or {}) if p == PillarId.ECONOMY else {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=1,
        event_type=event_type, event_category="economy", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> EconomyScorer:
    return EconomyScorer(scoring_weights)


class TestHarvest:
    def test_positive(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("resource_harvested"), _ctx(window_tags={"harvest_active": 5}))
        assert rec is not None
        assert rec.delta == scoring_weights["harvest_active"]

    def test_zero_harvest_fires_after_gate(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_harvest_after_tick")
        rec = scorer.score(_env("resource_harvested", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "zero_harvest" in rec.tags
        assert rec.delta == scoring_weights["zero_harvest"]

    def test_zero_harvest_not_before_gate(self, scorer: EconomyScorer) -> None:
        rec = scorer.score(_env("resource_harvested", tick=5), _ctx(tick=5, window_tags={}))
        assert rec is not None
        assert "zero_harvest" not in rec.tags


class TestCrafting:
    def test_positive(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("item_crafted"), _ctx(window_tags={"crafting_active": 3}))
        assert rec is not None
        assert rec.delta == scoring_weights["crafting_active"]

    def test_zero_crafting_fires_after_gate(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_crafting_after_tick")
        rec = scorer.score(_env("item_crafted", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "zero_crafting" in rec.tags


class TestTrade:
    def test_trade_executed_positive(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("trade_executed"), _ctx(window_tags={"trade_active": 2}))
        assert rec is not None
        assert rec.delta == scoring_weights["trade_active"]

    def test_shop_transaction(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("shop_transaction"), _ctx(window_tags={"trade_active": 2}))
        assert rec is not None
        assert rec.delta == scoring_weights["trade_active"]

    def test_zero_trade_fires_after_gate(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_trade_after_tick")
        rec = scorer.score(_env("trade_executed", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "zero_trade" in rec.tags


class TestGoldAndConservation:
    def test_gold_transferred(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("gold_transferred"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["gold_flow"]

    def test_conservation_valid(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("conservation_law_verified"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["conservation_valid"]

    def test_conservation_violated(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("conservation_law_violated"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["conservation_violated"]
        assert rec.delta < 0

    def test_gold_sink_fired(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("gold_sink_fired"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["inflation_controlled"]


class TestEcologyExclusion:
    def test_ecology_cycle_not_scored(self, scorer: EconomyScorer) -> None:
        """ecology_cycle_completed must NOT be in EconomyScorer.EVENT_TYPES (owned by WorldDynamicsScorer)."""
        assert "ecology_cycle_completed" not in EconomyScorer.EVENT_TYPES
        # Direct call also returns None
        rec = scorer.score(_env("ecology_cycle_completed"), _ctx())
        assert rec is None


class TestMiscPositives:
    def test_resource_node_depleted(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("resource_node_depleted"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["scarcity_active"]

    def test_paid_info_transaction(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("paid_info_transaction"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights.for_pillar("ECONOMY")["knowledge_economy_active"]

    def test_quest_reward_dispensed(self, scorer: EconomyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("quest_reward_dispensed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["quest_economy_coupling"]


class TestNullReturn:
    def test_null_unknown(self, scorer: EconomyScorer) -> None:
        assert scorer.score(_env("combat_initiated"), _ctx()) is None
