"""Static guard for TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK: the SARIF upload job and its permissions.

Only the job that uploads SARIF may hold `security-events: write`; the workflow keeps the repository's read-only
default token for every other job. The job must be advisory, limited to same-repository pull requests (a fork's
token is read-only), and pin the upload action to a full commit SHA.
"""
import re
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_TEXT = (_ROOT / ".github" / "workflows" / "test.yml").read_text()
_WORKFLOW = yaml.safe_load(_TEXT)
_JOBS = _WORKFLOW["jobs"]
_UPLOAD_JOB = "code-health-sarif"
_UPLOAD_USES = re.compile(r"github/codeql-action/upload-sarif@[0-9a-f]{40}")


def _write_scopes(permissions) -> dict:
    """The scopes granted `write` (a bare `write-all` string counts as everything; no block means the read-only default)."""
    if permissions is None:
        return {}
    if isinstance(permissions, str):
        return {"all": permissions} if permissions == "write-all" else {}
    return {scope: level for scope, level in permissions.items() if level == "write"}


def test_only_the_uploading_job_has_security_events_write() -> None:
    holders = [name for name, job in _JOBS.items() if "security-events" in (job.get("permissions") or {})]
    assert holders == [_UPLOAD_JOB]
    assert _JOBS[_UPLOAD_JOB]["permissions"] == {"contents": "read", "security-events": "write"}


def test_the_workflow_has_no_top_level_write_permissions() -> None:
    assert "permissions" not in _WORKFLOW or not _write_scopes(_WORKFLOW["permissions"]), "the default token stays read-only"
    for name, job in _JOBS.items():
        if name != _UPLOAD_JOB:
            assert not _write_scopes(job.get("permissions")), name


def test_the_upload_job_is_advisory_and_limited_to_same_repository_pull_requests() -> None:
    job = _JOBS[_UPLOAD_JOB]
    assert job["name"].endswith("(advisory)") and job["continue-on-error"] is True
    condition = job["if"]
    assert "github.event_name == 'pull_request'" in condition
    assert "github.event.pull_request.head.repo.full_name == github.repository" in condition, "a fork's token is read-only"
    for step in job["steps"]:
        if step.get("id") == "sarif" or "upload-sarif" in step.get("uses", ""):
            assert step["continue-on-error"] is True, step


def test_the_upload_action_is_pinned_to_a_full_commit_sha_and_used_once() -> None:
    uses = [s["uses"] for job in _JOBS.values() for s in job.get("steps", []) if "upload-sarif" in s.get("uses", "")]
    assert len(uses) == 1 and _UPLOAD_USES.fullmatch(uses[0]), uses
    assert "# v4." in _TEXT.split(uses[0])[1].splitlines()[0], "the version stays in a comment next to the SHA"


def test_the_upload_runs_whenever_the_filter_ran_even_with_no_changed_files_but_not_after_could_not_run() -> None:
    steps = {s.get("name"): s for s in _JOBS[_UPLOAD_JOB]["steps"]}
    upload = steps["Upload SARIF to code scanning"]
    assert "steps.sarif.outcome == 'success'" in upload["if"]
    assert "hashFiles" not in upload["if"], "no file-exists guard: the empty SARIF must be uploaded too"
    assert upload["with"]["sarif_file"] == "reports/code_health/code-health.sarif" and upload["with"]["category"] == "code-health"


def test_checkout_does_not_keep_the_token_and_untrusted_text_is_never_interpolated_into_a_run_step() -> None:
    checkout = next(s for s in _JOBS[_UPLOAD_JOB]["steps"] if s.get("uses", "").startswith("actions/checkout"))
    assert checkout["with"]["persist-credentials"] is False
    interpolated = {m for s in _JOBS[_UPLOAD_JOB]["steps"] for m in re.findall(r"\$\{\{\s*([^}]+?)\s*\}\}", s.get("run", ""))}
    assert interpolated <= {"github.event.pull_request.base.sha", "github.event.pull_request.head.sha"}, interpolated
