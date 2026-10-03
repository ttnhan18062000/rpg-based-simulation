"""Static guard for TCK-20261002-UV-REMAINING-CI-JOBS: every Python CI job installs from uv.lock.

Only `tools-a-e` collects the code-health tests that invoke ruff and complexipy, so it alone
syncs the `lint` dependency group; every other job passes `--no-group lint`.
"""
import tomllib
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_JOBS = yaml.safe_load((_ROOT / ".github" / "workflows" / "test.yml").read_text())["jobs"]
_NO_PYTHON_INSTALL = {"changed-files", "frontend"}
_LINT_JOBS = {"tools-a-e"}


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
    assert lint == {"ruff", "complexipy"}
    assert not any(d.split("==")[0] in lint for d in groups["dev"])
    assert data["tool"]["uv"]["default-groups"] == ["dev", "lint"]
