"""Unit tests for CombatScorer — SQ-03, SQ-04."""
from __future__ import annotations
import uuid

import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.combat import CombatScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, combat_event_count: int = 5) -> ScoringContext:
    counts = {p: 0 for p in PillarId}
    counts[PillarId.COMBAT] = combat_event_count
    return ScoringContext(
        run_id="test",
        current_tick=tick,
        entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts=counts,
        window_tag_counts={p: {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex,
        run_id="test",
        tick=tick,
        entity_id=1,
        event_type=event_type,
        event_category="combat",
        severity="INFO",
        source_system="test",
        message="",
        payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> CombatScorer:
    return CombatScorer(scoring_weights)


class TestCombatInitiated:
    def test_positive(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("combat_initiated"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["combat_active"]
        assert "combat_active" in rec.tags
        assert rec.pillar == PillarId.COMBAT

    def test_null_for_unknown(self, scorer: CombatScorer) -> None:
        rec = scorer.score(_env("totally_unknown"), _ctx())
        assert rec is None


class TestCombatResolved:
    def test_positive(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("combat_resolved"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["combat_resolved"]
        assert "combat_resolved" in rec.tags


class TestNearDeathSurvival:
    def test_positive(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("near_death_survival"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["survival_tension"]
        assert "survival_tension" in rec.tags


class TestTacticalVariety:
    def test_first_modifier_scores(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("combat_damage", payload={"tactical_modifier": "flanking"}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["tactical_variety"]
        assert "tactical_variety" in rec.tags

    def test_duplicate_modifier_no_score(self, scorer: CombatScorer) -> None:
        scorer.score(_env("combat_damage", payload={"tactical_modifier": "flanking"}), _ctx())
        rec = scorer.score(_env("combat_damage", payload={"tactical_modifier": "flanking"}), _ctx())
        assert rec is None

    def test_no_modifier_no_score(self, scorer: CombatScorer) -> None:
        rec = scorer.score(_env("combat_damage", payload={}), _ctx())
        assert rec is None


class TestEntityKilled:
    def test_attrition(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("entity_killed", tick=50), _ctx(tick=50))
        assert rec is not None
        assert rec.delta == scoring_weights["attrition"]
        assert "attrition" in rec.tags

    def test_early_extinction_before_gate(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("early_extinction_before_tick")
        rec = scorer.score(_env("entity_killed", tick=gate - 1), _ctx(tick=gate - 1))
        assert rec is not None
        assert rec.delta == scoring_weights["early_extinction"]
        assert "early_extinction" in rec.tags

    def test_early_extinction_fires_only_once(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("early_extinction_before_tick")
        rec1 = scorer.score(_env("entity_killed", tick=gate - 1), _ctx(tick=gate - 1))
        rec2 = scorer.score(_env("entity_killed", tick=gate - 1), _ctx(tick=gate - 1))
        assert rec1 is not None and "early_extinction" in rec1.tags
        assert rec2 is not None and "early_extinction" not in rec2.tags

    def test_no_early_extinction_after_gate(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("early_extinction_before_tick")
        rec = scorer.score(_env("entity_killed", tick=gate + 5), _ctx(tick=gate + 5))
        assert rec is not None
        assert "early_extinction" not in rec.tags
        assert rec.delta == scoring_weights["attrition"]


class TestAttritionThreshold:
    def test_attrition_spiral(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("attrition_50pct_by_tick")
        rec = scorer.score(_env("attrition_threshold_crossed", tick=gate - 1, payload={"threshold": 0.5}), _ctx(tick=gate - 1))
        assert rec is not None
        assert rec.delta == scoring_weights["attrition_spiral"]
        assert "attrition_spiral" in rec.tags

    def test_extinction_degenerate(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("attrition_90pct_by_tick")
        rec = scorer.score(_env("attrition_threshold_crossed", tick=gate - 1, payload={"threshold": 0.9}), _ctx(tick=gate - 1))
        assert rec is not None
        assert rec.delta == scoring_weights["extinction_degenerate"]
        assert "extinction_degenerate" in rec.tags

    def test_no_score_after_gate(self, scorer: CombatScorer) -> None:
        rec = scorer.score(_env("attrition_threshold_crossed", tick=9999, payload={"threshold": 0.5}), _ctx(tick=9999))
        assert rec is None


class TestHardLaw:
    def test_hard_law_violation(self, scorer: CombatScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("combat_hard_law_violation"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["combat_hard_law"]
        assert "combat_hard_law" in rec.tags


class TestCombatDormant:
    def test_dormant_fires_after_gate_with_zero_events(
        self, scorer: CombatScorer, scoring_weights: ScoringWeights
    ) -> None:
        gate = scoring_weights.int_param("zero_combat_by_tick")
        # Context shows zero combat events recorded; any combat event after gate triggers dormant check
        ctx = _ctx(tick=gate + 1, combat_event_count=0)
        rec = scorer.score(_env("combat_initiated", tick=gate + 1), ctx)
        # dormant fires first since event_count is 0
        assert rec is not None
        assert "combat_dormant" in rec.tags
        assert rec.delta == scoring_weights["combat_dormant"]

    def test_dormant_not_fire_when_events_exist(self, scorer: CombatScorer) -> None:
        gate = 200
        ctx = _ctx(tick=gate + 10, combat_event_count=50)
        rec = scorer.score(_env("combat_initiated", tick=gate + 10), ctx)
        assert rec is None or "combat_dormant" not in rec.tags
