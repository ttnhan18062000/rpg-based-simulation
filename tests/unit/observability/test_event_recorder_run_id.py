"""The recorder stamps its run id on every envelope, so the event file does not say ``unknown_run``."""
from __future__ import annotations

import json
from pathlib import Path

from src.observability.event_recorder import EventRecorder
from src.observability.events import SimulationEvent


def _ev() -> SimulationEvent:
    return SimulationEvent(event_type="t", event_category="lifecycle", tick=1, severity="INFO", source_system="test", message="", entity_id=1)


def _run_ids(run_dir: str, run_id) -> list[str]:
    recorder = EventRecorder(run_dir=run_dir, enabled=True)
    recorder.run_id = run_id
    recorder.record(_ev())
    recorder.shutdown()
    return [json.loads(line)["run_id"] for line in Path(recorder.filepath).read_text(encoding="utf-8").splitlines()]


def test_the_recorders_run_id_is_written_on_each_event_line(tmp_path):
    assert _run_ids(str(tmp_path / "a"), "run_abc") == ["run_abc"]


def test_a_recorder_given_no_run_id_keeps_the_unknown_run_fallback(tmp_path):
    assert _run_ids(str(tmp_path / "b"), None) == ["unknown_run"]
