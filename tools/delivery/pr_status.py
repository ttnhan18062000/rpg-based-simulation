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
— no repo-configured required-status-checks list is read.

**Workflow scoping (TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE, fixing a doc/code
disagreement in the originating ticket).** `gh api .../actions/runs?head_sha=` is repo-wide across
every workflow, not just the one `--workflow-path` names. Runs are **partitioned**, not filtered:
only runs whose `path` matches `--workflow-path` (default `.github/workflows/test.yml`) can produce
GREEN/PENDING/FAILING; every other run at the same head SHA is reported separately in the result's
`other_workflow_runs` field rather than silently voting on the verdict or being discarded — matching
the originating ticket's own Assumption 3 recommendation ("reported separately: a docs-publish
failure is not a code regression"). A head SHA with runs from another workflow but none yet from
the target workflow is `UNKNOWN`, not `FAILING` or `ABSENT` — the other workflow's outcome says
nothing about the target workflow's state.

**Complete context enumeration (TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS).**
The workflow-runs source above never sees a standalone check run (another app, code scanning, a
`ruff` job posted outside the target workflow), so a PR with a failing `ruff` read GREEN. After the
workflow verdict, ``_evaluate_contexts`` therefore enumerates EVERY context for the head SHA:
``commits/<sha>/check-runs`` (all pages), ``commits/<sha>/status`` (all pages), and cross-checks them
against ``gh pr checks`` (text output: this ``gh`` has no ``--json`` for it). Any failing context
-> FAILING naming it; a fetch/pagination error, a required check absent from the examined set, or a
context only ``gh pr checks`` can see -> UNKNOWN, never GREEN. Check runs that belong to a *different*
workflow's run keep their existing "reported separately, does not vote" treatment. The
examined-context count is part of the result so a reader can see how complete the view was.

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
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple, Optional

import yaml

DEFAULT_WORKFLOW_PATH = Path(".github/workflows/test.yml")

# Run-level and job-level GitHub Actions `conclusion` values that mean "this did not pass",
# distinct from PASSING_CONCLUSIONS below. `neutral`/`skipped` are treated as passing, matching
# GitHub's own merge-requirement semantics for non-required checks.
FAILURE_CONCLUSIONS = {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}
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


def _verdict(
    verdict: str, head_sha: Optional[str], reason: str, failing_jobs=None,
    other_workflow_runs=None,
) -> dict:
    return {
        "verdict": verdict,
        "head_sha": head_sha,
        "reason": reason,
        "failing_jobs": failing_jobs or [],
        "other_workflow_runs": other_workflow_runs or [],
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


MAX_CONTEXT_PAGES = 20  # 2000 contexts; reaching it without a complete set is UNKNOWN, not "enough"
_ACTIONS_RUN_ID_RE = re.compile(r"/actions/runs/(\d+)")
STATUS_FAILURE_STATES = {"failure", "error"}
GH_CHECKS_FAILING = {"fail", "cancel"}  # `gh pr checks` bucket words (text output)
GH_CHECKS_PENDING = {"pending"}
ANNOTATION_LIMIT = 5


def _fetch_paginated(run_command: CommandRunner, path: str, list_key: str) -> tuple[Optional[list], Optional[str]]:
    """All pages of an endpoint shaped ``{"total_count": N, <list_key>: [...]}``. Any fetch error,
    malformed page, or short result (fewer items than ``total_count`` once pages run out, or the page
    cap reached) is an error, never a partial list that reads as a complete pass."""
    items: list = []
    for page in range(1, MAX_CONTEXT_PAGES + 1):
        payload, err = _gh_json(
            run_command, ["api", f"repos/{{owner}}/{{repo}}/{path}?per_page=100&page={page}"]
        )
        if err is not None:
            return None, err
        if not isinstance(payload, dict) or not isinstance(payload.get(list_key), list) or not isinstance(
            payload.get("total_count"), int
        ):
            return None, f"'{path}' page {page} had an unexpected shape (no total_count/{list_key})"
        batch = payload[list_key]
        items.extend(batch)
        if len(items) >= payload["total_count"]:
            return items, None
        if not batch:
            return None, f"'{path}' ran out of pages at {len(items)} of {payload['total_count']} items"
    return None, f"'{path}' still incomplete after {MAX_CONTEXT_PAGES} pages"


def _gh_pr_checks(run_command: CommandRunner, pr_number, required: bool) -> tuple[Optional[list], Optional[str]]:
    """``gh pr checks`` text output as ``[(name, bucket)]``. It exits non-zero while any check fails or
    is pending, so stdout is parsed regardless of the exit code. ``[]`` (with no error) means gh says
    there are no (required) checks; an unparseable result is an error."""
    cmd = ["gh", "pr", "checks", str(pr_number)] + (["--required"] if required else [])
    result = run_command(cmd)
    rows = []
    for line in (result.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            return None, f"'{' '.join(cmd)}' produced a line that is not tab-separated: {line[:80]!r}"
        rows.append((parts[0], parts[1].strip()))
    if rows:
        return rows, None
    if "no required checks" in (result.stderr or "").lower() or "no checks reported" in (result.stderr or "").lower():
        return [], None
    return None, f"'{' '.join(cmd)}' returned nothing (exit {result.returncode}): {(result.stderr or '').strip()[:200]}"


def _fetch_annotations(run_command: CommandRunner, check_run_id) -> list:
    payload, err = _gh_json(
        run_command, ["api", f"repos/{{owner}}/{{repo}}/check-runs/{check_run_id}/annotations"]
    )
    if err is not None or not isinstance(payload, list):
        return [{"note": f"could not fetch annotations: {err or 'unexpected shape'}"}]
    return [
        {
            "path": a.get("path"), "start_line": a.get("start_line"),
            "level": a.get("annotation_level"), "message": (a.get("message") or "")[:200],
        }
        for a in payload[:ANNOTATION_LIMIT]
    ]


def _evaluate_contexts(
    head_sha: str, pr_number, other_run_ids: set, run_command: CommandRunner,
) -> dict:
    """Every context at ``head_sha`` that is not part of another workflow's run. Returns failing /
    pending / unknown lists plus ``examined`` and ``notes``; any fetch error lands in ``errors`` so the
    caller can refuse GREEN."""
    out = {"examined": 0, "failing": [], "pending": [], "unrecognized": [], "errors": [], "notes": [], "required": None}

    check_runs, err = _fetch_paginated(run_command, f"commits/{head_sha}/check-runs", "check_runs")
    if err:
        out["errors"].append(f"check-runs: {err}")
        check_runs = []
    statuses, err = _fetch_paginated(run_command, f"commits/{head_sha}/status", "statuses")
    if err:
        out["errors"].append(f"commit status: {err}")
        statuses = []

    voting_names: set = set()
    other_names: set = set()
    for cr in check_runs:
        name = cr.get("name")
        m = _ACTIONS_RUN_ID_RE.search(cr.get("details_url") or "")
        if m and int(m.group(1)) in other_run_ids:
            other_names.add(name)
            continue
        voting_names.add(name)
        out["examined"] += 1
        if cr.get("status") != "completed":
            out["pending"].append({"name": name, "source": "check-run"})
        elif cr.get("conclusion") in FAILURE_CONCLUSIONS:
            out["failing"].append({
                "name": name, "source": "check-run", "conclusion": cr.get("conclusion"),
                "annotations": _fetch_annotations(run_command, cr.get("id")),
            })
        elif cr.get("conclusion") not in PASSING_CONCLUSIONS:
            out["unrecognized"].append({"name": name, "source": "check-run", "conclusion": cr.get("conclusion")})
    for st in statuses:
        name = st.get("context")
        voting_names.add(name)
        out["examined"] += 1
        state = st.get("state")
        if state in STATUS_FAILURE_STATES:
            out["failing"].append({"name": name, "source": "commit-status", "conclusion": state, "annotations": []})
        elif state == "pending":
            out["pending"].append({"name": name, "source": "commit-status"})
        elif state != "success":
            out["unrecognized"].append({"name": name, "source": "commit-status", "conclusion": state})

    known = voting_names | other_names
    if pr_number is not None:
        # Defence in depth against a third enumeration gap: anything gh itself reports that this
        # enumeration did not see, or saw differently, must not be lost.
        gh_all, err = _gh_pr_checks(run_command, pr_number, required=False)
        if err:
            out["notes"].append(f"cross-check with 'gh pr checks' unavailable: {err}")
        else:
            failing_names = {f["name"] for f in out["failing"]}
            pending_names = {p["name"] for p in out["pending"]}
            for name, bucket in gh_all:
                if name in other_names:
                    continue
                if bucket in GH_CHECKS_FAILING and name not in failing_names:
                    out["failing"].append({
                        "name": name, "source": "gh pr checks only", "conclusion": bucket, "annotations": [],
                    })
                elif bucket in GH_CHECKS_PENDING and name not in pending_names:
                    out["pending"].append({"name": name, "source": "gh pr checks only"})
                if name not in known:
                    out["unrecognized"].append({"name": name, "source": "gh pr checks only", "conclusion": bucket})

        required, err = _gh_pr_checks(run_command, pr_number, required=True)
        if err:
            out["required"] = f"required checks unreadable ({err}); completeness rests on the all-contexts rule"
        elif not required:
            out["required"] = "no required checks configured on this branch; completeness rests on the all-contexts rule"
        else:
            missing = sorted({n for n, _ in required} - known)
            out["required"] = f"{len(required)} required check(s) read"
            if missing:
                out["unrecognized"].extend(
                    {"name": n, "source": "required but never examined", "conclusion": None} for n in missing
                )
    else:
        out["notes"].append("no PR number: gh pr checks cross-check and required-check completeness skipped")
    return out


def _apply_contexts(result: dict, ctx: dict) -> dict:
    """Fold the context evaluation into the workflow-derived verdict. Only ever makes it stricter."""
    result["contexts_examined"] = ctx["examined"]
    result["failing_contexts"] = ctx["failing"]
    result["context_notes"] = ctx["notes"] + ([ctx["required"]] if ctx["required"] else [])

    if ctx["failing"]:
        names = ", ".join(f"{f['name']} ({f['source']})" for f in ctx["failing"])
        prior = "" if result["verdict"] == "FAILING" else f" (workflow-run view said {result['verdict']})"
        result["verdict"] = "FAILING"
        result["reason"] = f"{len(ctx['failing'])} failing context(s): {names}{prior}"
    elif result["verdict"] == "GREEN":
        if ctx["errors"]:
            result["verdict"], result["reason"] = "UNKNOWN", "workflow runs look green but the context list is incomplete: " + "; ".join(ctx["errors"])
        elif ctx["pending"]:
            names = ", ".join(p["name"] for p in ctx["pending"])
            result["verdict"], result["reason"] = "PENDING", f"{len(ctx['pending'])} context(s) still pending: {names}"
        elif ctx["unrecognized"]:
            names = ", ".join(f"{u['name']} ({u['source']}: {u['conclusion']})" for u in ctx["unrecognized"])
            result["verdict"], result["reason"] = "UNKNOWN", f"context(s) not confirmed passing: {names}"
        else:
            result["reason"] += f"; {ctx['examined']} context(s) examined, none failing"
    return result


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
    sha_matching = [r for r in all_runs if r.get("head_sha") == head_sha]

    # Partition (not filter) by workflow — see the module docstring's Workflow scoping note. Only
    # the target workflow's runs at this SHA may produce GREEN/PENDING/FAILING; a run from any
    # other workflow is reported separately and never votes on the verdict (AC2).
    target_path = str(workflow_path)
    applicable = [r for r in sha_matching if r.get("path") == target_path]
    other_workflow_runs = [r for r in sha_matching if r.get("path") != target_path]

    if applicable:
        result = _verdict_from_applicable_runs(applicable, head_sha, run_command)
    elif sha_matching:
        result = _verdict(
            "UNKNOWN", head_sha,
            f"{len(other_workflow_runs)} run(s) found for the current head SHA, but none from the "
            f"target workflow ({target_path}) — another workflow's outcome says nothing about the "
            f"target workflow's state",
        )
    elif all_runs:
        result = _verdict(
            "UNKNOWN", head_sha,
            f"{len(all_runs)} run(s) found, but all are for an older SHA than the current head "
            f"({head_sha}) — a stale run says nothing about the current commit",
        )
    else:
        result = _absent_reason(pr_info, resolved_branch, head_sha, workflow_path, run_command)

    result["other_workflow_runs"] = other_workflow_runs

    other_run_ids = {r.get("id") for r in other_workflow_runs if r.get("id") is not None}
    pr_number = pr or (pr_info.get("number") if isinstance(pr_info, dict) else None)
    ctx = _evaluate_contexts(head_sha, pr_number, other_run_ids, run_command)
    return _apply_contexts(result, ctx)


def _print_human(result: dict) -> None:
    print(f"verdict: {result['verdict']}")
    print(f"head_sha: {result['head_sha']}")
    print(f"reason: {result['reason']}")
    other = result.get("other_workflow_runs") or []
    if other:
        print(f"other_workflow_runs: {len(other)} (did not vote on this verdict)")
        for run in other:
            print(f"  {run.get('path')}: status={run.get('status')} conclusion={run.get('conclusion')}")
    if "contexts_examined" in result:
        print(f"contexts_examined: {result['contexts_examined']}")
    for note in result.get("context_notes") or []:
        print(f"note: {note}")
    for ctx in result.get("failing_contexts") or []:
        print(f"  failing context: {ctx['name']} [{ctx['source']}] {ctx['conclusion']}")
        for a in ctx.get("annotations") or []:
            print(f"    annotation: {a.get('path')}:{a.get('start_line')} {a.get('message') or a.get('note')}")
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
