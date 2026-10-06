"""tools/agent-monitoring/hand_closure_time.py and its use by record_hand_orchestrated_closure.py
(TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS; design: stored_artifacts/TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN/design.md).

Unit tests over plain lists, plus the real CLI in a scratch git repo with seeded `tools.jsonl` rows."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.agent_working_paths import AGENT_MONITORING

_TOOLS = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import hand_closure_time as hct  # noqa: E402
import record_events  # noqa: E402
import record_run  # noqa: E402

SID = "sess-1"
BASE = datetime(2026, 10, 6, 8, 0, 0, tzinfo=timezone.utc)


def _iso(minutes: float) -> str:
    return (BASE + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _rows(*minutes, sid=SID, run_id=None):
    return [{"session_id": sid, "run_id": run_id, "ts": _iso(m), "tool": "Bash"} for m in minutes]


# ---- resolve -----------------------------------------------------------------------------------

def test_declared_start_wins_and_ignores_evidence():
    res = hct.resolve(_iso(60), _iso(10), None, SID, _rows(30, 31, 32, 33), [])
    assert (res.duration_source, res.start_ts, res.end_ts) == ("declared", _iso(10), _iso(60))


def test_no_evidence_is_unknown_with_start_equal_end():
    res = hct.resolve(_iso(60), None, None, SID, [], [])
    assert (res.duration_source, res.start_ts, res.end_ts) == ("unknown", _iso(60), _iso(60))


def test_fewer_than_three_claimable_rows_is_unknown():
    assert hct.resolve(_iso(60), None, None, SID, _rows(50, 55), []).duration_source == "unknown"


def test_five_rows_derive_the_start_from_the_first_row():
    res = hct.resolve(_iso(60), None, None, SID, _rows(40, 41, 45, 50, 55), [])
    assert (res.duration_source, res.start_ts, res.claim_peers) == ("tool_activity", _iso(40), 0)
    assert len(res.claimed) == 5


def test_a_declared_end_alone_bounds_the_derivation():
    res = hct.resolve(_iso(120), None, _iso(60), SID, _rows(40, 45, 50, 100, 110), [])
    assert (res.duration_source, res.start_ts, res.end_ts) == ("tool_activity", _iso(40), _iso(60))


def test_an_idle_gap_over_the_pause_threshold_starts_a_new_block():
    res = hct.resolve(_iso(200), None, None, SID, _rows(10, 11, 12, 150, 160, 170, 190), [])
    assert res.start_ts == _iso(150) and len(res.claimed) == 4


def test_rows_after_the_previous_closure_belong_to_this_one_and_peers_are_counted():
    rows = _rows(10, 20, 30, 40, 50, 55, 58)
    res = hct.resolve(_iso(60), None, None, SID, rows, [_iso(35)])
    assert [r["ts"] for r in res.claimed] == [_iso(40), _iso(50), _iso(55), _iso(58)] and res.claim_peers == 1


def test_two_closures_in_one_block_never_claim_the_same_row():
    rows = _rows(10, 20, 30, 40, 50, 55, 58)
    first = hct.resolve(_iso(35), None, None, SID, rows, [])
    second = hct.resolve(_iso(60), None, None, SID, rows, [_iso(35)])
    ts = [r["ts"] for r in first.claimed] + [r["ts"] for r in second.claimed]
    assert len(ts) == len(set(ts)) == 7


def test_a_later_closure_with_nothing_new_is_unknown():
    assert hct.resolve(_iso(60), None, None, SID, _rows(10, 20, 30), [_iso(31)]).duration_source == "unknown"


# ---- the readers --------------------------------------------------------------------------------

def _write(path: Path, rows: list[dict], junk: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows) + ("not json\n" if junk else ""))


def test_session_tool_rows_ignore_other_sessions_and_sidecar_attributed_rows(tmp_path):
    week = tmp_path / "2026-W41"
    _write(week / "tools.jsonl", _rows(1, 2) + _rows(3, sid="other") + _rows(4, run_id="TCK-X"))
    _write(week / "branch.tools.jsonl", _rows(5))
    assert [r["ts"] for r in hct.session_tool_rows(SID, tmp_path)] == [_iso(1), _iso(2), _iso(5)]
    assert hct.session_tool_rows("", tmp_path) == []


def test_prior_closure_ends_use_only_hand_runs_of_this_session_before_the_end(tmp_path):
    runs = [{"execution_mode": "hand", "session_id": SID, "end_ts": _iso(10)},
            {"execution_mode": "hand", "session_id": SID, "end_ts": _iso(90)},
            {"execution_mode": "hand", "session_id": "other", "end_ts": _iso(20)},
            {"execution_mode": "pipeline", "session_id": SID, "end_ts": _iso(30)},
            {"execution_mode": "hand", "end_ts": _iso(40)}]
    _write(tmp_path / "2026-W41" / "b.runs.jsonl", runs)
    assert hct.prior_closure_ends(SID, tmp_path, _iso(60)) == [_iso(10)]


def test_a_read_failure_is_unknown_not_an_error(tmp_path):
    res = hct.resolve_for_session(_iso(60), None, None, SID, tmp_path / "does-not-exist")
    assert res.duration_source == "unknown" and res.start_ts == res.end_ts == _iso(60)


# ---- validators ---------------------------------------------------------------------------------

def test_old_rows_without_the_new_fields_stay_valid():
    run = {"run_id": "r", "start_ts": _iso(0), "workflow": "implement-ticket", "tier": "hotfix", "final_status": "DONE", "agent_count": 1}
    assert record_run.validate_record(run) == []
    assert record_run.validate_record({**run, "duration_source": "tool_activity", "session_id": None, "claim_peers": 0}) == []


@pytest.mark.parametrize("extra", [{"duration_source": "guessed"}, {"session_id": 5}, {"claim_peers": -1}, {"claim_peers": True}])
def test_bad_provenance_fields_are_rejected(extra):
    run = {"run_id": "r", "start_ts": _iso(0), "workflow": "implement-ticket", "tier": "hotfix", "final_status": "DONE", "agent_count": 1}
    assert record_run.validate_record({**run, **extra})


# ---- the CLI ------------------------------------------------------------------------------------

_RECORD = _TOOLS / "record_hand_orchestrated_closure.py"
_EVENTS = json.dumps([{"phase": "Scope", "status": "ok", "summary": "s"}, {"phase": "Implement", "status": "ok", "summary": "i"}])
_TITLE = ["--title", "T", "--log-summary", "S"]


def _repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "test-branch", str(path)], check=True)


def _run(tmp_path: Path, *args, session: str | None = SID):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
    if session:
        env["CLAUDE_CODE_SESSION_ID"] = session
    return subprocess.run([sys.executable, str(_RECORD), "--ticket-id", "TCK-FAKE-TIME", "--tier", "hotfix", "--events", _EVENTS, *_TITLE, *args],
                          capture_output=True, text=True, cwd=tmp_path, env=env)


def _records(tmp_path: Path):
    week = datetime.now(timezone.utc).strftime("%G-W%V")
    base = tmp_path / AGENT_MONITORING / "data" / week
    run = json.loads((base / "test-branch.runs.jsonl").read_text().strip().splitlines()[-1])
    events = [json.loads(l) for l in (base / "test-branch.events.jsonl").read_text().splitlines()]
    return run, events


def _seed_recent(tmp_path: Path, minutes_ago: list[float], sid=SID) -> None:
    now = datetime.now(timezone.utc)
    rows = [{"session_id": sid, "run_id": None, "ts": (now - timedelta(minutes=m)).isoformat().replace("+00:00", "Z"), "tool": "Bash"} for m in minutes_ago]
    week = now.strftime("%G-W%V")
    _write(tmp_path / AGENT_MONITORING / "data" / week / "seed.tools.jsonl", rows, junk=False)


def test_cli_with_no_evidence_records_unknown_and_null_duration(tmp_path):
    _repo(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    run, events = _records(tmp_path)
    assert run["duration_source"] == "unknown" and run["duration_s"] is None and run["start_ts"] == run["end_ts"]
    assert run["session_id"] == SID and all(e["session_id"] == SID for e in events)
    assert record_run.validate_record(run) == [] and all(record_events.validate_record(e) == [] for e in events)


def test_cli_with_the_session_s_tool_rows_records_tool_activity(tmp_path):
    _repo(tmp_path)
    _seed_recent(tmp_path, [30, 25, 20, 10, 5])
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    run, _ = _records(tmp_path)
    assert run["duration_source"] == "tool_activity" and run["claim_peers"] == 0
    assert 29 * 60 <= run["duration_s"] <= 31 * 60


def test_cli_ignores_another_sessions_rows(tmp_path):
    _repo(tmp_path)
    _seed_recent(tmp_path, [30, 25, 20, 10, 5], sid="someone-else")
    run, _ = (_run(tmp_path), _records(tmp_path))[1]
    assert run["duration_source"] == "unknown"


def test_cli_declared_start_records_declared_and_the_measured_duration(tmp_path):
    _repo(tmp_path)
    start = (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat().replace("+00:00", "Z")
    assert _run(tmp_path, "--start-ts", start).returncode == 0
    run, _ = _records(tmp_path)
    assert run["duration_source"] == "declared" and 44 * 60 <= run["duration_s"] <= 46 * 60


def test_cli_an_inverted_declared_span_is_never_a_duration(tmp_path):
    _repo(tmp_path)
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    assert _run(tmp_path, "--start-ts", future).returncode == 0
    run, _ = _records(tmp_path)
    assert run["duration_s"] is None and run["duration_source"] == "unknown"


def test_cli_without_a_session_id_records_a_null_session_and_unknown(tmp_path):
    _repo(tmp_path)
    assert _run(tmp_path, session=None).returncode == 0
    run, _ = _records(tmp_path)
    assert run["session_id"] is None and run["duration_source"] == "unknown"


# ---- readers of the run rows: old rows, and the new unknown rows -----------------------------------

def _run_row(**extra):
    return {"run_id": "TCK-A", "ticket_id": "TCK-A", "start_ts": _iso(0), "end_ts": _iso(0), "workflow": "implement-ticket", "tier": "hotfix",
            "final_status": "DONE", "agent_count": 1, "execution_mode": "hand", "duration_s": 0, **extra}


def test_generate_retro_loads_old_rows_and_rows_with_the_new_fields():
    import generate_retro

    old = _run_row()
    unknown = _run_row(run_id="TCK-B", ticket_id="TCK-B", duration_s=None, duration_source="unknown", session_id=None)
    derived = _run_row(run_id="TCK-C", ticket_id="TCK-C", end_ts=_iso(30), duration_s=1800, duration_source="tool_activity", session_id=SID, claim_peers=0)
    text = generate_retro.generate([old, unknown, derived], [], "W")
    assert "Run Summary" in text


def test_the_integrity_report_checks_still_load_rows_with_the_new_fields():
    sys.path.insert(0, str(_TOOLS.parent / "gate_checks"))
    from duplicate_run_record_check import check_duplicate_run_records

    rows = [_run_row(duration_s=None, duration_source="unknown", session_id=SID), _run_row(run_id="TCK-D", ticket_id="TCK-D")]
    assert all(r["status"] == "PASS" for r in check_duplicate_run_records(runs=rows))
