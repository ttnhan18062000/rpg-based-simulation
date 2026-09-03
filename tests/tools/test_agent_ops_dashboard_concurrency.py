"""Concurrency tests for src/api/agent_ops_dashboard/ingest.py::DashboardCache.

Covers TCK-20260716-AGENTOPS-DASHBOARD-BACKEND's AC #4 (RLock-per-method,
matching src/api/read_model_cache.py::ReadModelCache's exact locking pattern —
concurrent requests during a rebuild never observe a partially-rebuilt
structure) and AC #8 under concurrent reads (a completing run's
is_inferred_active flip is atomic together with its timestamp switch).

Uses real threading.Thread instances (not a single-threaded proxy), with a
monkeypatched delay in one parse step to deterministically widen the race
window instead of relying on real timing luck.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.api.agent_ops_dashboard import ingest


_FIXTURE_WEEK = "2026-W23"


def _init_repo(tmp_path: Path) -> None:
    (tmp_path / "agent-monitoring" / "data" / _FIXTURE_WEEK).mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "todos").mkdir(parents=True, exist_ok=True)


def _write_ticket(tmp_path: Path, ticket_id: str) -> None:
    p = tmp_path / "tickets" / "inprogress" / f"{ticket_id}.md"
    fm = (
        "status: active\nlayer: observability\nauthority: P1\naudience: agent\n"
        f"ticket_id: {ticket_id}\nphase: open\ndate: 2026-07-16\ntags: []"
    )
    p.write_text(f"---\n{fm}\n---\n\n# {ticket_id}\n", encoding="utf-8")


def _append_run(tmp_path: Path, run_id: str) -> None:
    runs_file = tmp_path / "agent-monitoring" / "data" / _FIXTURE_WEEK / "runs.jsonl"
    existing = runs_file.read_text() if runs_file.exists() else ""
    row = json.dumps(
        {
            "run_id": run_id,
            "start_ts": "2026-07-16T10:00:00Z",
            "end_ts": "2026-07-16T10:10:00Z",
            "workflow": "implement-ticket",
            "tier": "hotfix",
            "final_status": "DONE",
            "agent_count": 1,
            "duration_s": 600,
        }
    )
    runs_file.write_text(existing + row + "\n")


def _patch_slow_parse(monkeypatch, delay: float = 0.02) -> None:
    """Widen the rebuild's critical section deterministically, rather than
    relying on real filesystem/timing luck to expose a race."""
    original_parse = ingest.parse_ticket_file

    def slow_parse(*args, **kwargs):
        time.sleep(delay)
        return original_parse(*args, **kwargs)

    monkeypatch.setattr(ingest, "parse_ticket_file", slow_parse)


# ---------------------------------------------------------------------------
# AC #4 — no reader ever observes a half-old/half-new snapshot
# ---------------------------------------------------------------------------


def test_concurrent_requests_never_observe_partial_rebuild(tmp_path, monkeypatch):
    """A single DashboardCache.get_run() call reads tickets_by_id, runs_by_id,
    and inferred_active together under one lock acquisition — this is the
    property that must never tear. (Two independently-locked calls, e.g.
    get_tickets() followed by get_runs(), can legitimately straddle two
    different rebuilds even when each individual rebuild is atomic — that is
    not what AC #4 guards against, so this test deliberately reads both
    ticket and run state through one call.)
    """
    _init_repo(tmp_path)
    _write_ticket(tmp_path, "TCK-20260101-OLD")

    cache = ingest.DashboardCache(repo_root=tmp_path)
    cache.get_tickets()  # prime the cache with state A

    _patch_slow_parse(monkeypatch)

    new_id = "TCK-20260102-NEW"
    snapshots: list[tuple[bool, bool]] = []
    stop = threading.Event()

    def reader() -> None:
        while not stop.is_set():
            detail = cache.get_run(new_id)
            if detail is not None:
                has_run = detail.final_status == "DONE"
                has_ticket_title = detail.ticket_title is not None
                snapshots.append((has_run, has_ticket_title))

    reader_threads = [threading.Thread(target=reader) for _ in range(4)]
    for t in reader_threads:
        t.start()

    time.sleep(0.01)
    # A ticket and a run sharing the same id land together — a torn rebuild
    # would show one present without the other in some observed snapshot.
    _write_ticket(tmp_path, new_id)
    _append_run(tmp_path, new_id)

    time.sleep(0.2)
    stop.set()
    for t in reader_threads:
        t.join(timeout=5)

    assert snapshots, "no snapshots collected — reader threads did not run"
    inconsistent = [s for s in snapshots if s[0] != s[1]]
    assert not inconsistent, f"observed partially-rebuilt snapshots: {inconsistent}"
    assert (True, True) in snapshots, "rebuild never appeared to complete during the test window"


# ---------------------------------------------------------------------------
# AC #8 under concurrency — the active->completed flip is atomic
# ---------------------------------------------------------------------------


def test_active_run_completion_flips_atomically_under_concurrent_reads(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    now = datetime.now(timezone.utc)
    live_ts = (now - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    tools_file = tmp_path / "agent-monitoring" / "data" / _FIXTURE_WEEK / "tools.jsonl"
    tools_file.write_text(
        json.dumps(
            {
                "run_id": "TCK-LIVE-X",
                "seq": 1,
                "ts": live_ts,
                "tool": "Read",
                "input_summary": "/x.py",
                "status": "ok",
                "duration_ms": 5,
            }
        )
        + "\n"
    )

    cache = ingest.DashboardCache(repo_root=tmp_path)
    primed = cache.get_run("TCK-LIVE-X")
    assert primed is not None and primed.is_inferred_active is True

    _patch_slow_parse(monkeypatch)

    violations = []
    stop = threading.Event()

    def reader() -> None:
        while not stop.is_set():
            run = cache.get_run("TCK-LIVE-X")
            if run is not None and run.is_inferred_active and run.end_ts:
                violations.append(run)

    reader_threads = [threading.Thread(target=reader) for _ in range(4)]
    for t in reader_threads:
        t.start()

    time.sleep(0.01)
    runs_file = tmp_path / "agent-monitoring" / "data" / _FIXTURE_WEEK / "runs.jsonl"
    end_ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    runs_file.write_text(
        json.dumps(
            {
                "run_id": "TCK-LIVE-X",
                "start_ts": live_ts,
                "end_ts": end_ts,
                "workflow": "implement-ticket",
                "tier": "hotfix",
                "final_status": "DONE",
                "agent_count": 1,
                "duration_s": 120,
            }
        )
        + "\n"
    )

    time.sleep(0.2)
    stop.set()
    for t in reader_threads:
        t.join(timeout=5)

    assert not violations, f"observed is_inferred_active=True with a populated end_ts: {violations}"

    final = cache.get_run("TCK-LIVE-X")
    assert final is not None
    assert final.is_inferred_active is False
    assert final.end_ts == end_ts
