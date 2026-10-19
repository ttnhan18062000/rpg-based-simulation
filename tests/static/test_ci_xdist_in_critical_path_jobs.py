"""Static guard for TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS.

The three critical-path jobs of `.github/workflows/test.yml` (Integration, Tools f-z, API/CLI/engine/logging) run their pytest steps in parallel with
pytest-xdist, inside the job, so the job count does not grow (the free plan allows 20 concurrent jobs and the Tests workflow already starts 21).
`--dist loadgroup` honours `xdist_group`. The one set that cannot run in parallel today, the visual_assets tests that take the real store lock
(issue #657), runs in its own serial step of the same job. No GitHub Actions execution is possible from pytest, so this reads the YAML.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOW = _ROOT / ".github" / "workflows" / "test.yml"
_PYPROJECT = _ROOT / "pyproject.toml"
XDIST_JOBS = ("integration", "tools-f-z", "api-cli-engine")
FLAGS = "-n auto --dist loadgroup"
SERIAL_STEP = "Run: tests/visual_assets (store lock, serial)"
MAX_JOB_COUNT = 21  # test.yml's job count when xdist was added: a ceiling, so removing a job is free and adding one needs a deliberate edit (free plan: 20 concurrent jobs)


def _jobs() -> dict:
    return yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _pytest_run_steps(job: dict) -> list[dict]:
    """The steps that run the tests: they start with `pytest` (the base-branch collect-only step runs `cd ... && pytest` and has --collect-only)."""
    return [s for s in job["steps"] if str(s.get("run", "")).lstrip().startswith("pytest") and "--collect-only" not in s["run"]]


def test_the_job_count_does_not_grow():
    assert len(_jobs()) <= MAX_JOB_COUNT, (
        f"test.yml has {len(_jobs())} jobs, over the {MAX_JOB_COUNT} it had when xdist was added (TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS): the free plan runs 20 jobs at once and Tests already "
        "starts more than that, so a new job queues behind the others. Parallelise inside a job instead, or raise MAX_JOB_COUNT deliberately."
    )


@pytest.mark.parametrize("job", XDIST_JOBS)
def test_every_pytest_step_of_a_critical_path_job_runs_under_xdist_except_the_serial_store_lock_step(job):
    steps = _pytest_run_steps(_jobs()[job])
    assert steps, job
    for step in steps:
        run = " ".join(step["run"].split())
        if step.get("name") == SERIAL_STEP:
            assert "-n " not in run and "xdist" not in run, "the store-lock step must stay serial"
        else:
            assert FLAGS in run, f"{job}: step {step.get('name')!r} must run with {FLAGS}"


def test_the_serial_store_lock_step_exists_only_in_the_api_job_and_the_parallel_step_ignores_exactly_its_paths():
    serial_paths = ("tests/visual_assets/store", "tests/visual_assets/test_review_cli.py", "tests/visual_assets/test_key_usage.py")
    jobs = _jobs()
    for name, job in jobs.items():
        has = any(s.get("name") == SERIAL_STEP for s in job["steps"])
        assert has == (name == "api-cli-engine"), name
    steps = {s.get("name"): " ".join(s["run"].split()) for s in _pytest_run_steps(jobs["api-cli-engine"])}
    for path in serial_paths:
        assert path in steps[SERIAL_STEP]
        assert f"--ignore={path}" in steps["Run: tests/visual_assets"]
    assert "--ignore=" not in steps[SERIAL_STEP]


def test_both_visual_assets_junit_files_reach_the_merged_report():
    merge = next(s for s in _jobs()["api-cli-engine"]["steps"] if s.get("name") == "Merge JUnit XML")["run"]
    assert "api-cli-engine-visual_assets.xml" in merge and "api-cli-engine-visual_assets-serial.xml" in merge


def test_pytest_xdist_is_a_dev_dependency_locked_in_uv_lock():
    assert "pytest-xdist" in _PYPROJECT.read_text(encoding="utf-8")
    assert 'name = "pytest-xdist"' in (_ROOT / "uv.lock").read_text(encoding="utf-8")
