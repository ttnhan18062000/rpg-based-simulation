"""Tests for tools/gate_checks/monitoring_integrity_backlog_check.py
(TCK-20260915-MONITORING-INTEGRITY-BACKLOG, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from monitoring_integrity_backlog_check import (  # noqa: E402
    NO_RUN_RECORD_CEILING,
    UNKNOWN_WEEK_ROW_CEILING,
    UNUSABLE_TS_EVENT_CEILING,
    UNUSABLE_TS_RUN_CEILING,
    check_monitoring_integrity_backlog,
    count_unknown_week_rows,
    find_unusable_ts_records,
    find_working_log_rows_missing_run_record,
)


# ---------------------------------------------------------------------------
# find_working_log_rows_missing_run_record (item 2)
# ---------------------------------------------------------------------------

def _write_working_log(tmp_path, rows):
    path = tmp_path / "working_log.csv"
    lines = ["timestamp,ticket_id,title,status,summary,artifacts_path"]
    lines.extend(rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_missing_run_record_detected_for_done_ticket_after_monitoring_start():
    tmp_rows = ["2026-07-01T00:00:00Z,TCK-MISSING,Title,DONE,Summary,none"]
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = _write_working_log(Path(d), tmp_rows)
        missing = find_working_log_rows_missing_run_record(run_ids=set(), working_log_path=path)
    assert missing == ["TCK-MISSING"]


def test_present_run_record_not_flagged():
    tmp_rows = ["2026-07-01T00:00:00Z,TCK-PRESENT,Title,DONE,Summary,none"]
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = _write_working_log(Path(d), tmp_rows)
        missing = find_working_log_rows_missing_run_record(run_ids={"TCK-PRESENT"}, working_log_path=path)
    assert missing == []


def test_pre_monitoring_start_ticket_not_flagged():
    tmp_rows = ["2026-06-01T00:00:00Z,TCK-OLD,Title,DONE,Summary,none"]
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = _write_working_log(Path(d), tmp_rows)
        missing = find_working_log_rows_missing_run_record(run_ids=set(), working_log_path=path)
    assert missing == []


def test_non_done_status_not_flagged():
    tmp_rows = ["2026-07-01T00:00:00Z,TCK-INPROGRESS,Title,INPROGRESS,Summary,none"]
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = _write_working_log(Path(d), tmp_rows)
        missing = find_working_log_rows_missing_run_record(run_ids=set(), working_log_path=path)
    assert missing == []


def test_malformed_row_skipped_not_misread():
    tmp_rows = ["2026-07-01T00:00:00Z,TCK-BAD,Title, with a comma,DONE,Summary,none"]
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = _write_working_log(Path(d), tmp_rows)
        missing = find_working_log_rows_missing_run_record(run_ids=set(), working_log_path=path)
    assert missing == []


def test_non_tck_prefixed_id_not_flagged():
    tmp_rows = ["2026-07-01T00:00:00Z,FOLDER-something,Title,DONE,Summary,none"]
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = _write_working_log(Path(d), tmp_rows)
        missing = find_working_log_rows_missing_run_record(run_ids=set(), working_log_path=path)
    assert missing == []


# ---------------------------------------------------------------------------
# find_unusable_ts_records (item 4)
# ---------------------------------------------------------------------------

def test_run_with_none_start_ts_flagged():
    runs = [{"run_id": "TCK-A", "start_ts": None}, {"run_id": "TCK-B", "start_ts": "2026-07-01T00:00:00Z"}]
    bad_runs, bad_events = find_unusable_ts_records(runs, [])
    assert bad_runs == ["TCK-A"]
    assert bad_events == []


def test_run_with_none_ts_fallback_field_flagged():
    runs = [{"run_id": "TCK-C", "ts": None}]
    bad_runs, _ = find_unusable_ts_records(runs, [])
    assert bad_runs == ["TCK-C"]


def test_event_with_none_ts_flagged():
    events = [{"run_id": "TCK-D", "ts": None}, {"run_id": "TCK-E", "ts": "2026-07-01T00:00:00Z"}]
    bad_runs, bad_events = find_unusable_ts_records([], events)
    assert bad_runs == []
    assert bad_events == ["TCK-D"]


# ---------------------------------------------------------------------------
# count_unknown_week_rows (item 5)
# ---------------------------------------------------------------------------

def test_unknown_week_row_count_sums_all_jsonl_files(tmp_path):
    unknown_week = tmp_path / "unknown-week"
    unknown_week.mkdir()
    (unknown_week / "runs.jsonl").write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")
    (unknown_week / "events.jsonl").write_text('{"b":1}\n', encoding="utf-8")
    assert count_unknown_week_rows(tmp_path) == 3


def test_unknown_week_missing_directory_returns_zero(tmp_path):
    assert count_unknown_week_rows(tmp_path) == 0


def test_unknown_week_blank_lines_not_counted(tmp_path):
    unknown_week = tmp_path / "unknown-week"
    unknown_week.mkdir()
    (unknown_week / "tools.jsonl").write_text('{"a":1}\n\n\n{"a":2}\n', encoding="utf-8")
    assert count_unknown_week_rows(tmp_path) == 2


# ---------------------------------------------------------------------------
# check_monitoring_integrity_backlog aggregate ratchet
# ---------------------------------------------------------------------------

def test_all_four_conditions_pass_when_within_ceiling(tmp_path):
    working_log_path = _write_working_log(tmp_path, [])
    results = check_monitoring_integrity_backlog(
        run_ids=set(), runs=[], events=[], working_log_path=working_log_path, data_dir=tmp_path,
    )
    assert len(results) == 4
    assert all(r["status"] == "PASS" for r in results)


def test_item2_condition_fails_when_missing_count_exceeds_ceiling(tmp_path):
    rows = [f"2026-07-01T00:00:00Z,TCK-{i},Title,DONE,Summary,none" for i in range(3)]
    working_log_path = _write_working_log(tmp_path, rows)
    results = check_monitoring_integrity_backlog(
        run_ids=set(), runs=[], events=[], working_log_path=working_log_path, data_dir=tmp_path,
        no_run_record_ceiling=2,
    )
    assert results[0]["status"] == "FAIL"
    assert "item 2" in results[0]["evidence"]


def test_item4_conditions_fail_independently_when_exceeded(tmp_path):
    working_log_path = _write_working_log(tmp_path, [])
    runs = [{"run_id": "TCK-A", "start_ts": None}, {"run_id": "TCK-B", "start_ts": None}]
    events = [{"run_id": "TCK-A", "ts": None}]
    results = check_monitoring_integrity_backlog(
        run_ids={"TCK-A", "TCK-B"}, runs=runs, events=events,
        working_log_path=working_log_path, data_dir=tmp_path,
        unusable_ts_run_ceiling=1, unusable_ts_event_ceiling=0,
    )
    assert results[1]["status"] == "FAIL"
    assert "item 4" in results[1]["evidence"]
    assert results[2]["status"] == "FAIL"


def test_item5_condition_fails_when_unknown_week_grows(tmp_path):
    working_log_path = _write_working_log(tmp_path, [])
    unknown_week = tmp_path / "unknown-week"
    unknown_week.mkdir()
    (unknown_week / "runs.jsonl").write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")
    results = check_monitoring_integrity_backlog(
        run_ids=set(), runs=[], events=[], working_log_path=working_log_path, data_dir=tmp_path,
        unknown_week_ceiling=1,
    )
    assert results[3]["status"] == "FAIL"
    assert "item 5" in results[3]["evidence"]


def test_ceilings_may_only_decrease_never_used_to_paper_over_a_regression():
    assert NO_RUN_RECORD_CEILING == 218, (
        "NO_RUN_RECORD_CEILING changed -- if this is because working_log/run-record coverage "
        "genuinely improved, lower this value to match (never raise it to paper over a regression)"
    )
    assert UNUSABLE_TS_RUN_CEILING == 66
    assert UNUSABLE_TS_EVENT_CEILING == 55
    assert UNKNOWN_WEEK_ROW_CEILING == 34


def test_real_corpus_is_at_or_below_all_four_ratchet_ceilings():
    results = check_monitoring_integrity_backlog()
    for r in results:
        assert r["status"] == "PASS", f"real corpus exceeded a ratchet ceiling: {r['evidence']}"


def test_makefile_wires_monitoring_integrity_backlog_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "monitoring-integrity-backlog-check:" in makefile_text
    assert "monitoring_integrity_backlog_check.py" in makefile_text
    assert "monitoring-integrity-backlog-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
