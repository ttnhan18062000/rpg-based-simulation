"""TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG: the dispatch/skip decision."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tools.test_architecture.slow_regression_watchdog import DISPATCH, SKIP, decide, main

NOW = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)


def _run(age: timedelta, *, status="completed", event="schedule", branch="main", run_id=1):
    return {
        "databaseId": run_id,
        "event": event,
        "status": status,
        "headBranch": branch,
        "createdAt": (NOW - age).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def test_no_runs_dispatches():
    assert decide([], NOW)[0] == DISPATCH


def test_just_under_ten_hours_skips():
    assert decide([_run(timedelta(hours=9, minutes=59))], NOW)[0] == SKIP


def test_just_over_ten_hours_dispatches():
    assert decide([_run(timedelta(hours=10, minutes=1))], NOW)[0] == DISPATCH


def test_exactly_ten_hours_dispatches():
    assert decide([_run(timedelta(hours=10))], NOW)[0] == DISPATCH


@pytest.mark.parametrize("status", ["queued", "in_progress", "waiting"])
def test_active_run_skips_whatever_its_age(status):
    assert decide([_run(timedelta(hours=30), status=status)], NOW)[0] == SKIP


def test_active_run_skips_even_when_a_newer_completed_run_exists():
    runs = [_run(timedelta(hours=30), status="in_progress", run_id=1), _run(timedelta(hours=20), run_id=2)]
    assert decide(runs, NOW)[0] == SKIP


def test_manual_dispatch_run_counts_as_newest():
    runs = [_run(timedelta(hours=14), run_id=1), _run(timedelta(hours=2), event="workflow_dispatch", run_id=2)]
    assert decide(runs, NOW)[0] == SKIP


def test_newest_is_chosen_by_time_not_list_order():
    runs = [_run(timedelta(hours=2), run_id=2), _run(timedelta(hours=14), run_id=1)]
    assert decide(runs, NOW)[0] == SKIP


def test_other_branches_are_ignored():
    runs = [_run(timedelta(hours=1), branch="feature"), _run(timedelta(hours=1), status="in_progress", branch="x")]
    assert decide(runs, NOW)[0] == DISPATCH


def test_failed_run_still_counts_as_a_run():
    run = _run(timedelta(hours=3))
    run["conclusion"] = "failure"
    assert decide([run], NOW)[0] == SKIP


def test_budget_as_designed_schedule_never_dispatches():
    # A 6 h gap and a slot running 3.5 h late (9.5 h since the previous run) both skip.
    assert decide([_run(timedelta(hours=6))], NOW)[0] == SKIP
    assert decide([_run(timedelta(hours=9, minutes=30))], NOW)[0] == SKIP


@pytest.mark.parametrize("bad", [None, "", "not-a-time", "2026-10-08T05:00:00"])
def test_malformed_or_missing_timestamp_fails_loud(bad):
    run = _run(timedelta(hours=20))
    if bad is None:
        del run["createdAt"]
    else:
        run["createdAt"] = bad
    with pytest.raises(ValueError):
        decide([run], NOW)


def test_malformed_timestamp_fails_even_when_an_active_run_would_skip():
    runs = [_run(timedelta(hours=1), status="in_progress"), {**_run(timedelta(hours=1), run_id=2), "createdAt": "x"}]
    with pytest.raises(ValueError):
        decide(runs, NOW)


def test_naive_now_is_rejected():
    with pytest.raises(ValueError):
        decide([], datetime(2026, 10, 8, 12, 0))


def test_cli_prints_decision_and_reason(tmp_path, capsys):
    path = tmp_path / "runs.json"
    path.write_text('[{"databaseId": 7, "event": "schedule", "status": "completed", '
                    '"headBranch": "main", "createdAt": "2026-10-08T00:00:00Z"}]')
    assert main([str(path), "--now", "2026-10-08T12:00:00Z"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "decision=dispatch"
    assert out[1].startswith("reason=newest run 7")


# --- TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN: no dispatch for a head that was tested recently ---

HEAD = "c" * 40


def _tested_run(age, *, tested=True, event="schedule", run_id=1, sha=HEAD):
    run = _run(age, event=event, run_id=run_id)
    run["headSha"] = sha
    run["tested"] = tested
    return run


def test_stale_schedule_but_head_tested_under_a_day_ago_does_not_dispatch():
    # newest run is 11 h old (over the 10 h staleness bar) and tested the head: the gate would skip a new run.
    decision, reason = decide([_tested_run(timedelta(hours=11))], NOW, head_sha=HEAD)
    assert decision == SKIP
    assert "tested" in reason


def test_stale_schedule_and_head_tested_over_a_day_ago_dispatches():
    assert decide([_tested_run(timedelta(hours=25))], NOW, head_sha=HEAD)[0] == DISPATCH


def test_head_untested_still_dispatches_when_stale():
    assert decide([_tested_run(timedelta(hours=11), sha="d" * 40)], NOW, head_sha=HEAD)[0] == DISPATCH


def test_gate_skipped_newest_run_counts_as_the_slot_firing_but_not_as_coverage():
    # A tested run 30 h ago, then a gate-skipped scheduled run 3 h ago: the slot fired (staleness skips) ...
    runs = [_tested_run(timedelta(hours=30), run_id=1), _tested_run(timedelta(hours=3), tested=False, run_id=2)]
    assert decide(runs, NOW, head_sha=HEAD)[0] == SKIP
    # ... and 11 h after a gate-skipped run the staleness bar is crossed, but only a skipped run is at hand, so the
    # head is not covered and a dispatch is allowed.
    runs = [_tested_run(timedelta(hours=11), tested=False, run_id=2)]
    assert decide(runs, NOW, head_sha=HEAD)[0] == DISPATCH


def test_without_head_sha_the_behaviour_is_unchanged():
    assert decide([_tested_run(timedelta(hours=11))], NOW)[0] == DISPATCH


def test_cli_head_sha_flag_applies_the_tested_head_rule(tmp_path, capsys):
    path = tmp_path / "runs.json"
    path.write_text(__import__("json").dumps([_tested_run(timedelta(hours=11))]))
    assert main([str(path), "--now", "2026-10-08T12:00:00Z", "--head-sha", HEAD]) == 0
    assert "decision=skip" in capsys.readouterr().out
