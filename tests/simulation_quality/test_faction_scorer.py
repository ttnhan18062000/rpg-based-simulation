"""Unit tests for FactionScorer — SQ-05, SQ-06."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.faction import FactionScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, faction_event_count: int = 5, window_tags: dict | None = None) -> ScoringContext:
    counts = {p: 0 for p in PillarId}
    counts[PillarId.FACTION] = faction_event_count
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts=counts,
        window_tag_counts={p: (window_tags or {}) if p == PillarId.FACTION else {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=None,
        event_type=event_type, event_category="strategy", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> FactionScorer:
    return FactionScorer(scoring_weights)


class TestDiplomaticTransition:
    def test_positive(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("diplomatic_transition"), _ctx(faction_event_count=5))
        assert rec is not None
        assert rec.delta == scoring_weights["diplomacy_active"]

    def test_dormant_fires_after_gate(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_diplomacy_by_tick")
        rec = scorer.score(_env("diplomatic_transition", tick=gate + 1), _ctx(tick=gate + 1, faction_event_count=0))
        assert rec is not None
        assert "diplomacy_dormant" in rec.tags


class TestAlliances:
    def test_coalition_forming(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("alliance_proposed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["coalition_forming"]

    def test_alliance_accepted(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("alliance_accepted"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["alliance_formed"]


class TestWarAndMilitary:
    def test_war_declared_no_score(self, scorer: FactionScorer) -> None:
        rec = scorer.score(_env("war_declared", payload={"war_id": "w1"}), _ctx())
        assert rec is None  # tracked but not scored directly

    def test_military_conflict_resolved(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("military_conflict_resolved"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["military_active"]


class TestTerritoryOwnership:
    def test_territory_shifted(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("territory_ownership_changed", payload={"faction_territory_pct": 0.5}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["territory_shifted"]

    def test_faction_monopoly(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("faction_monopoly_by_tick")
        rec = scorer.score(
            _env("territory_ownership_changed", tick=gate + 1, payload={"faction_territory_pct": 0.85}),
            _ctx(tick=gate + 1)
        )
        assert rec is not None
        assert "faction_monopoly" in rec.tags

    def test_conquest_degenerate(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("territory_ownership_changed", payload={"faction_territory_pct": 1.0}), _ctx())
        assert rec is not None
        assert "faction_conquest_degenerate" in rec.tags
        assert rec.delta == scoring_weights["faction_conquest_degenerate"]


class TestFactionExtinct:
    def test_early_extinction(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("faction_early_extinction_by_tick")
        rec = scorer.score(_env("faction_extinct", tick=gate - 1), _ctx(tick=gate - 1))
        assert rec is not None
        assert "faction_early_extinction" in rec.tags

    def test_no_score_after_gate(self, scorer: FactionScorer) -> None:
        rec = scorer.score(_env("faction_extinct", tick=9999), _ctx(tick=9999))
        assert rec is None


class TestResourceSeized:
    def test_positive(self, scorer: FactionScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("resource_seized"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["economic_military_coupling"]


class TestNullReturn:
    def test_null_unknown(self, scorer: FactionScorer) -> None:
        assert scorer.score(_env("combat_initiated"), _ctx()) is None


class TestBuildingSabotageOwnership:
    def test_building_sabotaged_not_in_faction_event_types(self) -> None:
        assert "building_sabotaged" not in FactionScorer.EVENT_TYPES

    def test_building_sabotaged_not_scored_by_faction(self, scorer: FactionScorer) -> None:
        assert scorer.score(_env("building_sabotaged"), _ctx()) is None
