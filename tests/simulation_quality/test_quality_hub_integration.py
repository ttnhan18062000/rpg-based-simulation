"""Integration tests for QualityHub: routing, accumulation, persistence, error isolation, disable."""
from __future__ import annotations
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.quality_hub import QualityHub
from src.simulation_quality.scorers.agency import AgencyScorer
from src.simulation_quality.scorers.combat import CombatScorer
from src.simulation_quality.weights import ScoringWeights


def _env(event_type: str, tick: int = 10, entity_id: int = 1, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex,
        run_id="hub-test",
        tick=tick,
        entity_id=entity_id,
        event_type=event_type,
        event_category="strategy",
        severity="INFO",
        source_system="test",
        message="",
        payload=payload or {},
    )


@pytest.fixture
def hub(scoring_weights: ScoringWeights, tmp_path):
    from src.simulation_quality.persistence import QualityPersistence
    scorers = [AgencyScorer(scoring_weights), CombatScorer(scoring_weights)]
    persistence = QualityPersistence(str(tmp_path))
    return QualityHub(scorers, scoring_weights, persistence, run_id="test-run")


class TestEventRouting:
    def test_agency_event_updates_agency_accumulator(self, hub: QualityHub) -> None:
        hub.on_envelope(_env("action_executed"))
        score = hub.get_pillar_score(PillarId.AGENCY)
        assert score > 0.0

    def test_combat_event_updates_combat_accumulator(self, hub: QualityHub) -> None:
        hub.on_envelope(_env("combat_initiated"))
        score = hub.get_pillar_score(PillarId.COMBAT)
        assert score > 0.0

    def test_unknown_event_no_update(self, hub: QualityHub) -> None:
        hub.on_envelope(_env("completely_unknown_event_xyz"))
        for pid in PillarId:
            assert hub.get_pillar_score(pid) == 0.0


class TestAccumulation:
    def test_raw_score_accumulates(self, hub: QualityHub) -> None:
        hub.on_envelope(_env("action_executed"))
        hub.on_envelope(_env("action_executed"))
        score = hub.get_pillar_score(PillarId.AGENCY)
        assert score > 0.0

    def test_tick_advances(self, hub: QualityHub) -> None:
        hub.on_envelope(_env("action_executed", tick=42))
        assert hub._tick == 42


class TestPersistence:
    def test_persistence_write_called(self, scoring_weights: ScoringWeights, tmp_path) -> None:
        from src.simulation_quality.persistence import QualityPersistence
        mock_persistence = MagicMock(spec=QualityPersistence)
        scorers = [AgencyScorer(scoring_weights)]
        hub = QualityHub(scorers, scoring_weights, mock_persistence, run_id="x")
        hub.on_envelope(_env("action_executed"))
        mock_persistence.write.assert_called_once()


class TestErrorIsolation:
    def test_scorer_exception_does_not_propagate(self, scoring_weights: ScoringWeights, tmp_path) -> None:
        from src.simulation_quality.persistence import QualityPersistence
        from src.simulation_quality.scorers.base import PillarScorer
        from src.simulation_quality.score_record import ScoreRecord

        class BoomScorer(PillarScorer):
            EVENT_TYPES = ("action_executed",)
            def score(self, envelope, context):
                raise RuntimeError("intentional test error")

        good_scorer = AgencyScorer(scoring_weights)
        boom_scorer = BoomScorer(scoring_weights)
        persistence = QualityPersistence(str(tmp_path))
        hub = QualityHub([good_scorer, boom_scorer], scoring_weights, persistence, run_id="x")

        # Should not raise — and good scorer should still score
        hub.on_envelope(_env("action_executed"))
        assert hub.get_pillar_score(PillarId.AGENCY) > 0.0


class TestDisableMechanism:
    def test_disabled_env_blocks_scoring(self, scoring_weights: ScoringWeights, tmp_path, monkeypatch) -> None:
        from src.simulation_quality.persistence import QualityPersistence
        monkeypatch.setenv("QUALITY_SCORING_DISABLED", "1")
        scorers = [AgencyScorer(scoring_weights)]
        persistence = QualityPersistence(str(tmp_path))
        hub = QualityHub(scorers, scoring_weights, persistence, run_id="x")
        hub.on_envelope(_env("action_executed"))
        assert hub.get_pillar_score(PillarId.AGENCY) == 0.0


class TestReadOnlyQueries:
    def test_get_pillar_grade(self, hub: QualityHub) -> None:
        grade = hub.get_pillar_grade(PillarId.AGENCY)
        assert grade in ("S", "A", "B", "C", "D", "F")

    def test_get_quality_report(self, hub: QualityHub) -> None:
        from src.simulation_quality.quality_report import QualityReport
        report = hub.get_quality_report()
        assert isinstance(report, QualityReport)
        assert "AGENCY" in report.pillars
