"""Performance tests for Simulation Quality Scoring.

Tests use timeit for stable measurement — no pytest-benchmark dependency.
Marked @pytest.mark.slow; skipped in fast CI (pytest -m "not slow").

Limits:
- scorer.score() median < 0.1 ms over 10,000 events
- QualityReport.build() < 50 ms with all 10 accumulators populated
- worst_events ≤ 100 entries after 10,000 events
- window_buffer ≤ 200 entries at all times
"""
from __future__ import annotations
import os
import timeit
import uuid
import tempfile
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.weights import ScoringWeights


_WEIGHTS_PATH = os.path.join("config/simulation_quality/scoring_weights.yaml")
_GRADE_PATH = os.path.join("config/simulation_quality/grade_thresholds.yaml")
_DETECTION_PATH = os.path.join("config/simulation_quality/detection_params.yaml")


@pytest.fixture(scope="module")
def weights() -> ScoringWeights:
    return ScoringWeights.load(_WEIGHTS_PATH, _GRADE_PATH, _DETECTION_PATH, "default")


def _env(event_type: str, tick: int = 1) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="perf-test", tick=tick, entity_id=1,
        event_type=event_type, event_category="test", severity="INFO",
        source_system="test", message="", payload={},
    )


def _ctx(tick: int = 1) -> ScoringContext:
    return ScoringContext(
        run_id="perf-test", current_tick=tick, entity_count=100,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: {} for p in PillarId},
    )


@pytest.mark.slow
def test_agency_scorer_median_under_0_1ms(weights: ScoringWeights) -> None:
    from src.simulation_quality.scorers.agency import AgencyScorer
    scorer = AgencyScorer(weights)
    env = _env("action_executed")
    ctx = _ctx()

    elapsed = timeit.timeit(lambda: scorer.score(env, ctx), number=10_000)
    median_ms = (elapsed / 10_000) * 1000
    assert median_ms < 0.1, f"AgencyScorer.score() median {median_ms:.4f}ms exceeds 0.1ms limit"


@pytest.mark.slow
def test_combat_scorer_median_under_0_1ms(weights: ScoringWeights) -> None:
    from src.simulation_quality.scorers.combat import CombatScorer
    scorer = CombatScorer(weights)
    env = _env("combat_initiated")
    ctx = _ctx()

    elapsed = timeit.timeit(lambda: scorer.score(env, ctx), number=10_000)
    median_ms = (elapsed / 10_000) * 1000
    assert median_ms < 0.1, f"CombatScorer.score() median {median_ms:.4f}ms exceeds 0.1ms limit"


@pytest.mark.slow
def test_quality_report_build_under_50ms(weights: ScoringWeights) -> None:
    from src.simulation_quality.pillar_accumulator import PillarAccumulator
    from src.simulation_quality.quality_report import QualityReportBuilder

    accumulators = {pid: PillarAccumulator(pid, weights) for pid in PillarId}

    # Populate each accumulator with 100 records
    for pid in PillarId:
        for i in range(100):
            rec = ScoreRecord(
                tick=i, event_id=uuid.uuid4().hex, pillar=pid,
                delta=1.0, reason="perf-fill", event_type="action_executed",
                entity_id=i, region_id=None, tags=("perf",),
            )
            accumulators[pid].add(rec)

    elapsed = timeit.timeit(
        lambda: QualityReportBuilder.build(accumulators, 100, "perf-test", weights),
        number=100,
    )
    avg_ms = (elapsed / 100) * 1000
    assert avg_ms < 50, f"QualityReportBuilder.build() avg {avg_ms:.2f}ms exceeds 50ms limit"


@pytest.mark.slow
def test_worst_events_bounded_at_100(weights: ScoringWeights) -> None:
    from src.simulation_quality.pillar_accumulator import PillarAccumulator

    acc = PillarAccumulator(PillarId.AGENCY, weights)
    for i in range(10_000):
        rec = ScoreRecord(
            tick=i, event_id=uuid.uuid4().hex, pillar=PillarId.AGENCY,
            delta=-float(i % 10 + 1), reason="perf-fill", event_type="action_executed",
            entity_id=i, region_id=None, tags=("perf",),
        )
        acc.add(rec)

    snap = acc.snapshot()
    assert len(snap["worst_events"]) <= 100, (
        f"worst_events has {len(snap['worst_events'])} entries; limit is 100"
    )


@pytest.mark.slow
def test_window_buffer_bounded_at_200(weights: ScoringWeights) -> None:
    from src.simulation_quality.pillar_accumulator import PillarAccumulator

    acc = PillarAccumulator(PillarId.ECONOMY, weights)
    for i in range(10_000):
        rec = ScoreRecord(
            tick=i, event_id=uuid.uuid4().hex, pillar=PillarId.ECONOMY,
            delta=1.0, reason="perf-fill", event_type="resource_harvested",
            entity_id=i, region_id=None, tags=("harvest_active",),
        )
        acc.add(rec)

    snap = acc.snapshot()
    assert len(snap["window_buffer"]) <= 200, (
        f"window_buffer has {len(snap['window_buffer'])} entries; limit is 200"
    )


@pytest.mark.slow
def test_quality_hub_on_envelope_non_blocking(weights: ScoringWeights) -> None:
    """on_envelope() must complete without deadlock from nested lock acquisition."""
    import threading
    from src.simulation_quality.quality_hub import QualityHub
    from src.simulation_quality.scorers.agency import AgencyScorer
    from src.simulation_quality.persistence import QualityPersistence

    with tempfile.TemporaryDirectory() as run_dir:
        persistence = QualityPersistence(run_dir)
        hub = QualityHub([AgencyScorer(weights)], weights, persistence, run_id="perf-nonblock")

        env = _env("action_executed", tick=1)
        completed = threading.Event()

        def _run():
            hub.on_envelope(env)
            completed.set()

        t = threading.Thread(target=_run)
        t.start()
        t.join(timeout=1.0)
        assert completed.is_set(), "on_envelope() timed out — possible deadlock"
        persistence.shutdown()
