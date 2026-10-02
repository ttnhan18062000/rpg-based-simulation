"""Tests for the three-way split of the former `api-tools` CI job (TCK-20261003-CI-SPLIT-API-TOOLS-JOB).

The split cuts tests/tools in two by file name with complementary --ignore-glob patterns and puts the
other directories in a third job. These tests pin the properties that make that safe: the old job is
gone, the three jobs exist and report like their predecessor, the two globs partition tests/tools so
no file can be skipped, a file matching neither glob still runs, and the coverage parser does not
mistake a glob word for a covered path.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.ci_workflow_test_coverage import parse_job_pytest_paths  # noqa: E402

_WORKFLOW = _ROOT / ".github" / "workflows" / "test.yml"
_TOOLS_JOBS = {"tools-a-e": "tests/tools/test_[f-z]*.py", "tools-f-z": "tests/tools/test_[a-e]*.py"}
_NEW_JOBS = ("tools-a-e", "tools-f-z", "api-cli-engine")
_OTHER_DIRS = ("api", "cli", "logging", "engine", "observability", "visual_assets")


def _jobs() -> dict:
    return yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _run_steps(job: dict) -> list[dict]:
    return [s for s in job["steps"] if (s.get("name") or "").startswith("Run: ")]


def test_the_old_job_is_gone_and_the_three_new_jobs_exist():
    jobs = _jobs()
    assert "api-tools" not in jobs
    for name in _NEW_JOBS:
        assert name in jobs


def test_the_slow_job_waits_for_all_three_and_not_the_old_one():
    needs = _jobs()["slow"]["needs"]
    assert "api-tools" not in needs
    assert all(name in needs for name in _NEW_JOBS)


@pytest.mark.parametrize(("job", "ignored"), _TOOLS_JOBS.items())
def test_each_tools_job_runs_tests_tools_with_the_other_halfs_glob_ignored(job, ignored):
    (step,) = _run_steps(_jobs()[job])
    run = step["run"]
    assert "pytest tests/tools " in run
    assert f"--ignore-glob='{ignored}'" in run
    assert '-m "not slow and not extra_slow"' in run
    base = next(s for s in _jobs()[job]["steps"] if s.get("name") == "Base branch test collection")["run"]
    assert f"--ignore-glob='{ignored}'" in base, "the base-branch collection must use the same ignore glob"


def test_the_two_globs_are_complementary_so_no_file_can_be_skipped():
    """Each tools job ignores exactly the other's letter range: a file is never ignored by both."""
    ignored_by = {job: glob for job, glob in _TOOLS_JOBS.items()}
    # a-e job ignores f-z and vice versa
    assert ignored_by["tools-a-e"].endswith("test_[f-z]*.py")
    assert ignored_by["tools-f-z"].endswith("test_[a-e]*.py")
    names = sorted(p.name for p in (_ROOT / "tests" / "tools").glob("test_*.py"))
    assert names, "expected test files under tests/tools"
    for name in names:
        first = name[len("test_")]
        in_a_e, in_f_z = "a" <= first <= "e", "f" <= first <= "z"
        assert in_a_e or in_f_z, f"{name} matches neither glob; it would run in both jobs"
        assert not (in_a_e and in_f_z)


def test_the_api_job_keeps_the_per_directory_steps_and_merges_their_junit():
    job = _jobs()["api-cli-engine"]
    assert [s["name"] for s in _run_steps(job)] == [f"Run: tests/{d}" for d in _OTHER_DIRS]
    assert all(s.get("if") == "always()" for s in _run_steps(job))
    merge = next(s for s in job["steps"] if s.get("name") == "Merge JUnit XML")
    assert "reports/junit/api-cli-engine.xml" in merge["run"]
    for d in _OTHER_DIRS:
        assert f"api-cli-engine-{d}.xml" in merge["run"]


@pytest.mark.parametrize("job", _NEW_JOBS)
def test_each_new_job_keeps_the_reporting_the_old_job_had(job):
    steps = {s.get("name"): s for s in _jobs()[job]["steps"]}
    assert steps["Upload JUnit XML"]["if"] == "always()"
    assert steps["Upload JUnit XML"]["with"]["name"].startswith(f"{job}-junit-")
    assert steps["Job summary"]["if"] == "always()"
    assert f'"{job}"' in steps["Job summary"]["run"] and "/tmp/base-collect.txt" in steps["Job summary"]["run"]
    assert steps["Fetch base branch for collect-only diff"]["if"] == "github.event_name == 'pull_request'"
    assert steps["Base branch test collection"]["if"] == "github.event_name == 'pull_request'"


def test_every_new_job_still_installs_with_pip_until_the_uv_migration():
    for job in _NEW_JOBS:
        runs = [s.get("run") for s in _jobs()[job]["steps"]]
        assert "pip install -r requirements.txt" in runs


def test_the_coverage_parser_reads_tests_tools_for_both_tools_jobs_and_ignores_the_glob_word():
    paths = parse_job_pytest_paths(_WORKFLOW.read_text(encoding="utf-8"))
    for job in _TOOLS_JOBS:
        assert paths[job] == {"tests/tools"}, "a --ignore-glob word must not be collected as a covered path"
    assert paths["api-cli-engine"] == {f"tests/{d}" for d in _OTHER_DIRS}


def test_the_parser_does_not_collect_an_ignore_glob_word_in_a_synthetic_job():
    text = (
        "jobs:\n"
        "  demo:\n"
        "    steps:\n"
        "      - name: Run\n"
        "        run: |\n"
        "          pytest tests/tools --ignore-glob='tests/tools/test_[f-z]*.py' -q\n"
    )
    assert parse_job_pytest_paths(text)["demo"] == {"tests/tools"}


def test_a_file_matching_neither_glob_runs_in_both_tools_jobs(tmp_path):
    """Run the two real ignore globs against a scratch tests/tools: a name outside a-z still runs."""
    tools = tmp_path / "tests" / "tools"
    tools.mkdir(parents=True)
    for name in ("test_alpha.py", "test_zulu.py", "test_9digits.py", "test_Upper.py"):
        (tools / name).write_text("def test_it():\n    pass\n")

    def collected(glob: str) -> set[str]:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/tools", f"--ignore-glob={glob}", "--collect-only", "-q",
             "-p", "no:cacheprovider"],
            cwd=tmp_path, capture_output=True, text=True, check=False,
        ).stdout
        return {line.split("::")[0].rsplit("/", 1)[-1] for line in out.splitlines() if "::" in line}

    a_e = collected(_TOOLS_JOBS["tools-a-e"])
    f_z = collected(_TOOLS_JOBS["tools-f-z"])
    assert a_e == {"test_alpha.py", "test_9digits.py", "test_Upper.py"}
    assert f_z == {"test_zulu.py", "test_9digits.py", "test_Upper.py"}
    assert a_e | f_z == {"test_alpha.py", "test_zulu.py", "test_9digits.py", "test_Upper.py"}


def _doubled_backslash_lines(text: str) -> list[int]:
    """1-based numbers of lines that end in two backslashes (see the test below for why that is a bug)."""
    return [n for n, line in enumerate(text.splitlines(), start=1) if line.rstrip().endswith("\\\\")]


def test_no_workflow_line_ends_in_a_doubled_backslash():
    """Inside a `run: |` block two trailing backslashes are one escaped backslash and a real newline,
    so the next line runs as its own command and the step fails."""
    bad = _doubled_backslash_lines(_WORKFLOW.read_text(encoding="utf-8"))
    assert not bad, f"doubled trailing backslash on test.yml line(s) {bad}"


def _joined_command(script: str) -> list[str]:
    """The words of the script's single shell command after joining backslash continuations."""
    return shlex.split(script.replace("\\\n", " "))


def test_the_merge_step_lists_exactly_the_xml_files_the_run_steps_write():
    job = _jobs()["api-cli-engine"]
    written = []
    for step in _run_steps(job):
        words = _joined_command(step["run"])
        written.append(next(w.split("=", 1)[1] for w in words if w.startswith("--junit-xml=")))
    merge = next(s for s in job["steps"] if s.get("name") == "Merge JUnit XML")
    words = _joined_command(merge["run"])
    assert words[:2] == ["python3", "tools/ci_junit_merge.py"]
    out = words[words.index("--out") + 1]
    inputs = [w for w in words[2:] if w.startswith("reports/") and w != out]
    assert out == "reports/junit/api-cli-engine.xml"
    assert inputs == written, "the merge must take exactly the per-directory XML files, in order"
    assert len(words) == 2 + 2 + len(written), "no stray argument such as a lone backslash"


def test_the_doubled_backslash_detector_flags_the_broken_form_and_passes_the_good_one():
    good = "python3 merge.py --out o.xml \\\n    a.xml \\\n    b.xml\n"
    broken = "python3 merge.py --out o.xml \\\n    a.xml \\\\\n    b.xml\n"
    assert _doubled_backslash_lines(good) == []
    assert _doubled_backslash_lines(broken) == [2]
