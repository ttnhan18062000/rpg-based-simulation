"""Unit tests for CognitionScorer — SQ-21, SQ-01/SQ-02 secondary."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.cognition import CognitionScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, window_tags: dict | None = None) -> ScoringContext:
    w = window_tags or {}
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=5,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: (w if p == PillarId.COGNITION else {}) for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=1,
        event_type=event_type, event_category="strategy", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> CognitionScorer:
    return CognitionScorer(scoring_weights)


class TestBeliefUpdated:
    def test_positive(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("belief_updated"), _ctx(window_tags={"belief_active": 3}))
        assert rec is not None
        assert rec.delta == scoring_weights["belief_active"]
        assert "belief_active" in rec.tags

    def test_dormant_fires_when_no_recent_updates(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("belief_dormant_window")
        rec = scorer.score(_env("belief_updated", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "belief_system_dormant" in rec.tags
        assert rec.delta == scoring_weights["belief_system_dormant"]

    def test_dormant_fires_only_once(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("belief_dormant_window")
        rec1 = scorer.score(_env("belief_updated", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        rec2 = scorer.score(_env("belief_updated", tick=gate + 2), _ctx(tick=gate + 2, window_tags={}))
        assert rec1 is not None and "belief_system_dormant" in rec1.tags
        assert rec2 is None or "belief_system_dormant" not in rec2.tags


class TestLeadCertaintyChanged:
    def test_sharpening(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("lead_certainty_changed", payload={"certainty_delta": 0.2}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["knowledge_sharpening"]
        assert "knowledge_sharpening" in rec.tags

    def test_knowledge_rot_on_active_lead(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("lead_certainty_changed", payload={"certainty_delta": -0.5, "lead_active": True}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["knowledge_rot"]
        assert "knowledge_rot" in rec.tags

    def test_no_score_on_inactive_lead_decay(self, scorer: CognitionScorer) -> None:
        rec = scorer.score(_env("lead_certainty_changed", payload={"certainty_delta": -0.1, "lead_active": False}), _ctx())
        assert rec is None

    def test_no_score_on_zero_delta(self, scorer: CognitionScorer) -> None:
        rec = scorer.score(_env("lead_certainty_changed", payload={"certainty_delta": 0.0}), _ctx())
        assert rec is None


class TestStrategicGoalChanged:
    def test_replan_on_rescoring(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("strategic_goal_changed", payload={"reason": "rescoring"}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["cognition_replan"]

    def test_no_score_when_external(self, scorer: CognitionScorer) -> None:
        rec = scorer.score(_env("strategic_goal_changed", payload={"reason": "external_event"}), _ctx())
        assert rec is None


class TestSelfModelUpdated:
    def test_positive(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("self_model_updated"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["self_model_active"]


class TestDecisionDivergence:
    def test_subjective_divergence(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("decision_divergence_detected", payload={}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["subjective_divergence"]
        assert "subjective_divergence" in rec.tags

    def test_omniscience_collapse(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("decision_divergence_detected", payload={"is_collapse": True}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["omniscience_collapse"]

    def test_omniscience_fires_once(self, scorer: CognitionScorer) -> None:
        rec1 = scorer.score(_env("decision_divergence_detected", payload={"is_collapse": True}), _ctx())
        rec2 = scorer.score(_env("decision_divergence_detected", payload={"is_collapse": True}), _ctx())
        assert rec1 is not None
        assert rec2 is None


class TestKnowledgeDefaultFallback:
    def test_negative(self, scorer: CognitionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("knowledge_default_fallback"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["zero_knowledge_decision"]
        assert "zero_knowledge_decision" in rec.tags


class TestNullReturn:
    def test_null_for_unknown(self, scorer: CognitionScorer) -> None:
        assert scorer.score(_env("some_random_event"), _ctx()) is None
