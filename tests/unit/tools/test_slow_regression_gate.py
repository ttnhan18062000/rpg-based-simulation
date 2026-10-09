"""TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN: the gate's run/skip decision and what counts as tested."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tools.test_architecture import slow_regression_gate as gate
from tools.test_architecture.slow_regression_gate import RUN, SKIP, actually_tested, collect, decide

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
HEAD = "a" * 40
OTHER = "b" * 40


def _run(age: timedelta, *, tested=True, sha=HEAD, status="completed", run_id=1, branch="main"):
    return {
        "databaseId": run_id,
        "event": "schedule",
        "status": status,
        "headBranch": branch,
        "headSha": sha,
        "tested": tested,
        "createdAt": (NOW - age).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def test_no_runs_at_all_runs():
    assert decide(HEAD, [], NOW)[0] == RUN


def test_head_never_tested_runs_even_when_other_commits_were():
    assert decide(HEAD, [_run(timedelta(hours=1), sha=OTHER)], NOW)[0] == RUN


def test_head_tested_two_hours_ago_skips():
    decision, reason = decide(HEAD, [_run(timedelta(hours=2))], NOW)
    assert decision == SKIP
    assert "run 1" in reason and "2.00 h ago" in reason


def test_head_tested_just_under_a_day_ago_skips():
    assert decide(HEAD, [_run(timedelta(hours=23, minutes=59))], NOW)[0] == SKIP


def test_head_tested_exactly_a_day_ago_runs_the_daily_rerun():
    assert decide(HEAD, [_run(timedelta(hours=24))], NOW)[0] == RUN


def test_head_tested_25_hours_ago_runs():
    assert decide(HEAD, [_run(timedelta(hours=25))], NOW)[0] == RUN


def test_only_gate_skipped_runs_at_head_do_not_count_as_coverage():
    runs = [_run(timedelta(hours=1), tested=False, run_id=1), _run(timedelta(hours=7), tested=False, run_id=2)]
    assert decide(HEAD, runs, NOW)[0] == RUN


def test_a_gate_skipped_run_newer_than_the_tested_one_does_not_reset_the_clock():
    runs = [_run(timedelta(hours=25), tested=True, run_id=1), _run(timedelta(hours=1), tested=False, run_id=2)]
    assert decide(HEAD, runs, NOW)[0] == RUN


def test_an_in_progress_run_at_head_is_not_a_completed_test():
    assert decide(HEAD, [_run(timedelta(hours=1), status="in_progress", tested=False)], NOW)[0] == RUN


def test_an_in_progress_run_flagged_tested_is_still_not_counted():
    assert decide(HEAD, [_run(timedelta(hours=1), status="in_progress", tested=True)], NOW)[0] == RUN


def test_the_callers_own_run_is_excluded():
    runs = [_run(timedelta(minutes=1), run_id=99)]
    assert decide(HEAD, runs, NOW, exclude_run_id=99)[0] == RUN
    assert decide(HEAD, runs, NOW)[0] == SKIP


def test_the_newest_tested_run_decides():
    runs = [_run(timedelta(hours=30), run_id=1), _run(timedelta(hours=3), run_id=2)]
    assert decide(HEAD, runs, NOW)[0] == SKIP


def test_runs_on_other_branches_are_ignored():
    assert decide(HEAD, [_run(timedelta(hours=1), branch="feature")], NOW)[0] == RUN


@pytest.mark.parametrize("created", [None, "", "not-a-time", "2026-10-09T10:00:00"])
def test_malformed_timestamp_raises(created):
    run = _run(timedelta(hours=1))
    run["createdAt"] = created
    with pytest.raises(ValueError):
        decide(HEAD, [run], NOW)


def test_naive_now_and_missing_head_raise():
    with pytest.raises(ValueError):
        decide(HEAD, [], datetime(2026, 10, 9, 12, 0))
    with pytest.raises(ValueError):
        decide("", [], NOW)


@pytest.mark.parametrize(
    ("status", "conclusion", "expected"),
    [
        ("completed", "success", True),
        ("completed", "failure", True),
        ("completed", "skipped", False),
        ("completed", "cancelled", False),
        ("in_progress", None, False),
    ],
)
def test_actually_tested_reads_the_suite_job_conclusion(status, conclusion, expected):
    jobs = [{"name": "Gate: skip if main was tested recently", "conclusion": "success"}, {"name": gate.SUITE_JOB_NAME, "conclusion": conclusion}]
    assert actually_tested({"status": status}, jobs) is expected


def test_a_run_with_no_suite_job_is_not_tested():
    assert actually_tested({"status": "completed"}, [{"name": "Gate: skip if main was tested recently", "conclusion": "success"}]) is False


def test_collect_fetches_jobs_only_for_completed_runs_at_head_and_flags_tested():
    listed = [
        {"databaseId": 1, "headSha": HEAD, "status": "completed", "createdAt": "x"},
        {"databaseId": 2, "headSha": HEAD, "status": "completed", "createdAt": "x"},
        {"databaseId": 3, "headSha": HEAD, "status": "in_progress", "createdAt": "x"},
        {"databaseId": 4, "headSha": OTHER, "status": "completed", "createdAt": "x"},
    ]
    seen = []
    conclusions = {1: "success", 2: "skipped"}

    def view_jobs(run_id):
        seen.append(run_id)
        return [{"name": gate.SUITE_JOB_NAME, "conclusion": conclusions[run_id]}]

    out = collect(HEAD, list_runs=lambda: listed, view_jobs=view_jobs)
    assert seen == [1, 2]
    assert [r["tested"] for r in out] == [True, False, False, False]


def test_cli_decide_prints_decision_and_reason(monkeypatch, capsys):
    runs = [_run(timedelta(hours=2))]
    monkeypatch.setattr(gate, "collect", lambda head: runs)
    assert gate.main(["decide", "--head-sha", HEAD, "--now", "2026-10-09T12:00:00Z"]) == 0
    out = capsys.readouterr().out
    assert "decision=skip" in out and "reason=" in out
