"""Unit tests for NarrativeScorer — SQ-19, SQ-20, SQ-22."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.narrative import NarrativeScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, window_tags: dict | None = None) -> ScoringContext:
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: (window_tags or {}) if p == PillarId.NARRATIVE else {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=1,
        event_type=event_type, event_category="narrative", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> NarrativeScorer:
    return NarrativeScorer(scoring_weights)


class TestQuestEvents:
    def test_quest_started_active(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("quest_started"), _ctx(window_tags={"quest_active": 2}))
        assert rec is not None
        assert rec.delta == scoring_weights["quest_active"]

    def test_zero_quest_starts_after_gate(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_quests_after_tick")
        rec = scorer.score(_env("quest_started", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "quest_system_dormant" in rec.tags
        assert rec.delta == scoring_weights["quest_system_dormant"]

    def test_zero_quest_dormant_fires_once(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_quests_after_tick")
        ctx = _ctx(tick=gate + 1, window_tags={})
        scorer.score(_env("quest_started", tick=gate + 1), ctx)
        rec2 = scorer.score(_env("quest_started", tick=gate + 2), ctx)
        assert rec2 is not None
        assert "quest_system_dormant" not in rec2.tags

    def test_quest_completed(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("quest_completed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["quest_resolved"]

    def test_quest_failed(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("quest_failed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["quest_failed"]


class TestChronicle:
    def test_chronicle_entry_active(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("chronicle_entry_created"), _ctx(window_tags={"history_forming": 3}))
        assert rec is not None
        assert rec.delta == scoring_weights["history_forming"]

    def test_narrative_silent_after_gate(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_chronicle_after_tick")
        rec = scorer.score(_env("chronicle_entry_created", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "history_silent" in rec.tags
        assert rec.delta == scoring_weights["history_silent"]

    def test_narrative_silent_fires_once(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_chronicle_after_tick")
        ctx = _ctx(tick=gate + 1, window_tags={})
        scorer.score(_env("chronicle_entry_created", tick=gate + 1), ctx)
        rec2 = scorer.score(_env("chronicle_entry_created", tick=gate + 2), ctx)
        assert rec2 is not None
        assert "history_silent" not in rec2.tags


class TestMilestoneAndEmergence:
    def test_world_emergence_event(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("world_emergence_event"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["emergence_active"]

    def test_narrative_milestone(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("narrative_milestone"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["history_forming"]


class TestScenarioObjectives:
    def test_objective_progressed(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("scenario_objective_progressed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["scenario_advancing"]

    def test_objective_completed(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("scenario_objective_completed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["scenario_resolved"]

    def test_scenario_stalled_fires_once(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("scenario_stalled"), _ctx())
        assert rec is not None
        assert "scenario_stalled" in rec.tags
        rec2 = scorer.score(_env("scenario_stalled"), _ctx())
        assert rec2 is None

    def test_hero_death_unrecorded(self, scorer: NarrativeScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("hero_death_unrecorded"), _ctx())
        assert rec is not None
        assert "hero_death_unrecorded" in rec.tags


class TestNullReturn:
    def test_null_unknown(self, scorer: NarrativeScorer) -> None:
        assert scorer.score(_env("combat_initiated"), _ctx()) is None
