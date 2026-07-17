"""Tests for src/api/agent_ops_dashboard/main.py's HTTP routes.

Covers TCK-20260716-AGENTOPS-DASHBOARD-BACKEND's AC #5 and the malformed-JSONL
tolerant-loading behavior surfaced through GET /api/health.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.agent_ops_dashboard import main
from src.api.agent_ops_dashboard.ingest import DashboardCache


def _client_with_repo(tmp_path: Path) -> TestClient:
    (tmp_path / "agent-monitoring").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "todos").mkdir(parents=True, exist_ok=True)
    main._cache = DashboardCache(repo_root=tmp_path)
    return TestClient(main.app)


# ---------------------------------------------------------------------------
# AC #5 — GET /api/runs/{run_id} returns 404, never 500 or empty 200
# ---------------------------------------------------------------------------


def test_run_detail_404_for_unknown_run_id(tmp_path):
    client = _client_with_repo(tmp_path)
    resp = client.get("/api/runs/TCK-DOES-NOT-EXIST")
    assert resp.status_code == 404
    assert resp.json()["detail"]


def test_run_timeline_404_for_unknown_run_id(tmp_path):
    client = _client_with_repo(tmp_path)
    resp = client.get("/api/runs/TCK-DOES-NOT-EXIST/timeline")
    assert resp.status_code == 404


def test_run_detail_200_for_known_run_id(tmp_path):
    (tmp_path / "agent-monitoring").mkdir(parents=True, exist_ok=True)
    runs_file = tmp_path / "agent-monitoring" / "runs.jsonl"
    runs_file.write_text(
        json.dumps(
            {
                "run_id": "TCK-KNOWN",
                "start_ts": "2026-07-01T00:00:00Z",
                "end_ts": "2026-07-01T01:00:00Z",
                "workflow": "implement-ticket",
                "tier": "hotfix",
                "final_status": "DONE",
                "agent_count": 3,
                "duration_s": 3600,
            }
        )
        + "\n"
    )
    client = _client_with_repo(tmp_path)
    resp = client.get("/api/runs/TCK-KNOWN")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "TCK-KNOWN"
    assert body["final_status"] == "DONE"
    assert body["is_inferred_active"] is False


# ---------------------------------------------------------------------------
# Malformed JSONL line: never crashes the API, counted in /api/health
# ---------------------------------------------------------------------------


def test_malformed_jsonl_line_skipped_and_counted_in_health(tmp_path):
    (tmp_path / "agent-monitoring").mkdir(parents=True, exist_ok=True)
    runs_file = tmp_path / "agent-monitoring" / "runs.jsonl"
    runs_file.write_text(
        '{"run_id": "TCK-OK", "start_ts": "2026-07-01T00:00:00Z", "final_status": "DONE"}\n'
        "{this is not valid json\n"
    )
    client = _client_with_repo(tmp_path)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["unparsed_lines"]["runs.jsonl"] == 1

    # The one valid row must still be usable — the malformed line never crashes anything.
    resp_runs = client.get("/api/runs")
    assert resp_runs.status_code == 200
    assert any(r["run_id"] == "TCK-OK" for r in resp_runs.json())


def test_health_status_is_always_ok_even_with_parse_errors(tmp_path):
    (tmp_path / "agent-monitoring").mkdir(parents=True, exist_ok=True)
    events_file = tmp_path / "agent-monitoring" / "events.jsonl"
    events_file.write_text("garbage\ngarbage\ngarbage\n")
    client = _client_with_repo(tmp_path)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["unparsed_lines"]["events.jsonl"] == 3
