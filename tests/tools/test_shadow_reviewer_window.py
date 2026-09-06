"""Pure-function unit tests for tools/agent-monitoring/shadow_reviewer_window.py
(TCK-20260904-SHADOW-REVIEWER-LOGGING).

Every test here uses a tmp_path-based agent-monitoring/data/<week>/events.jsonl fixture via
monkeypatch — never the real corpus.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import shadow_reviewer_window as w  # noqa: E402


def _write_events(data_dir: Path, week: str, records: list[dict]) -> None:
    week_dir = data_dir / week
    week_dir.mkdir(parents=True, exist_ok=True)
    events_file = week_dir / "events.jsonl"
    events_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def _shadow_event(reviewer: str, run_id: str, seq: int) -> dict:
    return {
        "run_id": run_id,
        "seq": seq,
        "ts": "2026-09-04T00:00:00Z",
        "phase": "Architecture-Verify" if reviewer == "architecture-reviewer" else "Security-Review",
        "agent": f"{reviewer}-shadow",
        "summary": "shadow",
        "status": "ok",
    }


# ---------------------------------------------------------------------------
# Bounded sample window — skip behavior when closed (AC #4)
# ---------------------------------------------------------------------------


def test_shadow_window_closed_skips_candidate_call(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DATA_DIR", tmp_path)

    max_samples = 50
    records = [
        _shadow_event("architecture-reviewer", f"TCK-FAKE-{i}", -100 - i)
        for i in range(max_samples)
    ]
    _write_events(tmp_path, "2026-W36", records)

    assert w.count_prior_shadow_samples("architecture-reviewer") == max_samples
    assert w.is_shadow_window_open("architecture-reviewer", max_samples) is False

    # One fewer sample -> window still open.
    _write_events(tmp_path, "2026-W36", records[:-1])
    assert w.is_shadow_window_open("architecture-reviewer", max_samples) is True


# ---------------------------------------------------------------------------
# Bounded sample window — independent per-reviewer thresholds (AC #4 + Risk #5)
# ---------------------------------------------------------------------------


def test_shadow_window_thresholds_are_independent_per_reviewer(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DATA_DIR", tmp_path)

    arch_records = [
        _shadow_event("architecture-reviewer", f"TCK-FAKE-ARCH-{i}", -100 - i) for i in range(60)
    ]
    security_records = [
        _shadow_event("security-reviewer", f"TCK-FAKE-SEC-{i}", -200 - i) for i in range(2)
    ]
    _write_events(tmp_path, "2026-W36", arch_records + security_records)

    assert w.is_shadow_window_open("architecture-reviewer", 50) is False
    assert w.is_shadow_window_open("security-reviewer", 10) is True


# ---------------------------------------------------------------------------
# count_prior_shadow_samples_for_run is scoped to one run_id
# ---------------------------------------------------------------------------


def test_count_prior_shadow_samples_for_run_scoped_to_one_run_id(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DATA_DIR", tmp_path)

    records = [
        _shadow_event("architecture-reviewer", "TCK-FAKE-RUN-A", -100),
        _shadow_event("architecture-reviewer", "TCK-FAKE-RUN-A", -101),
        _shadow_event("architecture-reviewer", "TCK-FAKE-RUN-B", -100),
    ]
    _write_events(tmp_path, "2026-W36", records)

    assert w.count_prior_shadow_samples_for_run("architecture-reviewer", "TCK-FAKE-RUN-A") == 2
    assert w.count_prior_shadow_samples_for_run("architecture-reviewer", "TCK-FAKE-RUN-B") == 1
    assert w.count_prior_shadow_samples_for_run("architecture-reviewer", "TCK-FAKE-RUN-C") == 0

    # Cross-run_id total (sample-window scope) differs from any single run_id's own count.
    assert w.count_prior_shadow_samples("architecture-reviewer") == 3


def test_compute_shadow_seq_disjoint_per_reviewer_and_run(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DATA_DIR", tmp_path)

    records = [
        _shadow_event("architecture-reviewer", "TCK-FAKE-SEQ", -100),
        _shadow_event("architecture-reviewer", "TCK-FAKE-SEQ", -101),
    ]
    _write_events(tmp_path, "2026-W36", records)

    # Third architecture-reviewer shadow call for this run_id continues past the prior 2.
    assert w.compute_shadow_seq("architecture-reviewer", "TCK-FAKE-SEQ") == -102
    # security-reviewer's own count for the same run_id is independent (0 prior).
    assert w.compute_shadow_seq("security-reviewer", "TCK-FAKE-SEQ") == -200
