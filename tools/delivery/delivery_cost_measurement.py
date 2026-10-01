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
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from tools.delivery.pr_status import (
        DEFAULT_WORKFLOW_PATH, FAILURE_CONCLUSIONS, CommandResult, _fetch_failing_job_details, _gh_json,
        default_run_command,
    )
    from tools.delivery.ci_triage_classifier import (
        classify_failing_job, parse_regression_policy_soft_paths, parse_workflow_job_paths,
        _KNOWN_BASELINE_DRIFT_PATHS, _KNOWN_PARKED_JOBS,
    )
except ImportError:
    _TOOLS_DIR = Path(__file__).resolve().parent.parent
    if str(_TOOLS_DIR / "delivery") not in sys.path:
        sys.path.insert(0, str(_TOOLS_DIR / "delivery"))
    from pr_status import (  # noqa: E402
        DEFAULT_WORKFLOW_PATH, FAILURE_CONCLUSIONS, CommandResult, _fetch_failing_job_details, _gh_json,
        default_run_command,
    )
    from ci_triage_classifier import (  # noqa: E402
        classify_failing_job, parse_regression_policy_soft_paths, parse_workflow_job_paths,
        _KNOWN_BASELINE_DRIFT_PATHS, _KNOWN_PARKED_JOBS,
    )

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


# --- Delivery rework rate (TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT) -------------------------
#
# Opt-in (`--rework`), read-only, baseline only. The CI history comes from the one `gh api
# repos/{owner}/{repo}/actions/runs` call pattern `pr_status.py` already uses (same endpoint, a
# `per_page`/`page` query instead of `head_sha`); failed runs are classified with the existing
# `_fetch_failing_job_details` + `ci_triage_classifier.classify_failing_job`, no new call pattern. If
# `gh` cannot be reached (the TLS-block trap) the section says so instead of reporting zeros.
# Which PRs count: those merged into `--ref` inside the week range, found by their squash subject
# `(#N)`. A run is attributed to a PR by branch name (`run.head_branch` == the PR's `head.ref` from the
# closed-PR list), because GitHub empties a run's own `pull_requests` once the branch is deleted.

_SQUASH_PR_RE = re.compile(r"\(#(\d+)\)\s*$")
RUNS_ENDPOINT = "repos/{owner}/{repo}/actions/runs?per_page=100&event=pull_request&page="
PULLS_ENDPOINT = "repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30&page="  # 100/page resets the connection on this network


def merged_prs_from_ref(run_command, ref: str, since_week=None, through_week=None) -> dict:
    """{pr_number: merge_commit_sha} for squash-merged PRs reachable from `ref` in the week range."""
    args = ["git", "log", ref, "--format=%H%x09%s"]
    if since_week:
        args.append(f"--since={_iso_week_start(since_week).date().isoformat()}")
    if through_week:
        args.append(f"--until={(_iso_week_end(through_week) + timedelta(days=1)).date().isoformat()}")
    result = run_command(args)
    prs = {}
    if result.returncode != 0:
        return prs
    for line in result.stdout.splitlines():
        sha, _, subject = line.partition("\t")
        m = _SQUASH_PR_RE.search(subject.strip())
        if m:
            prs.setdefault(int(m.group(1)), sha)
    return prs


def _sha_outcome(runs_for_sha: list) -> str:
    """'success' only if every run of the target workflow at this SHA passed on its first attempt."""
    if any(r.get("conclusion") in FAILURE_CONCLUSIONS for r in runs_for_sha):
        return "failure"
    if any(r.get("conclusion") not in ("success", "neutral", "skipped") for r in runs_for_sha):
        return "pending"
    if any((r.get("run_attempt") or 1) > 1 for r in runs_for_sha):
        return "success_after_rerun"
    return "success"


def summarize_pr_runs(runs: list) -> dict:
    """Rework facts for ONE PR from its target-workflow runs (any order)."""
    by_sha: dict = {}
    for r in sorted(runs, key=lambda r: r.get("created_at") or ""):
        by_sha.setdefault(r.get("head_sha"), []).append(r)
    shas = list(by_sha)  # push order = first-run order
    outcomes = [_sha_outcome(by_sha[sha]) for sha in shas]
    first = outcomes[0] if outcomes else None
    first_green_idx = next((i for i, o in enumerate(outcomes) if o in ("success", "success_after_rerun")), None)
    failed_idx = next((i for i, o in enumerate(outcomes) if o == "failure"), None)
    return {
        "pushes": len(shas),
        "first_pass_ci": first == "success",
        "first_outcome": first,
        "reran_attempts": sum(1 for r in runs if (r.get("run_attempt") or 1) > 1),
        "pushes_after_first_green": (len(shas) - first_green_idx - 1) if first_green_idx is not None else 0,
        "failed_then_fixed": failed_idx is not None and any(o.startswith("success") for o in outcomes[failed_idx + 1:]),
        "failed_run_ids": [r.get("id") for r in runs if r.get("conclusion") in FAILURE_CONCLUSIONS],
    }


def _read_pages(run_command, endpoint: str, key, max_pages: int, page_size: int = 100, jq: Optional[str] = None):
    """(rows, error): up to `max_pages` pages of one `gh api` list endpoint."""
    rows, err = [], None
    for page in range(1, max_pages + 1):
        payload, err = _gh_json(run_command, ["api", endpoint + str(page)] + (["--jq", jq] if jq else []))
        if err is not None:
            break
        batch = (payload.get(key, []) if key else payload) if payload is not None else []
        batch = batch if isinstance(batch, list) else []
        rows.extend(batch)
        if len(batch) < page_size:
            break
    return rows, err


def build_rework_report(
    ref: str,
    since_week: Optional[str] = None,
    through_week: Optional[str] = None,
    run_command=default_run_command,
    workflow_path: Path = DEFAULT_WORKFLOW_PATH,
    max_pages: int = 3,
    max_failed_run_details: int = 20,
) -> dict:
    sha = run_command(["git", "rev-parse", ref])
    measured_sha = sha.stdout.strip() if sha.returncode == 0 else None
    prs = merged_prs_from_ref(run_command, ref, since_week, through_week)
    base = {
        "measured_ref": ref, "measured_sha": measured_sha, "snapshot_caveat": SNAPSHOT_CAVEAT,
        "baseline_only": "Measures a baseline; never an 'after' claim and never a verdict on the delivery epic.",
        "prs_merged_in_range": len(prs),
    }
    runs, err = _read_pages(run_command, RUNS_ENDPOINT, "workflow_runs", max_pages)
    pulls, pulls_err = _read_pages(
        run_command, PULLS_ENDPOINT, None, max_pages + 1, page_size=30,
        jq="[.[] | {number, merged_at, head: {ref: .head.ref}}]",  # smaller body: the full PR payload is slow here
    )
    if (err is not None and not runs) or (pulls_err is not None and not pulls):
        return {**base, "ci_history_available": False,
                "reason": f"could not read CI run history: {err or pulls_err}"}

    branch_to_pr = {
        (p.get("head") or {}).get("ref"): p.get("number")
        for p in pulls if p.get("merged_at") and p.get("number") in prs
    }
    target = str(workflow_path)
    per_pr_runs: dict = {n: [] for n in prs}
    for r in runs:
        n = branch_to_pr.get(r.get("head_branch"))
        if r.get("path") == target and n in per_pr_runs:
            per_pr_runs[n].append(r)
    measured = {n: summarize_pr_runs(rs) for n, rs in per_pr_runs.items() if rs}

    job_paths = parse_workflow_job_paths(workflow_path) if Path(workflow_path).exists() else {}
    policy = Path("docs/testing/regression_policy.md")
    soft_paths = parse_regression_policy_soft_paths(policy) if policy.exists() else set()
    classes: dict = {}
    classified = skipped = 0
    for n, summary in sorted(measured.items()):
        changed = []
        shown = run_command(["git", "show", "--name-only", "--format=", prs[n]])
        if shown.returncode == 0:
            changed = [ln for ln in shown.stdout.splitlines() if ln.strip()]
        for run_id in summary["failed_run_ids"]:
            if classified >= max_failed_run_details:
                skipped += 1
                continue
            for job in _fetch_failing_job_details(run_command, run_id):
                category = classify_failing_job(
                    job, job_paths, soft_paths, changed, _KNOWN_BASELINE_DRIFT_PATHS, _KNOWN_PARKED_JOBS
                )["category"]
                classes[category] = classes.get(category, 0) + 1
            classified += 1

    n = len(measured)
    return {
        **base,
        "ci_history_available": True,
        "runs_read": len(runs),
        "closed_prs_read": len(pulls),
        "prs_with_ci_history": n,
        "prs_without_ci_history": len(prs) - n,
        "first_pass_ci_rate": (sum(1 for s in measured.values() if s["first_pass_ci"]) / n) if n else None,
        "prs_failed_then_fixed": sum(1 for s in measured.values() if s["failed_then_fixed"]),
        "pushes_after_first_green_total": sum(s["pushes_after_first_green"] for s in measured.values()),
        "reran_attempts_total": sum(s["reran_attempts"] for s in measured.values()),
        "failure_classes": classes,
        "failed_runs_unclassified_due_to_cap": skipped,
        "classification_note": (
            "class comes from the existing ci_triage_classifier job/step rules with the PR's own changed "
            "files (git show of its merge commit); UNCLASSIFIED means the signals do not place it, not 'fine'"
        ),
        "per_pr": {str(k): {kk: vv for kk, vv in v.items() if kk != "failed_run_ids"} for k, v in sorted(measured.items())},
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
    parser.add_argument(
        "--rework", action="store_true",
        help="Also report delivery rework (first-pass CI rate, failure classes, pushes after first green) "
        "for PRs merged into --ref (default origin/main) in the week range. Reads CI history via gh.",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(args.since_week, args.through_week, args.ref)
        if args.rework:
            report["rework"] = build_rework_report(args.ref or "origin/main", args.since_week, args.through_week)
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
        rw = report.get("rework")
        if rw:
            print(f"\nrework (snapshot of {rw['measured_ref']} @ {rw['measured_sha']}; baseline only):")
            if not rw["ci_history_available"]:
                print(f"  CI history unavailable: {rw['reason']}")
            else:
                rate = rw["first_pass_ci_rate"]
                print(f"  PRs merged in range: {rw['prs_merged_in_range']}, with CI history: {rw['prs_with_ci_history']}")
                print(f"  first-pass CI rate: {'n/a' if rate is None else f'{rate:.1%}'}")
                print(f"  failed-then-fixed PRs: {rw['prs_failed_then_fixed']}, pushes after first green: "
                      f"{rw['pushes_after_first_green_total']}, re-run attempts: {rw['reran_attempts_total']}")
                print(f"  failure classes: {rw['failure_classes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
