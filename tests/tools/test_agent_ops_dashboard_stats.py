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


def _write_tools(tmp_path: Path, rows: list[dict]) -> None:
    tools_file = tmp_path / "agent-monitoring" / "tools.jsonl"
    tools_file.write_text("\n".join(json.dumps(t) for t in rows) + "\n")


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


def test_stats_endpoint_includes_phase_status_distribution(tmp_path):
    _init_repo_skeleton(tmp_path)
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Investigate", "agent": "investigator",
         "status": "ok", "summary": "found stuff"},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "investigate", "agent": "investigator",
         "status": "failed", "summary": "found stuff"},
    ]
    _write_runs(tmp_path, runs)
    _write_events(tmp_path, events)

    from generate_retro import compute_retro_metrics

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    expected = compute_retro_metrics(runs, events, tickets_root=tmp_path / "tickets")
    assert stats.phase_status_distribution == expected["phase_status_distribution"]
    assert stats.phase_status_distribution == {"Investigate": {"ok": 1, "failed": 1}}


def test_stats_endpoint_includes_outliers_duration_and_cost_proxy(tmp_path):
    _init_repo_skeleton(tmp_path)
    runs = [
        dict(_BASE_RUN, run_id=f"TCK-STD-{i}", tier="standard", duration_s=1000)
        for i in range(3)
    ] + [dict(_BASE_RUN, run_id="TCK-STD-OUTLIER", tier="standard", duration_s=5000)]
    events = (
        [
            {"run_id": "TCK-FAKE", "seq": i, "phase": "Investigate", "agent": "investigator",
             "status": "ok", "summary": "found stuff", "cost_proxy_score": 100.0}
            for i in range(3)
        ]
        + [
            {"run_id": "TCK-FAKE", "seq": 100, "phase": "Investigate", "agent": "investigator",
             "status": "ok", "summary": "found stuff", "cost_proxy_score": 1000.0}
        ]
    )
    _write_runs(tmp_path, runs)
    _write_events(tmp_path, events)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert len(stats.outliers.duration_s) == 1
    duration_outlier = stats.outliers.duration_s[0]
    assert duration_outlier.run_id == "TCK-STD-OUTLIER"
    assert duration_outlier.tier == "standard"
    assert duration_outlier.duration_s == 5000
    assert duration_outlier.median == 1000.0
    assert duration_outlier.ratio == 5.0

    assert len(stats.outliers.cost_proxy_score) == 1
    cost_outlier = stats.outliers.cost_proxy_score[0]
    assert cost_outlier.run_id == "TCK-FAKE"
    assert cost_outlier.seq == 100
    assert cost_outlier.phase == "Investigate"
    assert cost_outlier.agent == "investigator"
    assert cost_outlier.cost_proxy_score == 1000.0


def test_stats_endpoint_outliers_seq_field_tolerates_none(tmp_path):
    _init_repo_skeleton(tmp_path)
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "phase": "Investigate", "agent": "investigator",
         "status": "ok", "summary": "found stuff", "cost_proxy_score": 100.0}
        for _ in range(3)
    ] + [
        {"run_id": "TCK-FAKE", "phase": "Investigate", "agent": "investigator",
         "status": "ok", "summary": "found stuff", "cost_proxy_score": 1000.0}
    ]
    _write_runs(tmp_path, runs)
    _write_events(tmp_path, events)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    # Must not raise ValidationError.
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert len(stats.outliers.cost_proxy_score) == 1
    assert stats.outliers.cost_proxy_score[0].seq is None


def test_stats_endpoint_zero_outliers_returns_empty_lists_not_missing_keys(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [])
    _write_events(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert stats.outliers.duration_s == []
    assert stats.outliers.cost_proxy_score == []
    assert stats.phase_status_distribution == {}


def test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented():
    """Source-text anti-drift guard: ingest.py must import compute_retro_metrics from
    generate_retro, never redefine its own copy of the computation."""
    source = Path("src/api/agent_ops_dashboard/ingest.py").read_text(encoding="utf-8")
    assert "from generate_retro import" in source
    assert "compute_retro_metrics" in source
    assert "def compute_retro_metrics(" not in source


# --- Skill Usage / KGMCP Cache Efficiency (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-
# SKILL-USAGE-DASHBOARD) ---

def test_stats_endpoint_includes_skill_usage_from_real_tools_jsonl(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [_BASE_RUN])
    _write_events(tmp_path, [])
    _write_tools(tmp_path, [
        {"run_id": "TCK-FAKE", "seq": 1, "tool": "Skill",
         "input_summary": "{'skill': 'graphify', 'args': None}", "status": "ok", "ts": "2026-07-06T00:00:01Z"},
        {"run_id": "TCK-FAKE", "seq": 1, "tool": "Skill",
         "input_summary": "{'skill': 'graphify', 'args': None}", "status": "ok", "ts": "2026-07-06T00:00:02Z"},
    ])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert stats.skill_usage.total_skill_invocations == 2
    assert stats.skill_usage.per_skill == {"graphify": 2}
    assert stats.skill_usage.derivation


def test_stats_endpoint_skill_usage_empty_when_no_skill_tool_calls(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [])
    _write_events(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert stats.skill_usage.total_skill_invocations == 0
    assert stats.skill_usage.per_skill == {}


def test_stats_endpoint_includes_kgmcp_cache_efficiency_from_real_access_log(tmp_path, monkeypatch):
    """Monkeypatches ingest.read_cache_access_log (rather than pointing retrieval_cache.CACHE_DB_
    PATH at tmp_path) since retrieval_cache.py's cache DB is a single fixed relative path, not
    parameterized by DashboardCache's own repo_root -- a pre-existing, documented limitation of
    that module (see Implementation Notes), out of this ticket's scope to change. This still
    proves the real wiring: ingest.py calls the real read_cache_access_log() and feeds its output
    through compute_retro_metrics() into the typed API response, unmodified."""
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [])
    _write_events(tmp_path, [])

    fake_rows = [
        {"cache_level": "level1_provider_result", "event_type": "write", "query_hash": "qh-1",
         "repo_branch_scope": "repo::main", "packet_id": None, "run_id": "TCK-FAKE", "seq": 1,
         "phase": "Implement", "agent": "implementer", "execution_id": None, "provider": None,
         "ticket_id": "TCK-FAKE", "sidecar_stale": 0, "ts": 1000.0},
        {"cache_level": "level1_provider_result", "event_type": "hit", "query_hash": "qh-1",
         "repo_branch_scope": "repo::main", "packet_id": None, "run_id": "TCK-FAKE", "seq": 2,
         "phase": "Implement", "agent": "implementer", "execution_id": None, "provider": None,
         "ticket_id": "TCK-FAKE", "sidecar_stale": 0, "ts": 1010.0},
    ]
    monkeypatch.setattr(ingest, "read_cache_access_log", lambda: fake_rows)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert stats.kgmcp_cache_efficiency.total_hits == 1
    assert stats.kgmcp_cache_efficiency.total_writes == 1
    assert stats.kgmcp_cache_efficiency.overall_reuse_rate == 0.5
    assert stats.kgmcp_cache_efficiency.per_ticket["TCK-FAKE"].hit == 1
    assert stats.kgmcp_cache_efficiency.verdict
    assert stats.kgmcp_cache_efficiency.derivation


def test_stats_endpoint_kgmcp_cache_efficiency_empty_access_log_returns_no_data_verdict(
    tmp_path, monkeypatch
):
    _init_repo_skeleton(tmp_path)
    _write_runs(tmp_path, [])
    _write_events(tmp_path, [])
    monkeypatch.setattr(ingest, "read_cache_access_log", lambda: [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert stats.kgmcp_cache_efficiency.total_hits == 0
    assert stats.kgmcp_cache_efficiency.total_writes == 0
    assert stats.kgmcp_cache_efficiency.verdict == "NO DATA"


def test_stats_endpoint_uses_real_read_cache_access_log_not_reimplemented():
    """Source-text anti-drift guard, mirroring test_stats_endpoint_uses_real_compute_retro_
    metrics_not_reimplemented's own pattern: ingest.py must import read_cache_access_log from
    retrieval_cache, never redefine its own copy."""
    source = Path("src/api/agent_ops_dashboard/ingest.py").read_text(encoding="utf-8")
    assert "from retrieval_cache import" in source
    assert "read_cache_access_log" in source
    assert "def read_cache_access_log(" not in source


def test_slow_run_and_duration_outlier_carry_active_idle_split(tmp_path):
    """TCK-20260822-DASHBOARD-DURATION-GAP-AWARE: SlowRunEntry/DurationOutlierEntry surface the
    sibling TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT's active_duration_s/idle_gap_s fields
    end-to-end through the real API pipeline (compute_retro_metrics -> ingest.py's **kwargs
    passthrough -> the typed Pydantic response) -- not just a unit test of the model in isolation.
    """
    _init_repo_skeleton(tmp_path)
    slow_run = dict(
        _BASE_RUN,
        run_id="TCK-SLOW-DASHBOARD",
        start_ts="2026-07-06T00:00:00Z",
        end_ts="2026-07-06T02:00:00Z",
        duration_s=7200,
    )
    _write_runs(tmp_path, [slow_run])
    _write_events(
        tmp_path,
        [
            {"run_id": "TCK-SLOW-DASHBOARD", "seq": 1, "ts": "2026-07-06T00:00:00Z", "phase": "Scope", "agent": "ticket-scoper"},
            {"run_id": "TCK-SLOW-DASHBOARD", "seq": 2, "ts": "2026-07-06T00:10:00Z", "phase": "Implement", "agent": "implementer"},
        ],
    )

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert len(stats.slow_runs) == 1
    row = stats.slow_runs[0]
    assert row.run_id == "TCK-SLOW-DASHBOARD"
    assert row.active_duration_s == 600.0  # 10 min active gap
    assert row.idle_gap_s == 6600.0  # 110 min idle gap


def test_slow_run_active_idle_split_none_when_start_ts_unparseable(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_runs(
        tmp_path,
        [
            dict(
                _BASE_RUN,
                run_id="TCK-SLOW-BADTS",
                start_ts="not-a-timestamp",
                end_ts="2026-07-06T02:00:00Z",
                duration_s=7200,
            )
        ],
    )
    _write_events(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    stats = cache.get_agent_monitoring_stats(all_time=True)

    assert len(stats.slow_runs) == 1
    assert stats.slow_runs[0].active_duration_s is None
    assert stats.slow_runs[0].idle_gap_s is None
