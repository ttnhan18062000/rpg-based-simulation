"""SimQ scores a run from its lossless simulation_events.jsonl, offline (decision 80 C, TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.simulation_quality.offline import (
    EVENTS_FILE,
    OFFLINE_GENERATED_AT,
    RunNotReplayable,
    build_hub,
    iter_envelopes,
    replay_run_dir,
    require_replayable,
    score_run_dir,
)
from src.simulation_quality.weights import ScoringWeights


def _weights() -> ScoringWeights:
    return ScoringWeights.load(
        "config/simulation_quality/scoring_weights.yaml",
        "config/simulation_quality/grade_thresholds.yaml",
        "config/simulation_quality/detection_params.yaml",
        "default",
    )


def _event(i: int, event_type: str, **payload) -> dict:
    return {
        "event_id": f"e{i}", "run_id": "r", "tick": i, "entity_id": 1 + i % 3, "event_type": event_type, "event_category": "combat",
        "severity": "INFO", "source_system": "test", "message": event_type, "payload": payload, "related_entity_ids": [2, 3],
    }


def _run_dir(tmp_path: Path, name: str = "run_a", extra_lines: tuple[str, ...] = ()) -> Path:
    run_dir = tmp_path / name
    run_dir.mkdir()
    events = [_event(i, "combat_kill" if i % 2 else "xp_granted", amount=5) for i in range(1, 41)]
    lines = [json.dumps(e) for e in events] + list(extra_lines)
    (run_dir / EVENTS_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return run_dir


def test_a_run_without_the_lossless_file_is_refused(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(RunNotReplayable, match="no simulation_events.jsonl"):
        require_replayable(empty)
    with pytest.raises(RunNotReplayable):
        score_run_dir(empty, _weights(), tmp_path / "out")
    assert not (tmp_path / "out" / "quality_report.json").exists()


def test_the_same_run_dir_gives_a_byte_identical_report(tmp_path):
    run_dir = _run_dir(tmp_path)
    report_a, result_a = score_run_dir(run_dir, _weights(), tmp_path / "a")
    report_b, result_b = score_run_dir(run_dir, _weights(), tmp_path / "b")
    assert report_a.generated_at == OFFLINE_GENERATED_AT
    for name in ("quality_report.json", "quality_scores.jsonl"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    assert (tmp_path / "a" / "quality_report.json").stat().st_size > 0
    assert result_a == result_b


def test_per_type_event_counts_are_an_output_keyed_by_the_type_in_the_file(tmp_path):
    run_dir = _run_dir(tmp_path)
    hub, persistence = build_hub(_weights(), tmp_path / "out", "r")
    try:
        result = replay_run_dir(run_dir, hub)
    finally:
        persistence.shutdown()
    # combat_kill is translated to entity_killed inside the hub; the count stays under the name in the file
    assert result.event_counts_by_type == {"combat_kill": 20, "xp_granted": 20}
    assert result.event_count == 40 and result.skipped_lines == 0


def test_an_unreadable_line_is_counted_and_skipped_not_fatal(tmp_path):
    run_dir = _run_dir(tmp_path, extra_lines=("{not json", json.dumps({"event_type": "missing the other fields"})))
    hub, persistence = build_hub(_weights(), tmp_path / "out", "r")
    try:
        result = replay_run_dir(run_dir, hub)
    finally:
        persistence.shutdown()
    assert result.event_count == 40 and result.skipped_lines == 2


def test_the_replay_scores_what_the_live_hub_scores_for_the_same_events(tmp_path):
    run_dir = _run_dir(tmp_path)
    live_hub, live_persistence = build_hub(_weights(), tmp_path / "live", "r")
    try:
        for envelope in iter_envelopes(str(run_dir / EVENTS_FILE)):
            live_hub.on_envelope(envelope)
        live = live_hub.get_quality_report(generated_at=OFFLINE_GENERATED_AT)
    finally:
        live_persistence.shutdown()
    offline, _ = score_run_dir(run_dir, _weights(), tmp_path / "off", run_id="r")
    assert json.dumps(live.to_dict(), sort_keys=True) == json.dumps(offline.to_dict(), sort_keys=True)


def test_scoring_switched_off_refuses_instead_of_writing_an_empty_report(tmp_path, monkeypatch):
    monkeypatch.setenv("QUALITY_SCORING_DISABLED", "1")
    with pytest.raises(RunNotReplayable, match="QUALITY_SCORING_DISABLED"):
        score_run_dir(_run_dir(tmp_path), _weights(), tmp_path / "out")


def _write_manifest(run_dir: Path, **fields) -> None:
    path = RunArtifactRepository(base_dir=str(run_dir.parent)).resolve_path(run_dir.name, "manifest")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"run_id": run_dir.name, **fields}), encoding="utf-8")


def test_a_run_not_recorded_host_independent_is_refused_when_asked(tmp_path):
    run_dir = _run_dir(tmp_path)
    with pytest.raises(RunNotReplayable, match="host-independent"):
        score_run_dir(run_dir, _weights(), tmp_path / "o1", require_host_independent=True)  # no manifest at all
    _write_manifest(run_dir, signals_zeroed=False)
    with pytest.raises(RunNotReplayable, match="host-independent"):
        score_run_dir(run_dir, _weights(), tmp_path / "o2", require_host_independent=True)
    _write_manifest(run_dir, signals_zeroed=True, audit_mode=True)
    report, _ = score_run_dir(run_dir, _weights(), tmp_path / "o3", require_host_independent=True)
    assert report.tick_count > 0
