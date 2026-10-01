"""TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND: explicit week close, one section per acceptance criterion.
All fixtures live in tmp_path; nothing under the real agent-monitoring/data or tickets/ is touched."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

_TOOLS = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
sys.path.insert(0, str(_TOOLS))

import week_close as wc  # noqa: E402
import week_close_nudge as nudge  # noqa: E402

WEEK = "2026-W39"  # Mon 2026-09-21 .. Sun 2026-09-27
AFTER = date(2026, 9, 28)
DURING = date(2026, 9, 25)


def _w(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def _fixture(tmp_path, with_working_log=False):
    data = tmp_path / "agent-monitoring" / "data"
    wk = data / WEEK
    _w(wk / "runs.jsonl", [{"run_id": "A", "start_ts": "2026-09-22T10:00:00Z"}])
    _w(wk / "events.jsonl", [{"run_id": "A", "seq": 2, "ts": "2026-09-22T10:05:00Z"}])
    _w(wk / "tools.jsonl", [{"run_id": "A", "seq": 1, "ts": "2026-09-22T10:01:00Z"}])
    _w(wk / "b1.runs.jsonl", [{"run_id": "B", "start_ts": "2026-09-21T09:00:00Z"},
                              {"run_id": "A", "start_ts": "2026-09-22T10:00:00Z"}])  # one exact duplicate
    _w(wk / "b1.events.jsonl", [{"run_id": "B", "seq": 1, "ts": "2026-09-21T09:01:00Z"}])
    _w(wk / "b2.events.jsonl", [{"run_id": "A", "seq": 1, "ts": "2026-09-22T10:05:00Z"}])  # same ts, lower seq
    _w(wk / "b1.tools.jsonl", [{"run_id": "B", "seq": 1, "ts": "2026-09-21T09:02:00Z"}])
    if with_working_log:
        _w(wk / "b1.working_log.jsonl", [{"timestamp": "2026-09-21T09:00:00Z", "ticket_id": "TCK-X", "title": "t",
                                           "status": "DONE", "summary": "s", "artifacts_path": ""}])
        (tmp_path / "tickets").mkdir()
        (tmp_path / "tickets" / "working_log.csv").write_text(
            "timestamp,ticket_id,title,status,summary,artifacts_path\r\n", encoding="utf-8")
    return data


def _lines(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]


def _snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


# AC1
def test_close_leaves_exactly_three_canonical_files_and_second_run_changes_nothing(tmp_path):
    data = _fixture(tmp_path)
    wc.close_week(WEEK, data, AFTER)
    assert sorted(p.name for p in (data / WEEK).iterdir()) == ["events.jsonl", "runs.jsonl", "tools.jsonl"]
    first = _snapshot(tmp_path)
    again = wc.close_week(WEEK, data, AFTER)
    assert _snapshot(tmp_path) == first
    assert all(again[k]["shard_files"] == 0 and not again[k]["rewrote_canonical"] for k in ("runs", "events", "tools"))


# AC2
def test_closing_current_or_unfinished_week_refuses_and_touches_nothing(tmp_path):
    data = _fixture(tmp_path)
    before = _snapshot(tmp_path)
    with pytest.raises(wc.WeekCloseError, match="refusing to close"):
        wc.close_week(WEEK, data, DURING)
    assert _snapshot(tmp_path) == before
    for bad in ("2026-W99", "2026W39", ""):
        with pytest.raises(wc.WeekCloseError):
            wc.close_week(bad, data, AFTER)


def test_cli_refusal_exits_nonzero_without_touching_files(tmp_path):
    data = _fixture(tmp_path)
    before = _snapshot(tmp_path)
    proc = subprocess.run([sys.executable, str(_TOOLS / "week_close.py"), "--week", WEEK, "--data-dir", str(data),
                           "--today", "2026-09-25"], capture_output=True, text=True)
    assert proc.returncode == 2 and "REFUSED" in proc.stderr
    assert _snapshot(tmp_path) == before


# AC3
def test_rows_are_ordered_by_ts_then_seq_with_exact_duplicates_reported(tmp_path):
    data = _fixture(tmp_path)
    result = wc.close_week(WEEK, data, AFTER)
    runs = _lines(data / WEEK / "runs.jsonl")
    assert [r["run_id"] for r in runs] == ["B", "A"]  # 3 lines in, exact duplicate of A dropped
    assert result["runs"]["lines_in"] == 3 and result["runs"]["lines_out"] == 2 and result["runs"]["duplicates_dropped"] == 1
    events = _lines(data / WEEK / "events.jsonl")
    assert [(e["run_id"], e["seq"]) for e in events] == [("B", 1), ("A", 1), ("A", 2)]  # ts, then seq
    for kind in ("events", "tools"):
        assert result[kind]["duplicates_dropped"] == 0
        assert result[kind]["lines_in"] == result[kind]["lines_out"]


def test_unparseable_lines_sort_last_in_original_order(tmp_path):
    data = _fixture(tmp_path)
    (data / WEEK / "b9.tools.jsonl").write_text("not json\n", encoding="utf-8")
    wc.close_week(WEEK, data, AFTER)
    assert (data / WEEK / "tools.jsonl").read_text(encoding="utf-8").splitlines()[-1] == "not json"


def test_working_log_rows_land_once_in_the_csv_and_only_for_that_week(tmp_path):
    data = _fixture(tmp_path, with_working_log=True)
    other = data / "2026-W40"
    _w(other / "b3.working_log.jsonl", [{"timestamp": "2026-10-01T00:00:00Z", "ticket_id": "TCK-Y", "title": "t",
                                         "status": "DONE", "summary": "s", "artifacts_path": ""}])
    result = wc.close_week(WEEK, data, AFTER)
    csv_text = (tmp_path / "tickets" / "working_log.csv").read_text(encoding="utf-8")
    assert csv_text.count("TCK-X") == 1 and "TCK-Y" not in csv_text
    assert result["working_log"]["consolidated_rows"] == 1
    assert (other / "b3.working_log.jsonl").exists()  # another week's shard untouched
    wc.close_week(WEEK, data, AFTER)
    assert (tmp_path / "tickets" / "working_log.csv").read_text(encoding="utf-8").count("TCK-X") == 1


# AC4
def test_late_shard_is_folded_by_the_next_close(tmp_path):
    data = _fixture(tmp_path)
    wc.close_week(WEEK, data, AFTER)
    _w(data / WEEK / "late.runs.jsonl", [{"run_id": "LATE", "start_ts": "2026-09-23T00:00:00Z"}])
    result = wc.close_week(WEEK, data, date(2026, 10, 12))
    assert result["runs"]["shard_files"] == 1
    assert [r["run_id"] for r in _lines(data / WEEK / "runs.jsonl")] == ["B", "A", "LATE"]
    assert not (data / WEEK / "late.runs.jsonl").exists()


def test_crash_between_replace_and_delete_is_healed_by_exact_dedup(tmp_path):
    data = _fixture(tmp_path)
    wc.close_week(WEEK, data, AFTER)
    canonical = _lines(data / WEEK / "runs.jsonl")
    # simulate: canonical already contains the shard's rows but the shard was never deleted
    _w(data / WEEK / "b1.runs.jsonl", [{"run_id": "B", "start_ts": "2026-09-21T09:00:00Z"}])
    wc.close_week(WEEK, data, AFTER)
    assert _lines(data / WEEK / "runs.jsonl") == canonical


# AC5
def test_nudge_fires_for_finished_week_with_shards_and_is_silent_otherwise(tmp_path):
    data = _fixture(tmp_path)
    assert nudge.weeks_needing_close(data, DURING) == []  # week not finished
    pending = nudge.weeks_needing_close(data, AFTER)
    assert pending and pending[0][0] == WEEK and pending[0][1] == 4
    assert "make agent-monitoring-close-week" in nudge.nudge_message(pending)
    wc.close_week(WEEK, data, AFTER)
    assert nudge.weeks_needing_close(data, AFTER) == []
    assert nudge.nudge_message([]) is None
    (data / "not-a-week").mkdir()
    (data / "not-a-week" / "x.runs.jsonl").write_text("{}\n", encoding="utf-8")
    assert nudge.weeks_needing_close(data, AFTER) == []  # non-ISO directories are ignored


def test_retro_nudge_hook_also_emits_the_close_week_nudge_even_below_the_retro_threshold(tmp_path):
    data = tmp_path / "agent-monitoring" / "data"
    _w(data / "2026-W01" / "b1.runs.jsonl", [{"run_id": "A"}])  # long finished, still has a shard
    proc = subprocess.run([sys.executable, str(_TOOLS / "retro_nudge_hook.py")], input=json.dumps({"session_id": "s1"}),
                          capture_output=True, text=True, cwd=tmp_path)
    assert proc.returncode == 0
    ctx = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "agent-monitoring-close-week" in ctx and "2026-W01" in ctx
