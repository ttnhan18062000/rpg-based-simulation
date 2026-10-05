"""Static guard for TCK-20261002-UV-REMAINING-CI-JOBS: every Python CI job installs from uv.lock.

Only `tools-a-e` collects the code-health tests that invoke ruff and complexipy, so it alone
syncs the `lint` dependency group; every other job passes `--no-group lint`.
"""
import tomllib
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_JOBS = yaml.safe_load((_ROOT / ".github" / "workflows" / "test.yml").read_text())["jobs"]
# resync-gate (TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC) runs one stdlib-only module on the
# runner's own python3, like changed-files, so it installs nothing.
_NO_PYTHON_INSTALL = {"changed-files", "frontend", "resync-gate"}
# code-health runs the ratchet itself (ruff, complexipy, ast-grep), so it syncs `lint` too.
_LINT_JOBS = {"tools-a-e", "code-health", "code-health-sarif"}


def _run_lines(job: dict) -> list[str]:
    return [s["run"] for s in job["steps"] if "run" in s]


def test_no_job_installs_python_dependencies_with_pip() -> None:
    offenders = [n for n, j in _JOBS.items() if any("pip install" in r for r in _run_lines(j))]
    assert offenders == []


def test_every_python_job_runs_one_locked_uv_sync() -> None:
    for name, job in _JOBS.items():
        if name in _NO_PYTHON_INSTALL:
            continue
        syncs = [r for r in _run_lines(job) if r.startswith("uv sync")]
        assert len(syncs) == 1, name
        assert "--locked" in syncs[0] and "--no-install-project" in syncs[0], name


def test_only_the_jobs_that_run_code_health_tests_sync_the_lint_group() -> None:
    for name, job in _JOBS.items():
        if name in _NO_PYTHON_INSTALL:
            continue
        sync = next(r for r in _run_lines(job) if r.startswith("uv sync"))
        assert ("--no-group lint" not in sync) == (name in _LINT_JOBS), name


def test_lint_group_holds_the_code_health_tools_and_is_a_default_group() -> None:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text())
    groups = data["dependency-groups"]
    lint = {d.split("==")[0] for d in groups["lint"]}
    assert lint == {"ruff", "complexipy", "ast-grep-cli"}
    assert not any(d.split("==")[0] in lint for d in groups["dev"])
    assert data["tool"]["uv"]["default-groups"] == ["dev", "lint"]


def test_code_health_job_is_blocking_and_the_ratchet_step_can_fail_it() -> None:
    """TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING: a required check must be able to fail the PR.

    Branch protection lists the job by its name. Only the changed-paths step keeps a step-level `continue-on-error`; the ratchet step, the package-registry step
    (blocking since TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING) and the job carry none.
    """
    job = _JOBS["code-health"]
    assert job["name"] == "Code health"
    assert "continue-on-error" not in job, "a broken setup must not read as a pass for a required check"
    assert "if" not in job and "needs" not in job, "runs on every trigger, not behind the path-filter gate"
    step = next(s for s in job["steps"] if "codebase.health check" in s.get("run", ""))
    assert "continue-on-error" not in step, "exit 1 or 2 must fail the job"
    assert "--annotate" in step["run"] and "--summary-out" in step["run"] and "$GITHUB_STEP_SUMMARY" in step["run"]
    assert job["timeout-minutes"] == 20 and _JOBS["typecheck"]["timeout-minutes"] == 10, "a hang must not hold a required check"
    tolerant = {s["name"] for s in job["steps"] if s.get("continue-on-error")}
    assert tolerant == {"Paths this PR changed"}
