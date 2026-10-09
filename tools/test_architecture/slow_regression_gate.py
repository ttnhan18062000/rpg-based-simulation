"""Decide whether a scheduled Slow regression run should test main, or skip because main was tested recently.

TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN. The suite costs about 2 runner-hours a run and the
schedule fires 4 times a day, so a scheduled slot on a commit that was already tested is wasted money. Two
consecutive runs on 2026-10-08/09 tested the same commit, though, and exactly those two exposed that the failing set
flaps on an unchanged commit (rolling issue #390), so one same-commit rerun a day is kept on purpose.

The rule, for main's head SHA ``H`` (the slow suite covers all of ``src/``, so nothing but ``H`` is looked at):

* ``run`` if no completed run that *actually tested* ``H`` exists;
* ``run`` if the newest such run was created 24 h ago or more;
* otherwise ``skip``.

"Actually tested" (the choice this module records): the run is ``completed`` and its job named ``Slow regression`` (the
suite job in ``slow-regression.yml``) concluded ``success`` or ``failure``. A run whose gate decided ``skip`` has that job
concluded ``skipped``, so it never counts as coverage; the gate does not count its own skips. A cancelled run (job
``cancelled``) did not finish testing and does not count either. A ``failure`` counts even when it is a setup-stage
failure (checkout or dependency install) rather than a test failure: the gate cannot tell them apart from the job
conclusion, and it errs toward the one same-commit rerun a day rather than a rerun of every failed setup. The job conclusions come from the jobs API (one call per
run at ``H``), because the run-level conclusion is ``success`` for a gate-skipped run and cannot tell the two apart.

Runs that are not completed (queued, in progress) never count as tested. The caller's own run is passed as
``exclude_run_id`` so the gate does not look at itself; the workflow's non-cancelling concurrency group means no other
run is in flight while the gate runs.

``workflow_dispatch`` never goes through this rule: a human asked for the run, or the watchdog already decided. The
watchdog (``slow_regression_watchdog.py``) applies the same rule before it dispatches, so it does not dispatch for a head
that was tested less than 24 h ago.

Malformed input raises ``ValueError``: a silent ``run`` on bad data would spend ~2 runner-hours per slot.

CLI (stdlib only; shells out to ``gh``)::

    python -m tools.test_architecture.slow_regression_gate decide --head-sha SHA [--exclude-run-id ID] [--now ISO]
    python -m tools.test_architecture.slow_regression_gate collect --head-sha SHA   # runs.json with ``tested`` per run

``decide`` prints ``decision=<run|skip>`` and ``reason=<one line>``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping

MAIN_BRANCH = "main"
SUITE_JOB_NAME = "Slow regression"
TESTED_CONCLUSIONS = frozenset({"success", "failure"})
RERUN_AFTER = timedelta(hours=24)

RUN = "run"
SKIP = "skip"


def _parse_time(value: Any, *, run: Mapping[str, Any]) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"run {run.get('databaseId')!r} has no createdAt timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"run {run.get('databaseId')!r} has unparseable createdAt {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"run {run.get('databaseId')!r} createdAt {value!r} has no timezone")
    return parsed


def actually_tested(run: Mapping[str, Any], jobs: Iterable[Mapping[str, Any]]) -> bool:
    """True if ``run`` is completed and its suite job concluded ``success`` or ``failure`` (see the module docstring)."""
    if run.get("status") != "completed":
        return False
    return any(job.get("name") == SUITE_JOB_NAME and job.get("conclusion") in TESTED_CONCLUSIONS for job in jobs)


def decide(head_sha: str, runs: Iterable[Mapping[str, Any]], now: datetime, exclude_run_id: Any = None) -> tuple[str, str]:
    """Return ``(decision, reason)`` for main's ``head_sha`` given ``runs`` (each with ``tested``) at ``now`` (tz-aware)."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not head_sha:
        raise ValueError("head_sha is required")
    at_head = [
        r for r in runs
        if r.get("headBranch", MAIN_BRANCH) == MAIN_BRANCH and r.get("headSha") == head_sha and r.get("databaseId") != exclude_run_id
    ]
    stamped = [(_parse_time(r.get("createdAt"), run=r), r) for r in at_head]  # parse all first: bad data fails loud
    tested = [(t, r) for t, r in stamped if r.get("tested") is True and r.get("status") == "completed"]
    short = head_sha[:9]
    if not tested:
        return RUN, f"no completed run has tested main's head {short}"
    newest_time, newest = max(tested, key=lambda pair: pair[0])
    age = now - newest_time
    hours = age.total_seconds() / 3600
    limit = RERUN_AFTER.total_seconds() / 3600
    if age < RERUN_AFTER:
        return SKIP, f"main's head {short} was tested by run {newest.get('databaseId')} {hours:.2f} h ago, under the {limit:g} h rerun interval"
    return RUN, f"main's head {short} was last tested by run {newest.get('databaseId')} {hours:.2f} h ago, at or over the {limit:g} h rerun interval"


def _gh_json(args: list[str]) -> Any:
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def collect(
    head_sha: str,
    list_runs: Callable[[], list[dict]] | None = None,
    view_jobs: Callable[[Any], list[dict]] | None = None,
) -> list[dict]:
    """Recent Slow regression runs with ``tested`` filled in. Jobs are fetched only for completed runs at ``head_sha``."""
    list_runs = list_runs or (
        lambda: _gh_json([
            "run", "list", "--workflow", "slow-regression.yml", "--branch", MAIN_BRANCH, "--limit", "30",
            "--json", "databaseId,event,status,createdAt,headBranch,headSha",
        ])
    )
    view_jobs = view_jobs or (lambda run_id: _gh_json(["run", "view", str(run_id), "--json", "jobs"]).get("jobs", []))
    runs = []
    for run in list_runs():
        run = dict(run)
        run["tested"] = run.get("headSha") == head_sha and run.get("status") == "completed" and actually_tested(run, view_jobs(run["databaseId"]))
        runs.append(run)
    return runs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("decide", "collect"):
        p = sub.add_parser(name)
        p.add_argument("--head-sha", required=True)
    sub.choices["decide"].add_argument("--exclude-run-id", type=int)
    sub.choices["decide"].add_argument("--now", help="ISO-8601 UTC time to decide at (default: the current time)")
    args = parser.parse_args(argv)
    runs = collect(args.head_sha)
    if args.cmd == "collect":
        json.dump(runs, sys.stdout)
        return 0
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    decision, reason = decide(args.head_sha, runs, now, exclude_run_id=args.exclude_run_id)
    print(f"decision={decision}")
    print(f"reason={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
