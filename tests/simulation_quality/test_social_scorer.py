"""Unit tests for SocialScorer — SQ-12, SQ-13, SQ-14."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.social import SocialScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, event_count: int = 5, window_tags: dict | None = None) -> ScoringContext:
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: (event_count if p == PillarId.SOCIAL else 0) for p in PillarId},
        window_tag_counts={p: (window_tags or {}) if p == PillarId.SOCIAL else {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=1,
        event_type=event_type, event_category="social", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> SocialScorer:
    return SocialScorer(scoring_weights)


class TestCooperation:
    def test_cooperation_active(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("cooperation_event"), _ctx(event_count=5))
        assert rec is not None
        assert rec.delta == scoring_weights["cooperation_active"]
        assert "cooperation_active" in rec.tags

    def test_cooperation_dormant_after_gate(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stagnation_window")
        rec = scorer.score(_env("cooperation_event", tick=gate + 1), _ctx(tick=gate + 1, event_count=0))
        assert rec is not None
        assert "cooperation_dormant" in rec.tags
        assert rec.delta == scoring_weights["cooperation_dormant"]

    def test_cooperation_dormant_fires_once(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stagnation_window")
        ctx = _ctx(tick=gate + 1, event_count=0)
        scorer.score(_env("cooperation_event", tick=gate + 1), ctx)
        rec2 = scorer.score(_env("cooperation_event", tick=gate + 2), ctx)
        assert rec2 is not None
        assert "cooperation_dormant" not in rec2.tags


class TestGroupDynamics:
    def test_group_joined(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("group_joined"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["group_forming"]

    def test_group_expelled(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("group_expelled"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["group_enforcement"]


class TestContracts:
    def test_offer_created_returns_none(self, scorer: SocialScorer) -> None:
        assert scorer.score(_env("contract_offer_created"), _ctx()) is None

    def test_offer_accepted(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("contract_offer_accepted"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["negotiation_active"]

    def test_milestone_completed(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("contract_milestone_completed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["contract_honored"]

    def test_contract_completed(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("contract_completed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["contract_complete"]

    def test_contract_lapsed(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("contract_lapsed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["contract_broken"]

    def test_offer_expired(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("contract_expired_offer"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["offer_dead"]


class TestReputation:
    def test_significant_shift(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("reputation_delta", payload={"delta": 1.0}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["reputation_shifting"]

    def test_small_shift_returns_none(self, scorer: SocialScorer) -> None:
        rec = scorer.score(_env("reputation_delta", payload={"delta": 0.1}), _ctx())
        assert rec is None

    def test_reputation_flat(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("reputation_delta", payload={"all_flat": True, "delta": 0.0}), _ctx())
        assert rec is not None
        assert "reputation_flat" in rec.tags
        assert rec.delta == scoring_weights["reputation_flat"]


class TestSocialMemory:
    def test_social_memory_created(self, scorer: SocialScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("social_memory_created"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["relationship_depth"]


class TestGriefNemesis:
    def test_social_scorer_scores_grief_urgency_triggered(
        self, scorer: SocialScorer, scoring_weights: ScoringWeights
    ) -> None:
        rec = scorer.score(_env("grief_urgency_triggered"), _ctx())
        assert rec is not None
        assert rec.pillar == PillarId.SOCIAL
        assert rec.delta == scoring_weights["grief_urgency_triggered"]
        assert "grief_urgency" in rec.tags

    def test_social_scorer_scores_nemesis_relation_formed(
        self, scorer: SocialScorer, scoring_weights: ScoringWeights
    ) -> None:
        rec = scorer.score(_env("nemesis_relation_formed"), _ctx())
        assert rec is not None
        assert rec.pillar == PillarId.SOCIAL
        assert rec.delta == scoring_weights["nemesis_relation_formed"]
        assert "nemesis_relation" in rec.tags


class TestAllianceExclusion:
    def test_alliance_formed_not_in_event_types(self, scorer: SocialScorer) -> None:
        """SocialScorer must NOT score alliance_formed — that belongs to FactionScorer."""
        assert "alliance_formed" not in SocialScorer.EVENT_TYPES


class TestNullReturn:
    def test_null_unknown(self, scorer: SocialScorer) -> None:
        assert scorer.score(_env("combat_initiated"), _ctx()) is None
