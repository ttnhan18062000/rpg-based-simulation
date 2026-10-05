"""Decide whether a pull_request `synchronize` push left the PR's own content unchanged.

When a PR goes CONFLICTING on `docs/REGISTRY.yaml` alone, the fix is a sync merge from main plus a
regenerated REGISTRY. The PR's own code did not change, so re-running every CI job repeats a result the
previous commit already produced. This module decides, fail open, whether the heavy jobs may be skipped.

`pr_content_unchanged` is `true` only when ALL hold; any other case, error or missing data is `false`:

1. The event is `pull_request` / `synchronize` and BEFORE exists in the clone (a force-push may drop it).
2. The PR's own patch, ignoring `docs/REGISTRY.yaml`, has the same `git patch-id --stable` before and
   after. The patch is the diff from `merge-base(BASE, commit)` to the commit, so a change by main next to
   the PR's lines changes the context and gives `false`. That is the intended conservative behaviour.
3. Every run of the `Tests` workflow on BEFORE has concluded, and every job in it is `success`,
   `skipped` or `neutral`. A failure, cancellation (a concurrency-group cancel included), timeout, a run
   still in progress, no run at all, or an API error gives `false`.

A chain of re-syncs works: each push compares against its own BEFORE, which was itself green or validly
skipped. The accepted risk is that the PR's code combined with the new main commits goes untested before
merge; the push to main always runs everything and surfaces a clash there.

The `resync-gate` job that calls this takes about 15 s (blobless full-history clone), so the heavy jobs wait
on seconds, not on the roughly 100 s `changed-files` clone.

Run: `python3 -m tools.test_architecture.registry_resync_skip` with the inputs in the environment
(`EVENT_NAME`, `EVENT_ACTION`, `BASE_SHA`, `BEFORE_SHA`, `AFTER_SHA`, `GITHUB_REPOSITORY`, `GITHUB_TOKEN`).
Prints `pr_content_unchanged=<bool>` on the first line and a markdown summary after it; the workflow
splits them. Always exits 0 so the gate can never fail the workflow.
"""

import json
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

REGISTRY_PATH = "docs/REGISTRY.yaml"
WORKFLOW_NAME = "Tests"
PASSING_CONCLUSIONS = frozenset({"success", "skipped", "neutral"})
_API = "https://api.github.com"

# A fetcher takes a REST path (beginning with "/") and returns the decoded JSON body; it raises on error.
Fetcher = Callable[[str], Dict[str, object]]


@dataclass(frozen=True)
class Decision:
    unchanged: bool
    rule: str  # the rule that decided, one line
    before: str


def _git(repo: str, *args: str, stdin: Optional[str] = None) -> str:
    done = subprocess.run(
        ["git", "-C", repo, *args], input=stdin, capture_output=True, text=True, check=True
    )
    return done.stdout


def _commit_exists(repo: str, sha: str) -> bool:
    if not sha or set(sha) == {"0"}:
        return False
    probe = subprocess.run(
        ["git", "-C", repo, "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True
    )
    return probe.returncode == 0


def pr_patch_id(repo: str, base: str, commit: str) -> str:
    """Stable patch-id of the PR's own change at `commit`, ignoring the REGISTRY file."""
    fork_point = _git(repo, "merge-base", base, commit).strip()
    patch = _git(repo, "diff", fork_point, commit, "--", ".", f":(exclude){REGISTRY_PATH}")
    if not patch.strip():
        return "empty"
    out = _git(repo, "patch-id", "--stable", stdin=patch).split()
    return out[0] if out else "empty"


def previous_run_passed(fetch: Fetcher, repo_slug: str, before: str) -> Tuple[bool, str]:
    """True only when every `Tests` run on BEFORE finished and every job in it passed or was skipped."""
    runs = fetch(f"/repos/{repo_slug}/actions/runs?head_sha={before}&per_page=100")
    tests = [r for r in runs.get("workflow_runs", []) if r.get("name") == WORKFLOW_NAME]
    if not tests:
        return False, f"no `{WORKFLOW_NAME}` run found on {before[:12]}"
    for run in tests:
        if run.get("status") != "completed":
            return False, f"run {run.get('id')} is {run.get('status')}"
        jobs = fetch(f"/repos/{repo_slug}/actions/runs/{run['id']}/jobs?per_page=100")
        job_list = jobs.get("jobs", [])
        if not job_list or int(jobs.get("total_count", len(job_list))) > len(job_list):
            return False, f"run {run['id']} jobs unavailable or paginated"
        for job in job_list:
            if job.get("conclusion") not in PASSING_CONCLUSIONS:
                return False, f"run {run['id']} job `{job.get('name')}` is {job.get('conclusion')}"
    return True, f"{len(tests)} `{WORKFLOW_NAME}` run(s) on {before[:12]} all green or skipped"


def decide(
    repo: str,
    repo_slug: str,
    event_name: str,
    action: str,
    base: str,
    before: str,
    after: str,
    fetch: Fetcher,
) -> Decision:
    """Never raises: any error is the fail-open answer."""
    try:
        if event_name != "pull_request" or action != "synchronize":
            return Decision(False, f"event is {event_name}/{action}, not pull_request/synchronize", before)
        if not _commit_exists(repo, before):
            return Decision(False, "BEFORE commit is missing from the clone (force-push or rebase)", before)
        if not _commit_exists(repo, base) or not _commit_exists(repo, after):
            return Decision(False, "BASE or AFTER commit is missing from the clone", before)
        if pr_patch_id(repo, base, before) != pr_patch_id(repo, base, after):
            return Decision(False, "the PR's own patch (REGISTRY excluded) changed", before)
        ok, detail = previous_run_passed(fetch, repo_slug, before)
        if not ok:
            return Decision(False, f"previous commit not green: {detail}", before)
        return Decision(True, f"PR patch identical (REGISTRY excluded) and previous commit green: {detail}", before)
    except Exception as exc:  # fail open: a failed check must run everything, never skip
        return Decision(False, f"decision errored ({type(exc).__name__}: {exc})", before)


def github_fetcher(token: str) -> Fetcher:
    def fetch(path: str) -> Dict[str, object]:
        req = urllib.request.Request(
            _API + path,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    return fetch


def render(decision: Decision) -> List[str]:
    lines = [f"pr_content_unchanged={'true' if decision.unchanged else 'false'}"]
    lines.append("### Registry re-sync skip")
    verdict = "heavy jobs that read no REGISTRY.yaml are skipped" if decision.unchanged else "everything runs"
    lines.append(f"- Decision: **{verdict}**")
    lines.append(f"- Rule that decided: {decision.rule}")
    lines.append(f"- BEFORE compared against: `{decision.before or 'none'}`")
    return lines


def main() -> int:
    env = os.environ
    try:
        decision = decide(
            repo=".",
            repo_slug=env.get("GITHUB_REPOSITORY", ""),
            event_name=env.get("EVENT_NAME", ""),
            action=env.get("EVENT_ACTION", ""),
            base=env.get("BASE_SHA", ""),
            before=env.get("BEFORE_SHA", ""),
            after=env.get("AFTER_SHA", ""),
            fetch=github_fetcher(env.get("GITHUB_TOKEN", "")),
        )
    except Exception as exc:
        decision = Decision(False, f"gate errored ({type(exc).__name__}: {exc})", env.get("BEFORE_SHA", ""))
    print("\n".join(render(decision)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
