"""Static architecture guard for TCK-20260823-CI-STEP-SUMMARY-REPORTING: proves the
`--junit-xml=` flag and the `if: always()` job-summary step are wired correctly into each of the
9 fast-lane jobs in `.github/workflows/test.yml`, that no new dependency or marketplace Action
was introduced, and that the `slow`/`migration-lanes` jobs (explicitly deferred, see
staging_artifacts/TCK-20260823-CI-STEP-SUMMARY-REPORTING/plan.md "Decisions Made by This Plan")
stay untouched.

Follows the established `yaml.safe_load` + dict/text-assertion pattern used by
`tests/static/test_ci_narrow_path_filtered_jobs.py` -- no live GitHub Actions execution is
possible from pytest.
"""

from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOW_PATH = _ROOT / ".github" / "workflows" / "test.yml"
_REQUIREMENTS_PATH = _ROOT / "requirements.txt"

_FASTLANE_JOBS = [
    "unit-core-world",
    "unit-gameplay",
    "unit-infra",
    "integration",
    "api-tools",
    "agent-orchestration",
    "simulation-quality",
    "arch-docs",
    "perf-cert-arena",
]

_PRE_EXISTING_USES = {
    "actions/checkout@v5",
    "actions/setup-python@v6",
    "actions/upload-artifact@v4",
}

_BANNED_REQUIREMENTS_ENTRIES = ("pytest-cov", "pytest-html")
_BANNED_MARKETPLACE_ACTION_SUBSTRINGS = ("dorny/test-reporter", "EnricoMi/publish-unit-test-result-action")

_EXPECTED_MIGRATION_LANES_YAML = """
name: "Migration lanes"
runs-on: ubuntu-latest
needs: [changed-files]
if: ${{ !cancelled() && (needs.changed-files.result != 'success' || needs.changed-files.outputs.run_migration_lanes == 'true') }}
steps:
  - uses: actions/checkout@v5
  - uses: actions/setup-python@v6
    with: { python-version: "3.13", cache: pip }
  - run: pip install -r requirements.txt
  - name: Fast lanes
    run: make lane-all-fast
  - name: Expansion gate
    run: make gate-expansion
"""

_EXPECTED_SLOW_YAML = """
name: "Slow regression"
runs-on: ubuntu-latest
if: github.ref == 'refs/heads/main' || github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
needs:
  - unit-core-world
  - unit-gameplay
  - unit-infra
  - integration
  - api-tools
  - agent-orchestration
  - simulation-quality
  - arch-docs
  - perf-cert-arena
  - migration-lanes
steps:
  - uses: actions/checkout@v5
  - uses: actions/setup-python@v6
    with: { python-version: "3.13", cache: pip }
  - run: pip install -r requirements.txt
  - name: Slow tests — corpus diversity (isolated per-test, TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE)
    run: make simq-corpus-diversity-slow-isolated
  - name: Slow tests (includes 5k behavioral regression)
    run: |
      pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q --ignore=tests/unit/worldassembly/test_corpus_diversity.py
  - name: Legacy regression
    run: make lane-legacy-regression
  - name: Upload certification report
    uses: actions/upload-artifact@v4
    if: always()
    with:
      name: certification-report-${{ github.sha }}
      path: reports/certification/
      retention-days: 30
"""


def _workflow() -> dict:
    return yaml.safe_load(_WORKFLOW_PATH.read_text())


def _jobs() -> dict:
    return _workflow()["jobs"]


def _pytest_step(job: dict) -> dict:
    step = next((s for s in job["steps"] if s.get("name") == "Run"), None)
    assert step is not None, "expected a step named 'Run' containing the pytest invocation"
    return step


def _summary_step_index(job: dict) -> int:
    return next(
        (i for i, s in enumerate(job["steps"]) if s.get("name") == "Job summary"),
        -1,
    )


def test_all_fastlane_jobs_have_junit_xml_flag() -> None:
    jobs = _jobs()
    for job_name in _FASTLANE_JOBS:
        run_text = _pytest_step(jobs[job_name]).get("run") or ""
        assert "--junit-xml=" in run_text, (
            f"job {job_name!r} pytest invocation is missing --junit-xml="
        )


def test_junit_xml_path_is_job_local_and_not_under_tests_dir() -> None:
    jobs = _jobs()
    paths_by_job: dict[str, str] = {}
    for job_name in _FASTLANE_JOBS:
        run_text = _pytest_step(jobs[job_name]).get("run") or ""
        marker = "--junit-xml="
        idx = run_text.index(marker)
        rest = run_text[idx + len(marker):]
        path = rest.split()[0].strip()
        assert not path.startswith("tests/"), (
            f"job {job_name!r}'s --junit-xml= path {path!r} starts with 'tests/' -- this would "
            "silently corrupt tools/gate_checks/ci_workflow_test_coverage.py's "
            "_extract_pytest_paths() directory-coverage tokenizer"
        )
        paths_by_job[job_name] = path

    assert len(set(paths_by_job.values())) == len(paths_by_job), (
        f"expected a unique --junit-xml= path per job, got {paths_by_job}"
    )


def test_all_fastlane_jobs_have_always_run_summary_step() -> None:
    jobs = _jobs()
    for job_name in _FASTLANE_JOBS:
        job = jobs[job_name]
        steps = job["steps"]
        pytest_index = next(i for i, s in enumerate(steps) if s.get("name") == "Run")
        summary_index = _summary_step_index(job)
        assert summary_index != -1, f"job {job_name!r} has no 'Job summary' step"
        assert summary_index > pytest_index, (
            f"job {job_name!r}'s 'Job summary' step must come after its 'Run' (pytest) step"
        )
        summary_step = steps[summary_index]
        assert summary_step.get("if") == "always()", (
            f"job {job_name!r}'s 'Job summary' step must have if: always()"
        )
        run_text = summary_step.get("run") or ""
        assert "tools/ci_junit_summary.py" in run_text
        assert "$GITHUB_STEP_SUMMARY" in run_text
        assert "/tmp/base-collect.txt" in run_text, (
            f"job {job_name!r}'s 'Job summary' step must pass /tmp/base-collect.txt as the "
            "third argument -- its absence on non-PR runs is itself the fallback mechanism"
        )


def test_no_new_requirements_txt_entry_and_no_new_marketplace_action() -> None:
    requirements_text = _REQUIREMENTS_PATH.read_text()
    for banned in _BANNED_REQUIREMENTS_ENTRIES:
        assert banned not in requirements_text, (
            f"requirements.txt must not gain a {banned!r} entry for this ticket -- "
            "--junit-xml is pytest's own built-in flag, no new dependency is needed"
        )

    workflow_text = _WORKFLOW_PATH.read_text()
    for banned in _BANNED_MARKETPLACE_ACTION_SUBSTRINGS:
        assert banned not in workflow_text, (
            f".github/workflows/test.yml must not reference the marketplace Action {banned!r} "
            "-- only plain shell/Python writing to $GITHUB_STEP_SUMMARY is in scope"
        )

    jobs = _jobs()
    all_uses: set[str] = set()
    for job in jobs.values():
        for step in job.get("steps", []):
            uses = step.get("uses")
            if uses:
                all_uses.add(uses)

    unexpected = all_uses - _PRE_EXISTING_USES
    assert not unexpected, (
        f"found unexpected new 'uses:' Action(s) in test.yml: {unexpected} -- only "
        f"{_PRE_EXISTING_USES} were expected"
    )


def test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket() -> None:
    jobs = _jobs()
    expected_migration_lanes = yaml.safe_load(_EXPECTED_MIGRATION_LANES_YAML)
    expected_slow = yaml.safe_load(_EXPECTED_SLOW_YAML)

    assert jobs["migration-lanes"] == expected_migration_lanes, (
        "migration-lanes job changed -- this ticket explicitly defers --junit-xml/summary "
        "reporting for this job (see plan.md 'Decisions Made by This Plan')"
    )
    assert jobs["slow"] == expected_slow, (
        "slow job changed -- this ticket explicitly defers --junit-xml/summary reporting for "
        "this job (see plan.md 'Decisions Made by This Plan')"
    )


# ── TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT: base-branch collect-only wiring ──────────────


def _fetch_step(job: dict) -> dict:
    step = next(
        (s for s in job["steps"] if s.get("name") == "Fetch base branch for collect-only diff"),
        None,
    )
    assert step is not None, "expected a step named 'Fetch base branch for collect-only diff'"
    return step


def _collection_step(job: dict) -> dict:
    step = next(
        (s for s in job["steps"] if s.get("name") == "Base branch test collection"),
        None,
    )
    assert step is not None, "expected a step named 'Base branch test collection'"
    return step


def test_all_fastlane_jobs_have_base_branch_collect_only_step() -> None:
    jobs = _jobs()
    for job_name in _FASTLANE_JOBS:
        job = jobs[job_name]
        steps = job["steps"]
        pytest_index = next(i for i, s in enumerate(steps) if s.get("name") == "Run")
        fetch_index = next(
            i
            for i, s in enumerate(steps)
            if s.get("name") == "Fetch base branch for collect-only diff"
        )
        collection_index = next(
            i for i, s in enumerate(steps) if s.get("name") == "Base branch test collection"
        )
        summary_index = _summary_step_index(job)

        assert fetch_index > pytest_index, (
            f"job {job_name!r}'s base-branch fetch step must come after its 'Run' step"
        )
        assert collection_index > fetch_index, (
            f"job {job_name!r}'s base-branch collection step must come after its fetch step"
        )
        assert summary_index > collection_index, (
            f"job {job_name!r}'s 'Job summary' step must come after the base-branch collection step"
        )

        fetch_step = _fetch_step(job)
        assert fetch_step.get("if") == "github.event_name == 'pull_request'", (
            f"job {job_name!r}'s base-branch fetch step must be gated on pull_request events only"
        )
        assert "git fetch origin" in (fetch_step.get("run") or "")
        assert "git worktree add" in (fetch_step.get("run") or "")

        collection_step = _collection_step(job)
        assert collection_step.get("if") == "github.event_name == 'pull_request'", (
            f"job {job_name!r}'s base-branch collection step must be gated on pull_request events only"
        )
        run_text = collection_step.get("run") or ""
        assert "--collect-only" in run_text
        assert "-m \"not slow and not extra_slow\"" in run_text
        assert "/tmp/base-collect.txt" in run_text

        head_path_list = _pytest_step(job).get("run") or ""
        head_paths = {
            token.rstrip("\\")
            for token in head_path_list.split()
            if token.startswith("tests/")
        }
        base_paths = {
            token.rstrip("\\") for token in run_text.split() if token.startswith("tests/")
        }
        assert base_paths == head_paths, (
            f"job {job_name!r}'s base-branch collect-only path list {base_paths} must match "
            f"its head 'Run' step's path list {head_paths} for the two ID sets to be comparable"
        )


def test_base_branch_collect_only_step_run_text_not_tokenized_by_pytest_path_guard() -> None:
    jobs = _jobs()
    for job_name in _FASTLANE_JOBS:
        job = jobs[job_name]
        collection_step = _collection_step(job)
        run_text = collection_step.get("run") or ""
        for line in run_text.splitlines():
            stripped = line.strip()
            assert stripped != "pytest", (
                f"job {job_name!r}'s base-branch collection step has a bare 'pytest' line -- "
                "this would be independently tokenized by "
                "tools/gate_checks/ci_workflow_test_coverage.py::_extract_pytest_paths"
            )
            assert not stripped.startswith("pytest "), (
                f"job {job_name!r}'s base-branch collection step has a bare 'pytest ...' line -- "
                "must be prefixed with a non-pytest shell construct (e.g. 'cd ... && pytest ...')"
            )
            assert not stripped.startswith("pytest\\"), (
                f"job {job_name!r}'s base-branch collection step has a bare backslash-continued "
                "'pytest\\' line -- must be prefixed with a non-pytest shell construct"
            )
        assert "cd /tmp/base-checkout && pytest" in run_text, (
            f"job {job_name!r}'s base-branch collection step must invoke pytest via a "
            "'cd /tmp/base-checkout && pytest ...' prefix, never a bare 'pytest ...' line"
        )


def test_new_steps_gated_on_pull_request_event_only() -> None:
    jobs = _jobs()
    for job_name in _FASTLANE_JOBS:
        job = jobs[job_name]
        for step_name in (
            "Fetch base branch for collect-only diff",
            "Base branch test collection",
        ):
            step = next(s for s in job["steps"] if s.get("name") == step_name)
            assert step.get("if") == "github.event_name == 'pull_request'", (
                f"job {job_name!r}'s {step_name!r} step must be gated on pull_request events "
                "only, so push/schedule/workflow_dispatch runs never produce a base-collect "
                "file and fall back cleanly to the existing single-row summary"
            )


def test_no_cross_job_aggregate_step_or_job_added() -> None:
    expected_job_names = set(_FASTLANE_JOBS) | {
        "changed-files",
        "perf-cert-arena",
        "migration-lanes",
        "typecheck",
        "slow",
    }
    assert set(_jobs().keys()) == expected_job_names, (
        "job set changed -- this ticket must not add a new CI job (no cross-job aggregate "
        "new-vs-existing summary is in scope, per the ticket's Out of Scope bullet)"
    )


def test_no_new_requirements_txt_entry_for_new_existing_split() -> None:
    # The base-branch collection mechanism is git/pytest shell plus stdlib-only Python
    # classification logic -- re-running the parent ticket's existing assertion is sufficient
    # coverage since this ticket adds no new 'uses:' step and no new dependency.
    test_no_new_requirements_txt_entry_and_no_new_marketplace_action()
