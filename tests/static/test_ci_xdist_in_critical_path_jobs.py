"""Static guard for TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS, tightened by TCK-20261026-CI-DROP-THE-THREE-SERIAL-XDIST-STEPS.

The three critical-path jobs of `.github/workflows/test.yml` (Integration, Tools f-z, API/CLI/engine/logging) run EVERY pytest step in parallel with
pytest-xdist, inside the job, so the job count does not grow (the free plan allows 20 concurrent jobs and the Tests workflow already starts 21).
`--dist loadgroup` honours `xdist_group`. The two serial steps that once existed (the visual_assets store-lock step and the tools-f-z native-refusal /
simq-observation step) are gone because their owner fixes landed; this file pins that they stay gone. No GitHub Actions execution is possible from
pytest, so this reads the YAML.
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
REMOVED_SERIAL_STEPS = ("Run: tests/visual_assets (store lock, serial)", "Run: tests/tools (f–z, workflow-file test, serial)")
FORMERLY_SERIAL_PATHS = (
    "tests/visual_assets/store",
    "tests/visual_assets/test_review_cli.py",
    "tests/visual_assets/test_key_usage.py",
    "tests/tools/test_implement_ticket_native_refusal.py",
    "tests/tools/test_simq_long_run_observation.py",
)
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
def test_every_pytest_step_of_a_critical_path_job_runs_under_xdist(job):
    steps = _pytest_run_steps(_jobs()[job])
    assert steps, job
    for step in steps:
        assert FLAGS in " ".join(step["run"].split()), f"{job}: step {step.get('name')!r} must run with {FLAGS}"


def test_the_serial_steps_are_gone_and_no_ignore_for_their_files_remains():
    jobs = _jobs()
    for name, job in jobs.items():
        for step in job["steps"]:
            assert step.get("name") not in REMOVED_SERIAL_STEPS, f"{name}: serial step {step.get('name')!r} must not come back"
            assert "serial" not in str(step.get("name", "")).lower(), f"{name}: a serial step needs an owner ticket and a new pin, not a quiet add"
    text = _WORKFLOW.read_text(encoding="utf-8")
    for path in FORMERLY_SERIAL_PATHS:
        assert f"--ignore={path}" not in text, f"--ignore={path} must not return"


def test_the_formerly_serial_files_are_collected_by_their_jobs_parallel_step():
    jobs = _jobs()
    tools = " ".join(_pytest_run_steps(jobs["tools-f-z"])[0]["run"].split())
    assert "pytest tests/tools --ignore-glob='tests/tools/test_[a-e]*.py'" in tools and "--ignore=" not in tools
    visual = next(" ".join(s["run"].split()) for s in _pytest_run_steps(jobs["api-cli-engine"]) if s.get("name") == "Run: tests/visual_assets")
    assert visual.startswith("pytest tests/visual_assets ") and "--ignore" not in visual


def test_tools_f_z_writes_the_one_junit_file_directly_with_no_merge_step():
    job = _jobs()["tools-f-z"]
    assert not any(s.get("name") == "Merge JUnit XML" for s in job["steps"])
    (step,) = _pytest_run_steps(job)
    assert "--junit-xml=reports/junit/tools-f-z.xml" in " ".join(step["run"].split())


def test_the_visual_assets_junit_file_reaches_the_merged_report_alone():
    merge = next(s for s in _jobs()["api-cli-engine"]["steps"] if s.get("name") == "Merge JUnit XML")["run"]
    assert "api-cli-engine-visual_assets.xml" in merge and "visual_assets-serial" not in merge


def test_pytest_xdist_is_a_dev_dependency_locked_in_uv_lock():
    assert "pytest-xdist" in _PYPROJECT.read_text(encoding="utf-8")
    assert 'name = "pytest-xdist"' in (_ROOT / "uv.lock").read_text(encoding="utf-8")
