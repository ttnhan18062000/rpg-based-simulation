"""Unit tests for InformationScorer — SQ-15, SQ-16."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.information import InformationScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, event_count: int = 5, window_tags: dict | None = None) -> ScoringContext:
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: (event_count if p == PillarId.INFORMATION else 0) for p in PillarId},
        window_tag_counts={p: (window_tags or {}) if p == PillarId.INFORMATION else {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=1,
        event_type=event_type, event_category="information", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> InformationScorer:
    return InformationScorer(scoring_weights)


class TestBeliefAssimilated:
    def test_belief_active(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("belief_assimilated"), _ctx(window_tags={"belief_active": 3}))
        assert rec is not None
        assert rec.delta == scoring_weights.for_pillar("INFORMATION")["belief_active"]

    def test_belief_system_silent_after_gate(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("belief_dormant_window")
        rec = scorer.score(_env("belief_assimilated", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "belief_system_silent" in rec.tags
        assert rec.delta == scoring_weights["belief_system_silent"]

    def test_belief_silent_fires_once(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("belief_dormant_window")
        ctx = _ctx(tick=gate + 1, window_tags={})
        scorer.score(_env("belief_assimilated", tick=gate + 1), ctx)
        rec2 = scorer.score(_env("belief_assimilated", tick=gate + 2), ctx)
        assert rec2 is not None
        assert "belief_system_silent" not in rec2.tags


class TestLeadCertainty:
    def test_certainty_increased(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("lead_certainty_updated", payload={"certainty_delta": 0.2}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["intel_quality_up"]

    def test_certainty_decreased_active_lead(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("lead_certainty_updated", payload={"certainty_delta": -0.3, "lead_active": True}), _ctx())
        assert rec is not None
        assert "knowledge_rot" in rec.tags

    def test_certainty_zero_returns_none(self, scorer: InformationScorer) -> None:
        rec = scorer.score(_env("lead_certainty_updated", payload={"certainty_delta": 0.0}), _ctx())
        assert rec is None


class TestContradiction:
    def test_lead_contradiction_resolved(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("lead_contradiction_resolved"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["intel_complexity"]
        assert "intel_complexity" in rec.tags


class TestPaidInfo:
    def test_knowledge_economy_active(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("paid_information_transaction"), _ctx(event_count=5))
        assert rec is not None
        assert rec.delta == scoring_weights.for_pillar("INFORMATION")["knowledge_economy_active"]

    def test_knowledge_economy_dormant_after_gate(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_diplomacy_by_tick")
        rec = scorer.score(_env("paid_information_transaction", tick=gate + 1), _ctx(tick=gate + 1, event_count=0))
        assert rec is not None
        assert "knowledge_economy_dormant" in rec.tags

    def test_paid_info_changed_goal(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("paid_info_changed_goal"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["info_has_impact"]


class TestBeliefStale:
    def test_belief_pipeline_deaf(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("belief_stale"), _ctx())
        assert rec is not None
        assert "belief_pipeline_deaf" in rec.tags


class TestDecisionDiverged:
    def test_subjective_divergence(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("decision_diverged_by_belief"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights.for_pillar("INFORMATION")["subjective_divergence"]

    def test_omniscience_collapse_once(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("decision_diverged_by_belief", payload={"is_collapse": True}), _ctx())
        assert rec is not None
        assert "omniscience_collapse" in rec.tags
        rec2 = scorer.score(_env("decision_diverged_by_belief", payload={"is_collapse": True}), _ctx())
        assert rec2 is None

    def test_paid_info_memory_failure(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("decision_diverged_by_belief", payload={"repeat_tip_count": 4}), _ctx())
        assert rec is not None
        assert "paid_info_memory_failure" in rec.tags


class TestRouteNewQuery:
    def test_information_seeking_active(self, scorer: InformationScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("route_new_query"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights.for_pillar("INFORMATION")["information_seeking_active"]
        assert "information_seeking_active" in rec.tags

    def test_route_new_query_in_event_types(self) -> None:
        assert "route_new_query" in InformationScorer.EVENT_TYPES


class TestNullReturn:
    def test_null_unknown(self, scorer: InformationScorer) -> None:
        assert scorer.score(_env("combat_initiated"), _ctx()) is None
