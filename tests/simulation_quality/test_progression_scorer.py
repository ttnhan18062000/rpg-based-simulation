"""Unit tests for ProgressionScorer — SQ-10, SQ-11, SQ-04 secondary."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.progression import ProgressionScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, window_tags: dict | None = None) -> ScoringContext:
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: (window_tags or {}) if p == PillarId.PROGRESSION else {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=1,
        event_type=event_type, event_category="lifecycle", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> ProgressionScorer:
    return ProgressionScorer(scoring_weights)


class TestXPGranted:
    def test_positive_per_10_xp(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("xp_granted", payload={"amount": 50}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["xp_active"] * 5
        assert "xp_active" in rec.tags

    def test_minimum_one_unit(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("xp_granted", payload={"amount": 5}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["xp_active"] * 1


class TestLevelUp:
    def test_level_milestone(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("level_up"), _ctx(window_tags={"level_milestone": 2}))
        assert rec is not None
        assert rec.delta == scoring_weights["level_milestone"]

    def test_level_cap_reached(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("level_up", payload={"at_cap": True}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["level_cap_reached"]
        assert "level_cap_reached" in rec.tags

    def test_all_level_1_fires_after_gate(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("progression_frozen_by_tick")
        rec = scorer.score(_env("level_up", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "all_level_1" in rec.tags
        assert rec.delta == scoring_weights["all_level_1"]


class TestEntityEvolved:
    def test_species_evolution(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(
            _env("entity_evolved", payload={"previous_kind": "goblin", "new_kind": "goblin_warrior"}),
            _ctx(),
        )
        assert rec is not None
        assert rec.delta == scoring_weights["species_evolution"]
        assert "species_evolution" in rec.tags


class TestSkillAndTrait:
    def test_skill_unlocked(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("skill_unlocked"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["skill_growth"]

    def test_trait_expressed(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("trait_expressed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["genetic_determinism_active"]

    def test_pillar_trait_unlocked(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("pillar_trait_unlocked"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["pillar_trait_milestone"]


class TestConversionAndSurvival:
    def test_progression_conversion_applied(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("progression_conversion_applied"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["soft_skill_evolution"]

    def test_near_death_survival(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("near_death_survival"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["survival_experience"]


class TestProgressionPlateau:
    def test_xp_freeze(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("progression_plateau_detected", payload={"type": "xp_freeze"}), _ctx())
        assert rec is not None
        assert "progression_frozen" in rec.tags

    def test_skill_silence(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("progression_plateau_detected", payload={"type": "skill_silence"}), _ctx())
        assert rec is not None
        assert "skill_system_silent" in rec.tags

    def test_xp_rate_zero_after_gate(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("xp_plateau_by_tick")
        rec = scorer.score(_env("progression_plateau_detected", tick=gate + 1, payload={"type": "xp_rate_zero"}), _ctx(tick=gate + 1))
        assert rec is not None
        assert "xp_plateau" in rec.tags

    def test_trait_rate_zero(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("progression_plateau_detected", payload={"type": "trait_rate_zero"}), _ctx())
        assert rec is not None
        assert "trait_system_silent" in rec.tags


class TestCapabilityGrowthStalled:
    def test_scores_configured_weight_and_tag(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("capability_growth_stalled", payload={"ticks_since_growth": 301, "level": 3}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["capability_growth_stalled"]
        assert "capability_growth_stalled" in rec.tags


class TestLifeArcIncoherent:
    def test_scores_configured_weight_and_tag(self, scorer: ProgressionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("life_arc_incoherent", payload={"generation": 2, "level": 1}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["life_arc_incoherent"]
        assert "life_arc_incoherent" in rec.tags


class TestNullReturn:
    def test_null_unknown(self, scorer: ProgressionScorer) -> None:
        assert scorer.score(_env("combat_initiated"), _ctx()) is None
