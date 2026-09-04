"""Tests for tools/agent-monitoring/seq_offset.py's compute_seq_offset(),
TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION.

Constructs events as plain Python dicts, mirroring test_validate_agent_monitoring.py's
fixture-construction style — no file I/O, no subprocess, pure-function testing.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from seq_offset import compute_seq_offset  # noqa: E402

_SEQ_OFFSET_PATH = _MONITORING_TOOLS_DIR / "seq_offset.py"


def _event(run_id, seq):
    return {"run_id": run_id, "seq": seq, "ts": "t", "phase": "Implement", "agent": "implementer",
            "status": "ok", "summary": "ok"}


def test_compute_seq_offset_continues_past_prior_session_max_seq():
    fixture = [_event("TCK-FAKE", seq) for seq in range(1, 7)]
    assert compute_seq_offset("TCK-FAKE", fixture) == 6


def test_compute_seq_offset_returns_zero_for_run_id_with_no_prior_history():
    assert compute_seq_offset("TCK-NEW", []) == 0
    unrelated = [_event("TCK-OTHER-A", 1), _event("TCK-OTHER-B", 5)]
    assert compute_seq_offset("TCK-NEW", unrelated) == 0


def test_compute_seq_offset_ignores_other_run_ids():
    fixture = [_event("TCK-FAKE", seq) for seq in range(1, 4)] + \
        [_event("TCK-OTHER", seq) for seq in range(1, 10)]
    assert compute_seq_offset("TCK-FAKE", fixture) == 3


def test_compute_seq_offset_is_read_only():
    fixture = [_event("TCK-FAKE", seq) for seq in range(1, 4)]
    before = copy.deepcopy(fixture)
    compute_seq_offset("TCK-FAKE", fixture)
    assert fixture == before


def test_seq_offset_reads_events_across_multiple_week_folders(tmp_path):
    week1 = tmp_path / "agent-monitoring" / "data" / "2026-W01"
    week1.mkdir(parents=True)
    (week1 / "events.jsonl").write_text(json.dumps(_event("TCK-FAKE", 3)) + "\n", encoding="utf-8")

    week2 = tmp_path / "agent-monitoring" / "data" / "2026-W02"
    week2.mkdir(parents=True)
    (week2 / "events.jsonl").write_text(json.dumps(_event("TCK-FAKE", 9)) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_SEQ_OFFSET_PATH), "TCK-FAKE"],
        cwd=str(tmp_path), capture_output=True, text=True, check=True,
    )
    marker_line = next(line for line in result.stdout.splitlines() if line.startswith("MARKER:"))
    offset = json.loads(marker_line[len("MARKER:"):])
    assert offset == 9
