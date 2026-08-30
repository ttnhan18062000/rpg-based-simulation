from __future__ import annotations
import json
import os
import pytest

from src.simulation_quality.persistence import QualityPersistence
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.pillar_accumulator import PillarAccumulator
from src.simulation_quality.quality_report import QualityReportBuilder
from src.simulation_quality.score_record import ScoreRecord


def _make_record(event_id: str, delta: float) -> ScoreRecord:
    return ScoreRecord(
        tick=1,
        event_id=event_id,
        pillar=PillarId.ECONOMY,
        delta=delta,
        reason="test",
        event_type="test_event",
        entity_id=1,
        region_id="test_region",
        tags=("harvest_active",),
    )


def test_write_appends_jsonl_line(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "run1")
    persistence = QualityPersistence(run_dir)
    try:
        record = _make_record("e1", 3.0)
        persistence.write(record)
        jsonl_path = os.path.join(run_dir, "quality_scores.jsonl")
        assert os.path.exists(jsonl_path)
    finally:
        # Records are batch-flushed every _FLUSH_INTERVAL writes (not per-write) —
        # shutdown() flushes any remainder, so read the file only after it.
        persistence.shutdown()
    with open(jsonl_path, "r") as fh:
        line = fh.readline()
    data = json.loads(line)
    assert data["event_id"] == "e1"
    assert data["delta"] == pytest.approx(3.0)
    assert data["pillar"] == "ECONOMY"


def test_write_multiple_appends_multiple_lines(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "run2")
    persistence = QualityPersistence(run_dir)
    try:
        for i in range(5):
            persistence.write(_make_record(f"e{i}", float(i)))
        jsonl_path = os.path.join(run_dir, "quality_scores.jsonl")
    finally:
        # Records are batch-flushed every _FLUSH_INTERVAL writes (not per-write) —
        # shutdown() flushes any remainder, so read the file only after it.
        persistence.shutdown()
    with open(jsonl_path, "r") as fh:
        lines = fh.readlines()
    assert len(lines) == 5


def test_write_report_creates_json_file(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "run3")
    persistence = QualityPersistence(run_dir)
    try:
        acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
        report = QualityReportBuilder.build(
            {PillarId.ECONOMY: acc},
            current_tick=10,
            run_id="test-run",
            weights=scoring_weights,
        )
        persistence.write_report(report)
        report_path = os.path.join(run_dir, "quality_report.json")
        assert os.path.exists(report_path)
        with open(report_path, "r") as fh:
            data = json.load(fh)
        assert data["run_id"] == "test-run"
    finally:
        persistence.shutdown()


def test_write_report_is_atomic_no_tmp_leftover(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "run4")
    persistence = QualityPersistence(run_dir)
    try:
        acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
        report = QualityReportBuilder.build(
            {PillarId.ECONOMY: acc},
            current_tick=10,
            run_id="r1",
            weights=scoring_weights,
        )
        persistence.write_report(report)
        tmp_path_file = os.path.join(run_dir, "quality_report.json.tmp")
        assert not os.path.exists(tmp_path_file)
    finally:
        persistence.shutdown()


def test_write_exception_does_not_propagate(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "run5")
    persistence = QualityPersistence(run_dir)
    try:
        persistence._file_handle = None
        record = _make_record("e1", 1.0)
        persistence.write(record)
    finally:
        persistence.shutdown()


def test_write_to_correct_path(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "data" / "runs" / "run-xyz")
    persistence = QualityPersistence(run_dir)
    try:
        persistence.write(_make_record("e1", 1.0))
        assert os.path.exists(os.path.join(run_dir, "quality_scores.jsonl"))
    finally:
        persistence.shutdown()


def test_quality_persistence_write_does_not_flush_every_record(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "run6")
    persistence = QualityPersistence(run_dir)
    try:
        flush_calls = {"count": 0}
        real_flush = persistence._file_handle.flush

        def _spy_flush():
            flush_calls["count"] += 1
            real_flush()

        persistence._file_handle.flush = _spy_flush

        write_count = persistence._FLUSH_INTERVAL - 1
        for i in range(write_count):
            persistence.write(_make_record(f"e{i}", float(i)))

        assert flush_calls["count"] < write_count
        assert flush_calls["count"] == 0

        # Crossing the flush interval triggers exactly one flush and resets the counter.
        persistence.write(_make_record("e_boundary", 1.0))
        assert flush_calls["count"] == 1
        assert persistence._pending_writes == 0
    finally:
        persistence.shutdown()


def test_quality_persistence_shutdown_flushes_remaining_records(tmp_path, scoring_weights):
    run_dir = str(tmp_path / "run7")
    persistence = QualityPersistence(run_dir)
    flush_calls = {"count": 0}
    real_flush = persistence._file_handle.flush

    def _spy_flush():
        flush_calls["count"] += 1
        real_flush()

    persistence._file_handle.flush = _spy_flush

    persistence.write(_make_record("e1", 1.0))
    assert flush_calls["count"] == 0

    persistence.shutdown()
    # shutdown() explicitly flushes before close(), and TextIOWrapper.close()
    # itself flushes internally too — assert "at least one", not an exact count.
    assert flush_calls["count"] >= 1

    jsonl_path = os.path.join(run_dir, "quality_scores.jsonl")
    with open(jsonl_path, "r") as fh:
        lines = fh.readlines()
    assert len(lines) == 1
