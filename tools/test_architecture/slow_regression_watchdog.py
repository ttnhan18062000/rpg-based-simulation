"""Decide whether the Slow regression workflow needs a manual dispatch.

TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG. GitHub's scheduled triggers are best-effort:
`slow-regression.yml` runs on the cron ``41 2,8,14,20 * * *`` (every 6 h, owner decision D2; off the hour since 2026-10-09), but a slot is
sometimes never created and observed runs start 1 to 3.5 h late. The hourly watchdog workflow
(`.github/workflows/slow-regression-watchdog.yml`) lists the recent Slow regression runs and calls
:func:`decide`; on ``dispatch`` it runs ``gh workflow run slow-regression.yml --ref main``.

The rule (only runs whose branch is ``main`` count):

* ``skip`` if any run is not yet completed (queued, in progress, waiting, ...);
* ``skip`` if the newest run (any event, any conclusion) was created less than 10 h ago;
* otherwise ``dispatch`` (including when there is no run at all).

Why 10 h: the schedule period is 6 h and the observed lateness is up to 3.5 h, so 10 h = 6 h +
3.5 h + 0.5 h grace. A shorter threshold would dispatch while a late scheduled run is still on its
way, and that run would follow and double the cost. When the schedule fires as designed the
watchdog dispatches nothing; the worst case is one extra run per dropped slot, which replaces the
dropped run instead of adding to it.

Malformed input (a missing or unparseable ``createdAt``, a naive timestamp) raises ``ValueError``:
a silent ``dispatch`` on bad data would spend ~2 runner-hours per hour.

CLI: ``python -m tools.test_architecture.slow_regression_watchdog RUNS.json`` reads the JSON that
``gh run list --json databaseId,event,status,createdAt,headBranch`` prints and prints
``decision=<dispatch|skip>`` and ``reason=<one line>``; ``--now`` takes an ISO-8601 UTC timestamp
for tests and manual checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

MAIN_BRANCH = "main"
MIN_AGE = timedelta(hours=10)

DISPATCH = "dispatch"
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


def decide(runs: Iterable[Mapping[str, Any]], now: datetime) -> tuple[str, str]:
    """Return ``(decision, reason)`` for the given Slow regression runs at ``now`` (tz-aware)."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    main_runs = [r for r in runs if r.get("headBranch") == MAIN_BRANCH]
    if not main_runs:
        return DISPATCH, "no Slow regression run on main"
    # Parse every timestamp first so malformed data fails loud even when an active run would skip.
    stamped = [(_parse_time(r.get("createdAt"), run=r), r) for r in main_runs]
    for _, run in stamped:
        if run.get("status") != "completed":
            return SKIP, f"run {run.get('databaseId')} on main is {run.get('status')}"
    newest_time, newest = max(stamped, key=lambda pair: pair[0])
    age = now - newest_time
    hours = age.total_seconds() / 3600
    if age < MIN_AGE:
        return SKIP, (
            f"newest run {newest.get('databaseId')} ({newest.get('event')}) is {hours:.2f} h old, "
            f"under the {MIN_AGE.total_seconds() / 3600:g} h threshold"
        )
    return DISPATCH, (
        f"newest run {newest.get('databaseId')} ({newest.get('event')}) is {hours:.2f} h old, "
        f"at or over the {MIN_AGE.total_seconds() / 3600:g} h threshold"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs_json", help="path to `gh run list --json ...` output, or - for stdin")
    parser.add_argument("--now", help="ISO-8601 UTC time to decide at (default: the current time)")
    args = parser.parse_args(argv)
    raw = sys.stdin.read() if args.runs_json == "-" else open(args.runs_json, encoding="utf-8").read()
    runs = json.loads(raw)
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    decision, reason = decide(runs, now)
    print(f"decision={decision}")
    print(f"reason={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
