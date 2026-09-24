"""One-call typed delivery-status verdict for a PR (TCK-20260924-DELIVERY-STATUS-TOOL).

Replaces the ~14 `gh` polling round-trips per PR measured in
`docs/plans/agent_infrastructure/github_delivery_process/plan.md` §1.1 with a single call that
answers "what is the state of this PR, against its current head SHA, right now?" and encodes the
CLAUDE.md "CI Failure Triage" decision tree as code instead of prose an agent must re-derive by
hand every time.

Verdicts (never inferred from an empty/zero-looking result — see the `UNKNOWN` branch below,
which exists specifically because a blocked fetch has, in this repo, previously been misread as
"0 pending" and reported green — [[project_ci_poll_tls_block_false_green]]):

- ``GREEN``   every applicable check completed successfully against the current head SHA.
- ``PENDING`` a run for the current head SHA exists and is genuinely in progress.
- ``FAILING`` at least one completed run for the current head SHA failed; per-step name/conclusion
  is attached for every failing job, fetched without ever reading a log body.
- ``ABSENT``  no run exists for the current head SHA, and a specific cause is established (a
  CONFLICTING PR with a pull_request-only trigger, or a push that has not landed yet).
- ``UNKNOWN`` state could not be established — either a fetch itself failed/returned something
  unparseable, or the only runs found are for an older SHA than the current head. Never reported
  as GREEN.

"Required" is defined here as "every check that ran completed successfully" (ticket Assumption 2)
— no repo-configured required-status-checks list is read. `deploy-docs.yml` runs are never in
scope, since this module only ever reasons about the single workflow file it is pointed at
(ticket Assumption 3).

Out of scope, deliberately (see the ticket's own Out of Scope section): polling/retry loops (one
call in, one verdict out — the caller decides when to ask again), any write of any kind (read-only,
no exceptions), classifying *why* a failure happened beyond job/step conclusions (that is
TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER, which consumes this module's output), and any
merge/blocking behavior — the exit code reflects only whether the tool itself ran, never whether
the PR is green (a FAILING verdict still exits 0; only a genuine internal error in this tool's own
code exits non-zero).

All I/O is routed through an injectable ``run_command`` callable, so every branch below is
unit-testable without a real ``gh``/``git`` binary or network access — see
`tests/tools/test_delivery_pr_status.py`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple, Optional

import yaml

DEFAULT_WORKFLOW_PATH = Path(".github/workflows/test.yml")

# Run-level and job-level GitHub Actions `conclusion` values that mean "this did not pass",
# distinct from PASSING_CONCLUSIONS below. `neutral`/`skipped` are treated as passing, matching
# GitHub's own merge-requirement semantics for non-required checks.
FAILURE_CONCLUSIONS = {"failure", "timed_out", "cancelled", "action_required"}
PASSING_CONCLUSIONS = {"success", "neutral", "skipped"}
IN_PROGRESS_STATUSES = {"in_progress", "queued", "waiting", "requested", "pending"}

# Keyword scan used only to make an UNKNOWN reason more specific when possible — never used to
# decide the verdict itself. The real fix for the incident this encodes is structural (check the
# return code before ever treating stdout as "the answer"), not pattern-matching on stderr text.
_TLS_BLOCK_KEYWORDS = ("certificate", "ssl", "tls", "x509", "fortinet", "fortiguard")


class CommandResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[list], CommandResult]


def default_run_command(cmd: list, timeout: int = 30) -> CommandResult:
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return CommandResult(1, "", str(exc))


def _tls_hint(stderr: str) -> Optional[str]:
    lowered = (stderr or "").lower()
    for kw in _TLS_BLOCK_KEYWORDS:
        if kw in lowered:
            return kw
    return None


def _gh_json(run_command: CommandRunner, args: list) -> tuple[Optional[Any], Optional[str]]:
    """Runs `gh <args>`. Never treats a failed or unparseable fetch as an empty result — this is
    the structural fix for the TLS-block-reads-as-"0 pending" incident: the return code is checked
    BEFORE stdout is ever parsed, so a blocked fetch can never fall through to a zero-count code
    path."""
    cmd = ["gh"] + args
    result = run_command(cmd)
    rendered = " ".join(cmd)
    if result.returncode != 0:
        detail = (result.stderr or "").strip()[:300]
        hint = _tls_hint(result.stderr)
        if hint:
            return None, (
                f"'{rendered}' failed (exit {result.returncode}) — looks like a network/TLS "
                f"block (matched '{hint}'), not a state to report: {detail}"
            )
        return None, f"'{rendered}' failed (exit {result.returncode}): {detail}"
    try:
        return json.loads(result.stdout), None
    except (ValueError, TypeError):
        return None, f"'{rendered}' exited 0 but stdout was not valid JSON"


def _git(run_command: CommandRunner, args: list) -> tuple[Optional[str], Optional[str]]:
    cmd = ["git"] + args
    result = run_command(cmd)
    rendered = " ".join(cmd)
    if result.returncode != 0:
        detail = (result.stderr or "").strip()[:300]
        return None, f"'{rendered}' failed (exit {result.returncode}): {detail}"
    return result.stdout, None


def _verdict(verdict: str, head_sha: Optional[str], reason: str, failing_jobs=None) -> dict:
    return {
        "verdict": verdict,
        "head_sha": head_sha,
        "reason": reason,
        "failing_jobs": failing_jobs or [],
    }


def workflow_covers_branch_via_push(workflow_path: Path, branch: Optional[str]) -> bool:
    """Whether `workflow_path`'s `on.push` trigger would ALSO run for `branch`'s own commits —
    i.e. whether this workflow is genuinely pull_request-only for this branch. Fails open (True,
    "don't claim the pull_request-only cause") on any read/parse error, since a false ABSENT
    reason is worse than falling through to the generic "no known cause" reason."""
    if not branch:
        return True
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        return True

    if not isinstance(doc, dict):
        return True

    # YAML 1.1 (PyYAML's default resolver) parses the bare key `on:` as the boolean True, not the
    # string "on" — a well-known GitHub Actions workflow YAML gotcha. Check both.
    on_block = doc.get("on", doc.get(True))
    if not isinstance(on_block, dict):
        return True

    if "push" not in on_block:
        return False  # no push trigger at all: this workflow never runs on a bare push, any branch

    push_block = on_block["push"]
    if not isinstance(push_block, dict):
        return True  # `push:` with no filters (empty/null) — unrestricted, covers every branch

    branches = push_block.get("branches")
    if branches is None:
        return True  # push present, no `branches:` filter — covers every branch

    return branch in branches


def _fetch_failing_job_details(run_command: CommandRunner, run_id) -> list:
    """Per ticket Scope item 5: job/step conclusions only, never a log body. Two calls per run —
    the jobs list to find which jobs failed, then the per-job endpoint (exactly as the ticket
    names it) for that job's own step conclusions."""
    jobs_payload, err = _gh_json(
        run_command, ["api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs"]
    )
    if err is not None or not isinstance(jobs_payload, dict):
        return [{
            "run_id": run_id, "job_id": None, "job_name": None, "steps": [],
            "note": f"could not fetch job list: {err}",
        }]

    details = []
    for job in jobs_payload.get("jobs", []):
        if job.get("conclusion") not in FAILURE_CONCLUSIONS:
            continue
        job_id = job.get("id")
        steps_payload, step_err = _gh_json(
            run_command, ["api", f"repos/{{owner}}/{{repo}}/actions/jobs/{job_id}"]
        )
        if step_err is not None or not isinstance(steps_payload, dict):
            details.append({
                "run_id": run_id, "job_id": job_id, "job_name": job.get("name"), "steps": [],
                "note": f"could not fetch step detail: {step_err}",
            })
            continue
        steps = [
            {"name": s.get("name"), "conclusion": s.get("conclusion")}
            for s in steps_payload.get("steps", [])
        ]
        details.append({
            "run_id": run_id, "job_id": job_id, "job_name": job.get("name"), "steps": steps,
        })
    return details


def _verdict_from_applicable_runs(applicable: list, head_sha: str, run_command: CommandRunner) -> dict:
    completed = [r for r in applicable if r.get("status") == "completed"]
    failed = [r for r in completed if r.get("conclusion") in FAILURE_CONCLUSIONS]

    if failed:
        failing_jobs = []
        for run in failed:
            failing_jobs.extend(_fetch_failing_job_details(run_command, run.get("id")))
        return _verdict(
            "FAILING", head_sha,
            f"{len(failed)} run(s) failed against current head SHA {head_sha}",
            failing_jobs=failing_jobs,
        )

    if completed and len(completed) == len(applicable) and all(
        r.get("conclusion") in PASSING_CONCLUSIONS for r in completed
    ):
        return _verdict("GREEN", head_sha, f"all checks completed successfully against {head_sha}")

    in_progress = [r for r in applicable if r.get("status") in IN_PROGRESS_STATUSES]
    if in_progress:
        return _verdict(
            "PENDING", head_sha, f"{len(in_progress)} run(s) in progress against {head_sha}"
        )

    return _verdict(
        "UNKNOWN", head_sha,
        "applicable run(s) found for the current head SHA but in an unrecognized status/"
        f"conclusion shape: {[(r.get('status'), r.get('conclusion')) for r in applicable]}",
    )


def _absent_reason(
    pr_info: dict, branch: Optional[str], head_sha: str, workflow_path: Path,
    run_command: CommandRunner,
) -> dict:
    if not branch:
        return _verdict(
            "ABSENT", head_sha,
            "no run exists for this SHA, and no branch name is available to disambiguate further",
        )

    remote_out, err = _git(run_command, ["ls-remote", "origin", branch])
    if err is not None:
        return _verdict(
            "UNKNOWN", head_sha,
            f"no run exists for this SHA, and the push-landed disambiguator itself failed "
            f"(cannot rule out an unlanded push): {err}",
        )

    remote_sha = remote_out.strip().split()[0] if remote_out and remote_out.strip() else None
    if remote_sha != head_sha:
        return _verdict(
            "ABSENT", head_sha,
            f"no run exists for this SHA, and the push may not have landed: origin/{branch} is "
            f"at {remote_sha or '(no ref found)'}, PR head is {head_sha}. Re-push, don't re-trigger.",
        )

    mergeable = pr_info.get("mergeable")
    if mergeable == "CONFLICTING" and not workflow_covers_branch_via_push(workflow_path, branch):
        return _verdict(
            "ABSENT", head_sha,
            "PR is CONFLICTING and this workflow's 'on:' block only triggers via pull_request for "
            "this branch (no covering push trigger) — GitHub cannot compute refs/pull/N/merge "
            "while CONFLICTING, so no run is created at all. Fix: resolve the merge conflict. A "
            "re-trigger commit, force-push, or branch recreation will NOT help and destroys the "
            "evidence that would show this cause.",
        )

    return _verdict(
        "ABSENT", head_sha,
        "no run exists for this SHA; the push has landed and the PR is not CONFLICTING-with-no-"
        "push-trigger, so neither known absent-run cause applies — cause not determined",
    )


def compute_pr_status(
    pr: Optional[str] = None,
    branch: Optional[str] = None,
    workflow_path: Path = DEFAULT_WORKFLOW_PATH,
    run_command: CommandRunner = default_run_command,
) -> dict:
    pr_view_args = ["pr", "view", "--json", "number,headRefOid,mergeable,headRefName"]
    if pr:
        pr_view_args.insert(2, str(pr))
    pr_info, err = _gh_json(run_command, pr_view_args)
    if err is not None:
        return _verdict("UNKNOWN", None, f"could not resolve PR info: {err}")

    head_sha = pr_info.get("headRefOid") if isinstance(pr_info, dict) else None
    if not head_sha:
        return _verdict("UNKNOWN", None, "'gh pr view' returned no headRefOid")

    resolved_branch = branch or (pr_info.get("headRefName") if isinstance(pr_info, dict) else None)

    runs_payload, err = _gh_json(
        run_command, ["api", f"repos/{{owner}}/{{repo}}/actions/runs?head_sha={head_sha}"]
    )
    if err is not None:
        return _verdict("UNKNOWN", head_sha, f"could not fetch run list: {err}")

    all_runs = runs_payload.get("workflow_runs", []) if isinstance(runs_payload, dict) else []
    applicable = [r for r in all_runs if r.get("head_sha") == head_sha]

    if applicable:
        return _verdict_from_applicable_runs(applicable, head_sha, run_command)

    if all_runs:
        return _verdict(
            "UNKNOWN", head_sha,
            f"{len(all_runs)} run(s) found, but all are for an older SHA than the current head "
            f"({head_sha}) — a stale run says nothing about the current commit",
        )

    return _absent_reason(pr_info, resolved_branch, head_sha, workflow_path, run_command)


def _print_human(result: dict) -> None:
    print(f"verdict: {result['verdict']}")
    print(f"head_sha: {result['head_sha']}")
    print(f"reason: {result['reason']}")
    for job in result["failing_jobs"]:
        print(f"  failing job: {job.get('job_name')} (run {job.get('run_id')}, job {job.get('job_id')})")
        for step in job.get("steps", []):
            print(f"    step: {step.get('name')}: {step.get('conclusion')}")
        if job.get("note"):
            print(f"    note: {job['note']}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="One-call typed delivery-status verdict for a PR (GREEN/PENDING/FAILING/"
        "ABSENT/UNKNOWN), replacing ~14 gh polling round-trips per PR. Read-only and advisory: "
        "exits 0 for every verdict including FAILING and UNKNOWN; non-zero only on a genuine "
        "internal error in this tool's own code."
    )
    parser.add_argument("--pr", default=None, help="PR number; omit to infer from the current branch")
    parser.add_argument("--branch", default=None, help="Branch name; omit to infer from PR info")
    parser.add_argument("--workflow-path", default=str(DEFAULT_WORKFLOW_PATH))
    parser.add_argument(
        "--json", action="store_true",
        help="Emit MARKER:<json> (matching the tools/gate_checks/ JSON CLI contract) instead of "
        "the human-readable form.",
    )
    args = parser.parse_args(argv)

    try:
        # `run_command` is passed explicitly (rather than relying on compute_pr_status's own
        # default parameter) so that patching the module-level `default_run_command` name — the
        # standard test seam — takes effect here too. A default-argument value is bound once at
        # function-definition time and would not see a later monkeypatch of the global.
        result = compute_pr_status(
            pr=args.pr, branch=args.branch, workflow_path=Path(args.workflow_path),
            run_command=default_run_command,
        )
    except Exception as exc:  # noqa: BLE001 - the one deliberate non-zero-exit path (AC8)
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print("MARKER:" + json.dumps(result))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
