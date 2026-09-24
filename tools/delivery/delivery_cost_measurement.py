"""Reports `gh`-calls-per-PR and subject traceability over a week range in one command
(TCK-20260924-DELIVERY-COST-MEASUREMENT), so this epic's own before/after claim is measured
rather than asserted.

Built on `tools/agent-monitoring/bash_command_mix.py`, extended (not duplicated) with a
`gh`-specific 3-word subcommand classifier — see that module's `gh_subcommand_key()`. This module
never reimplements Bash-head classification; it imports it.

**Two measurement traps, designed in rather than re-discovered** (both hit for real while drafting
this epic's plan):

1. **Never measure from the working tree.** `--ref` reads shards from a git ref's tree via `git
   ls-tree`/`git show` (`bash_command_mix.load_tools_rows_from_ref`), immune to this worktree
   being behind `origin/main`. Omitting `--ref` does not silently fall back to an equivalent
   reading — the output is unmistakably labeled a working-tree snapshot.
2. **A "closed" calendar week keeps growing.** Every report carries a snapshot caveat: any weekly
   total from this corpus is a snapshot as of the ref measured, not a final count, because every PR
   merge stages `agent-monitoring/` and can append past-week-stamped rows long after that week
   "ends."

**This module measures a baseline only — it never computes or presents an "after" number.** The
epic's own tools were not in use while its own tickets were implemented, and the corpus covering
that implementation work is contaminated by unrelated session activity. A real "after" needs a PR
actually delivered using `pr_status.py`/`pr_render.py`, which has not happened yet as of this
ticket. Out of scope, deliberately: judging whether the epic succeeded (report only, the user
judges), token-cost attribution (a different question, answered by `real_token_usage.py`), and any
blocking threshold or ratchet on the numbers.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from tools.delivery.pr_status import CommandResult, default_run_command
except ImportError:
    _TOOLS_DIR = Path(__file__).resolve().parent.parent
    if str(_TOOLS_DIR / "delivery") not in sys.path:
        sys.path.insert(0, str(_TOOLS_DIR / "delivery"))
    from pr_status import CommandResult, default_run_command  # noqa: E402

_AGENT_MONITORING_DIR = Path(__file__).resolve().parent.parent / "agent-monitoring"
if str(_AGENT_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_MONITORING_DIR))
import bash_command_mix as bcm  # noqa: E402

TICKET_ID = "TCK-20260924-DELIVERY-COST-MEASUREMENT"
SNAPSHOT_CAVEAT = (
    "Snapshot, not a final count: a 'closed' calendar week keeps growing, because every PR merge "
    "stages agent-monitoring/ and can append past-week-stamped rows long after that week ends."
)
WORKING_TREE_SNAPSHOT_LABEL = (
    "measured from the local working tree (no --ref given) -- may be behind origin/main and is "
    "not a valid before/after datapoint; pass --ref for a pinned, reproducible reading"
)


def _iso_week_start(week: str) -> datetime:
    return datetime.strptime(f"{week}-1", "%G-W%V-%u")


def _iso_week_end(week: str) -> datetime:
    return _iso_week_start(week) + timedelta(days=6)


def build_gh_call_report(rows: list) -> dict:
    gh_rows = [r for r in rows if r.get("tool") == "Bash" and bcm.bash_head(r.get("input_summary") or "") == "gh"]

    sub_counts: dict = {}
    unparseable = 0
    observation = 0
    action = 0
    pr_create_count = 0
    for row in gh_rows:
        summary = row.get("input_summary") or ""
        key = bcm.gh_subcommand_key(summary)
        if key is None:
            unparseable += 1
            continue
        sub_counts[key] = sub_counts.get(key, 0) + 1
        if key in bcm.GH_OBSERVATION_SUBCOMMANDS:
            observation += 1
        elif key in bcm.GH_ACTION_SUBCOMMANDS:
            action += 1
        if key == "gh pr create":
            pr_create_count += 1

    total_gh = len(gh_rows)
    gh_calls_per_pr = (total_gh / pr_create_count) if pr_create_count else (
        "undefined: zero 'gh pr create' calls in window, cannot compute a per-PR rate"
    )

    return {
        "gh_calls_total": total_gh,
        "gh_subcommand_counts": sub_counts,
        "gh_unparseable_count": unparseable,
        "gh_pr_create_count": pr_create_count,
        "gh_calls_per_pr": gh_calls_per_pr,
        "gh_observation_calls": observation,
        "gh_action_calls": action,
        "gh_observation_share": (observation / total_gh) if total_gh else 0.0,
    }


def measure_subject_traceability(
    run_command=default_run_command,
    since_week: Optional[str] = None,
    through_week: Optional[str] = None,
    measured_ref: str = "HEAD",
) -> dict:
    args = ["git", "log", measured_ref, "--format=%s"]
    if since_week:
        args += [f"--since={_iso_week_start(since_week).date().isoformat()}"]
    if through_week:
        until = (_iso_week_end(through_week) + timedelta(days=1)).date().isoformat()
        args += [f"--until={until}"]

    result = run_command(args)
    if result.returncode != 0:
        return {"total_subjects": 0, "ticket_id_subjects": 0, "share": 0.0, "error": result.stderr[:300]}

    subjects = [line for line in result.stdout.splitlines() if line.strip()]
    ticket_subjects = sum(1 for s in subjects if "TCK-" in s)
    total = len(subjects)
    return {
        "total_subjects": total,
        "ticket_id_subjects": ticket_subjects,
        "share": (ticket_subjects / total) if total else 0.0,
    }


def build_report(
    since_week: Optional[str] = None,
    through_week: Optional[str] = None,
    ref: Optional[str] = None,
    data_dir: Optional[Path] = None,
    run_command=default_run_command,
) -> dict:
    if ref:
        rows, sha = bcm.load_tools_rows_from_ref(ref, "tools", since_week, through_week)
        measured_ref = ref
        measured_sha = sha
    else:
        rows = bcm.load_tools_rows(data_dir or bcm.DEFAULT_DATA_DIR, since_week, through_week)
        measured_ref = WORKING_TREE_SNAPSHOT_LABEL
        measured_sha = None

    mix_report = bcm.build_bash_mix_report(rows, since_week, through_week)
    gh_report = build_gh_call_report(rows)
    traceability = measure_subject_traceability(
        run_command, since_week, through_week, measured_ref=ref or "HEAD",
    )

    git_head_calls = mix_report["bash_head_counts"].get("git", 0)
    git_status_diff_calls = sum(
        count for key, count in mix_report["bash_subcommand_counts"].items()
        if key in ("git status", "git diff")
    )

    return {
        "ticket_id": TICKET_ID,
        "since_week": since_week,
        "through_week": through_week,
        "measured_ref": measured_ref,
        "measured_sha": measured_sha,
        "snapshot_caveat": SNAPSHOT_CAVEAT,
        **gh_report,
        "git_calls_total": git_head_calls,
        "git_status_diff_calls": git_status_diff_calls,
        "git_status_diff_share": (git_status_diff_calls / git_head_calls) if git_head_calls else 0.0,
        "subject_traceability": {
            **traceability,
            "denominator": "same week range as the gh figures",
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Report gh-calls-per-PR and subject traceability over a week range. "
        "Read-only, advisory: never opens agent-monitoring/data/ for writing."
    )
    parser.add_argument("--ref", default=None, help="Git ref/SHA to measure from (recommended for any before/after datapoint).")
    parser.add_argument("--since-week", default=None)
    parser.add_argument("--through-week", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = build_report(args.since_week, args.through_week, args.ref)
    except Exception as exc:  # noqa: BLE001 - the one deliberate non-zero-exit path
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"measured_ref: {report['measured_ref']}")
        print(f"measured_sha: {report['measured_sha']}")
        print(f"{report['snapshot_caveat']}\n")
        print(f"gh calls total: {report['gh_calls_total']}")
        print(f"gh pr create count: {report['gh_pr_create_count']}")
        print(f"gh calls per PR: {report['gh_calls_per_pr']}")
        print(f"gh observation/action: {report['gh_observation_calls']}/{report['gh_action_calls']}")
        print(f"gh unparseable: {report['gh_unparseable_count']}")
        print(f"git status/diff share of git calls: {report['git_status_diff_share']:.1%}")
        tr = report["subject_traceability"]
        print(f"subject traceability: {tr['ticket_id_subjects']}/{tr['total_subjects']} "
              f"({tr['share']:.1%}), denominator: {tr['denominator']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
