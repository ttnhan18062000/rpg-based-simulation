"""TCK-20261021-HAND-CLOSURE-DURATION-FROM-LAST-ACTIVITY-AND-WEEK-CLOSE-REDERIVE, part 2: a week close re-derives the `unknown`
durations of that week's hand closures from the tool rows present now. All fixtures live in tmp_path."""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_TOOLS = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(_TOOLS.parent))

import week_close as wc  # noqa: E402
from gate_checks.duplicate_run_record_check import check_duplicate_run_records  # noqa: E402
from run_dedup import dedupe_to_latest_per_execution  # noqa: E402

WEEK, PREV = "2026-W39", "2026-W38"  # Mon 2026-09-21 .. Sun 2026-09-27
AFTER = date(2026, 9, 28)
SID = "sess-1"
BASE = datetime(2026, 9, 22, 8, 0, 0, tzinfo=timezone.utc)


def _iso(minutes):
    return (BASE + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _tool_rows(*minutes, sid=SID, run_id=None):
    return [{"session_id": sid, "run_id": run_id, "ts": _iso(m), "tool": "Bash"} for m in minutes]


def _unknown(run_id="A", exec_id="e1", closure=300, sid=SID, **extra):
    return {"run_id": run_id, "execution_id": exec_id, "start_ts": _iso(closure), "end_ts": _iso(closure), "duration_s": None,
            "duration_source": "unknown", "execution_mode": "hand", "session_id": sid, "final_status": "DONE",
            "workflow": "implement-ticket", "tier": "hotfix", "agent_count": None, **extra}


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8")


def _runs(data, week=WEEK):
    return [json.loads(x) for x in (data / week / "runs.jsonl").read_text(encoding="utf-8").splitlines()]


def _close(data):
    return wc.close_week(WEEK, data, AFTER, main_checkout=None)


def test_an_unknown_closure_after_a_pause_is_rederived_from_the_last_block_and_marked(tmp_path):
    data = tmp_path / "data"
    _write(data / WEEK / "runs.jsonl", [_unknown(closure=300)])
    _write(data / WEEK / "tools.jsonl", _tool_rows(40, 41, 45, 50, 55))
    result = _close(data)
    assert result["durations"]["rederived"] == 1
    (run,) = _runs(data)
    assert (run["duration_source"], run["start_ts"], run["end_ts"], run["closed_ts"]) == ("tool_activity", _iso(40), _iso(55), _iso(300))
    assert run["duration_s"] == 15 * 60 and run["duration_rederived"] == "week_close" and run["claim_peers"] == 0


def test_a_second_close_changes_nothing(tmp_path):
    data = tmp_path / "data"
    _write(data / WEEK / "runs.jsonl", [_unknown(closure=300)])
    _write(data / WEEK / "tools.jsonl", _tool_rows(40, 41, 45, 50, 55))
    _close(data)
    first = (data / WEEK / "runs.jsonl").read_bytes()
    again = _close(data)
    assert again["durations"] == {"rederived": 0, "stale_dropped": 0, "skipped": None}
    assert (data / WEEK / "runs.jsonl").read_bytes() == first


def test_too_few_rows_leave_the_row_unknown_and_the_file_untouched(tmp_path):
    data = tmp_path / "data"
    _write(data / WEEK / "runs.jsonl", [_unknown(closure=300)])
    _write(data / WEEK / "tools.jsonl", _tool_rows(50, 55))
    before = (data / WEEK / "runs.jsonl").read_bytes()
    assert _close(data)["durations"]["rederived"] == 0
    assert (data / WEEK / "runs.jsonl").read_bytes() == before


def test_late_rows_folded_by_this_close_are_used_and_the_previous_week_counts(tmp_path):
    data = tmp_path / "data"
    _write(data / WEEK / "runs.jsonl", [_unknown(closure=300)])
    _write(data / WEEK / "late-branch.tools.jsonl", _tool_rows(-30, -20))  # before the week starts: found in the previous week folder
    _write(data / PREV / "tools.jsonl", _tool_rows(-60))
    _write(data / WEEK / "tools.jsonl", _tool_rows(40, 41))
    # the previous-week rows are 100 minutes before the week block: not contiguous, so the block is only the last two rows
    assert _close(data)["durations"]["rederived"] == 0
    _write(data / WEEK / "another-late.tools.jsonl", _tool_rows(45))
    assert _close(data)["durations"]["rederived"] == 1  # a late shard folded by the re-close completes the block


def test_declared_and_tool_activity_rows_and_other_sessions_rows_are_untouched(tmp_path):
    data = tmp_path / "data"
    declared = _unknown(run_id="D", exec_id="d1", duration_source="declared", start_ts=_iso(1), end_ts=_iso(299), duration_s=17880)
    derived = _unknown(run_id="T", exec_id="t1", duration_source="tool_activity", start_ts=_iso(40), end_ts=_iso(55), duration_s=900)
    other = _unknown(run_id="O", exec_id="o1", sid="someone-else", closure=300)
    _write(data / WEEK / "runs.jsonl", [declared, derived, other])
    _write(data / WEEK / "tools.jsonl", _tool_rows(40, 41, 45, 50, 55))  # SID's rows only
    before = (data / WEEK / "runs.jsonl").read_bytes()
    assert _close(data)["durations"]["rederived"] == 0
    assert (data / WEEK / "runs.jsonl").read_bytes() == before


def test_a_non_hand_unknown_row_is_never_rederived(tmp_path):
    data = tmp_path / "data"
    _write(data / WEEK / "runs.jsonl", [_unknown(execution_mode="pipeline")])
    _write(data / WEEK / "tools.jsonl", _tool_rows(40, 41, 45, 50, 55))
    assert _close(data)["durations"]["rederived"] == 0


def test_a_later_closure_of_the_session_claims_only_after_the_rederived_end(tmp_path):
    data = tmp_path / "data"
    _write(data / WEEK / "runs.jsonl", [_unknown(run_id="A", exec_id="e1", closure=100), _unknown(run_id="B", exec_id="e2", closure=400)])
    _write(data / WEEK / "tools.jsonl", _tool_rows(10, 11, 12, 13, 300, 301, 302))
    assert _close(data)["durations"]["rederived"] == 2
    first, second = _runs(data)
    assert (first["start_ts"], first["end_ts"]) == (_iso(10), _iso(13)) and (second["start_ts"], second["end_ts"]) == (_iso(300), _iso(302))


def test_a_re_close_with_a_late_shard_holding_the_old_unknown_row_still_has_one_run(tmp_path):
    data = tmp_path / "data"
    old = _unknown(closure=300)
    _write(data / WEEK / "runs.jsonl", [old])
    _write(data / WEEK / "tools.jsonl", _tool_rows(40, 41, 45, 50, 55))
    _close(data)
    unrelated = _unknown(run_id="Z", exec_id="z1", closure=310, sid="nobody")
    _write(data / WEEK / "late.runs.jsonl", [old, unrelated])  # a branch merging late still carries the old unknown row
    result = _close(data)
    rows = _runs(data)
    assert result["durations"]["stale_dropped"] == 1
    assert sorted(r["run_id"] for r in rows) == ["A", "Z"]  # one A (the re-derived one); the unrelated unknown row is kept
    assert next(r for r in rows if r["run_id"] == "A")["duration_rederived"] == "week_close"
    assert len(dedupe_to_latest_per_execution(rows)) == 2
    assert check_duplicate_run_records(rows, ceiling=0)[0]["status"] == "PASS"


def test_the_cli_prints_one_line_with_the_counts(tmp_path, capsys):
    data = tmp_path / "data"
    _write(data / WEEK / "runs.jsonl", [_unknown(closure=300)])
    _write(data / WEEK / "tools.jsonl", _tool_rows(40, 41, 45, 50, 55))
    assert wc.main(["--week", WEEK, "--data-dir", str(data), "--today", AFTER.isoformat()]) == 0
    assert f"{WEEK} hand-closure durations: re-derived 1 unknown, dropped 0 stale" in capsys.readouterr().out
