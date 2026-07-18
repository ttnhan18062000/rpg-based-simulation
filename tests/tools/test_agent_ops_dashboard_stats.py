"""Tests for the /api/stats/agent-monitoring endpoint (TCK-20260718-AGENTOPS-STATS-API).

Covers: happy path against real fixture data, period-selection variants (days/all/week),
empty-data edge case, the None-gate-key sanitization fix, the non-string start_ts legacy-data
guard, and that compute_retro_metrics() is imported (not reimplemented).
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.agent_ops_dashboard import ingest, main


def _init_repo_skeleton(tmp_path: Path) -> None:
    (tmp_path / "agent-monitoring").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "todos").mkdir(parents=True, exist_ok=True)


def _write_runs(tmp_path: Path, rows: list[dict]) -> None:
    runs_file = tmp_path / "agent-monitoring" / "runs.jsonl"
    runs_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def _write_events(tmp_path: Path, rows: list[dict]) -> None:
    events_file = tmp_path / "agent-monitoring" / "events.jsonl"
    events_file.write_text("\n".join(json.dumps(e) for e in rows) + "\n")


_BASE_RUN = {
    "run_id": "TCK-FAKE",
    "start_ts": "2026-07-06T00:00:00Z",
    "end_ts": "2026-07-06T01:00:00Z",
    "workflow": "implement-ticket",
    "tier": "standard",
    "final_status": "DONE",
    "agent_count": 3,
    "duration_s": 600,
}


def test_stats_endpoint_returns_typed_shape_for_all_time(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [_BASE_RUN, dict(_BASE_RUN, run_id="TCK-FAKE-2", final_status="DOD_BLOCKED")])
    _write_events(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert stats.run_summary.total == 2
    assert stats.run_summary.done_count == 1
    assert stats.run_summary.gate_fail_count == 1
    assert "DOD_BLOCKED" in stats.gate_failure_breakdown


def test_stats_endpoint_empty_data_does_not_crash(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [])
    _write_events(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert stats.run_summary.total == 0
    assert stats.gate_failure_breakdown == {}
    assert stats.slow_runs == []


def test_stats_endpoint_none_gate_key_sanitized_to_unknown_string(tmp_path):
    """A run with neither final_status nor status resolves gate to None
    (_resolve_status returns None) — the API boundary must sanitize this to a valid JSON key
    string, never crash with a Pydantic validation error, without touching
    compute_retro_metrics()'s own dict (which legitimately carries the raw None key)."""
    _init_repo_skeleton(tmp_path)
    malformed_run = {
        "run_id": "TCK-NO-STATUS",
        "start_ts": "2026-07-06T00:00:00Z",
        "workflow": "implement-ticket",
        "tier": "standard",
        "agent_count": 1,
    }
    _write_runs(tmp_path, [malformed_run])
    _write_events(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert "unknown" in stats.gate_failure_breakdown
    assert stats.gate_failure_breakdown["unknown"] == 1


def test_stats_endpoint_days_filter_tolerates_legacy_non_string_start_ts(tmp_path):
    """Reproduces the real production bug found live (generate_retro.py --days 7 crashes on
    legacy runs.jsonl records with a raw Unix-timestamp number instead of an ISO8601 string) and
    confirms the new endpoint's own --days path (a fresh implementation, not a call into the
    buggy main()) tolerates it instead of raising."""
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [
        dict(_BASE_RUN, start_ts=1781425809.0960267),  # legacy float start_ts
        dict(_BASE_RUN, run_id="TCK-FAKE-2"),  # normal ISO string start_ts
    ])
    _write_events(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    # Must not raise.
    stats = cache.get_agent_monitoring_stats(days=36500)  # effectively "since forever"
    assert stats.run_summary.total == 1  # only the well-formed record is included


def test_stats_endpoint_route_returns_200_with_all_param(tmp_path, monkeypatch):
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [_BASE_RUN])
    _write_events(tmp_path, [])

    monkeypatch.setattr(main, "_cache", ingest.DashboardCache(repo_root=tmp_path))
    client = TestClient(main.app)

    resp = client.get("/api/stats/agent-monitoring?all=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_summary"]["total"] == 1


def test_ticket_corpus_stats_route_returns_200(tmp_path, monkeypatch):
    _init_repo_skeleton(tmp_path)
    tickets_dir = tmp_path / "tickets" / "done"
    tickets_dir.mkdir(parents=True, exist_ok=True)
    (tickets_dir / "TCK-20260710-FAKE.md").write_text(
        "---\nstatus: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
        "ticket_id: TCK-20260710-FAKE\nphase: done\ndate: 2026-07-10\ntags: []\n---\n\n"
        "# TCK-20260710-FAKE\n\n## Tier\nstandard\n\n## Type\nfeature\n\n"
        "## Priority\nP1\n\n## Status\nDONE\n",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "working_log.csv").write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
        "2026-07-10T00:00:00Z,TCK-20260710-FAKE,x,DONE,x,none\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(main, "_cache", ingest.DashboardCache(repo_root=tmp_path))
    client = TestClient(main.app)

    resp = client.get("/api/stats/tickets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["included_tickets"] == 1
    assert data["distribution"]["tier"]["standard"] == 1


def test_ticket_corpus_stats_empty_corpus_does_not_crash(tmp_path, monkeypatch):
    _init_repo_skeleton(tmp_path)
    (tmp_path / "tickets" / "working_log.csv").write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n", encoding="utf-8"
    )

    monkeypatch.setattr(main, "_cache", ingest.DashboardCache(repo_root=tmp_path))
    client = TestClient(main.app)

    resp = client.get("/api/stats/tickets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["included_tickets"] == 0


def test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented():
    """Source-text anti-drift guard: ingest.py must import compute_retro_metrics from
    generate_retro, never redefine its own copy of the computation."""
    source = Path("src/api/agent_ops_dashboard/ingest.py").read_text(encoding="utf-8")
    assert "from generate_retro import" in source
    assert "compute_retro_metrics" in source
    assert "def compute_retro_metrics(" not in source
