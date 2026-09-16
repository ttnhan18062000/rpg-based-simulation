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
    # actions/setup-node@v4 added by TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP for the new
    # 'frontend' job -- a legitimate, expected new Action (mirrors deploy-docs.yml's existing
    # actions/setup-node@v4 usage), not scope creep on this ticket's own dependency guard.
    "actions/setup-node@v4",
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
  - frontend
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


def _pytest_steps(job: dict) -> list[dict]:
    """A job's own pytest-invocation step(s): either exactly one named 'Run' (the common shape,
    8 of 9 fastlane jobs), or several named 'Run: <path>' (TCK-20260916-CI-PER-DIRECTORY-STEPS-
    FOR-BLOCKED-LOGS split unit-infra's single combined step into one per test directory, each
    if: always(), so a failure names its own directory via step conclusions alone). Every check
    below that used to assume a single 'Run' step now aggregates across whichever shape a job
    actually has -- the invariants (junit-xml coverage, step ordering, head/base path parity)
    still apply in full, just computed over N steps where N can be greater than 1."""
    steps = [s for s in job["steps"] if s.get("name") == "Run" or (s.get("name") or "").startswith("Run: ")]
    assert steps, "expected a step named 'Run' (or one or more 'Run: <path>' steps) containing the pytest invocation"
    return steps


def _pytest_step(job: dict) -> dict:
    """Back-compat single-step accessor for jobs guaranteed to have exactly one pytest step."""
    steps = _pytest_steps(job)
    assert len(steps) == 1, "expected exactly one pytest step; use _pytest_steps() for a split job"
    return steps[0]


def _summary_step_index(job: dict) -> int:
    return next(
        (i for i, s in enumerate(job["steps"]) if s.get("name") == "Job summary"),
        -1,
    )


def _junit_xml_path(run_text: str) -> str:
    marker = "--junit-xml="
    idx = run_text.index(marker)
    rest = run_text[idx + len(marker):]
    return rest.split()[0].strip()


def _assert_job_has_junit_xml_flag(job_name: str, job: dict) -> None:
    for step in _pytest_steps(job):
        run_text = step.get("run") or ""
        assert "--junit-xml=" in run_text, (
            f"job {job_name!r} step {step.get('name')!r} pytest invocation is missing "
            "--junit-xml="
        )


def test_all_fastlane_jobs_have_junit_xml_flag() -> None:
    jobs = _jobs()
    for job_name in _FASTLANE_JOBS:
        _assert_job_has_junit_xml_flag(job_name, jobs[job_name])


def test_aggregated_junit_xml_flag_check_still_fails_on_a_split_job_missing_the_flag() -> None:
    # Hard requirement: an aggregating helper is exactly the shape that can silently accept
    # anything. Plant a synthetic unit-infra-shaped job (multiple "Run: <path>" steps) where one
    # step is missing --junit-xml, and confirm the check still fails -- proving the
    # generalization didn't turn this into a no-op for split jobs.
    synthetic_job = {
        "steps": [
            {"name": "Run: tests/unit/domains", "run": "pytest tests/unit/domains --junit-xml=reports/junit/x-domains.xml"},
            {"name": "Run: tests/unit/observability", "run": "pytest tests/unit/observability"},  # missing the flag
        ]
    }
    try:
        _assert_job_has_junit_xml_flag("synthetic-unit-infra", synthetic_job)
    except AssertionError:
        return
    raise AssertionError(
        "expected _assert_job_has_junit_xml_flag to fail on a split job with one step missing "
        "--junit-xml=, but it passed silently"
    )


def test_junit_xml_path_is_job_local_and_not_under_tests_dir() -> None:
    jobs = _jobs()
    all_paths: list[tuple[str, str, str]] = []  # (job_name, step_name, path)
    for job_name in _FASTLANE_JOBS:
        for step in _pytest_steps(jobs[job_name]):
            run_text = step.get("run") or ""
            path = _junit_xml_path(run_text)
            assert not path.startswith("tests/"), (
                f"job {job_name!r} step {step.get('name')!r}'s --junit-xml= path {path!r} "
                "starts with 'tests/' -- this would silently corrupt "
                "tools/gate_checks/ci_workflow_test_coverage.py's _extract_pytest_paths() "
                "directory-coverage tokenizer"
            )
            all_paths.append((job_name, step.get("name"), path))

    seen_paths = [p for (_, _, p) in all_paths]
    assert len(set(seen_paths)) == len(seen_paths), (
        f"expected a unique --junit-xml= path per pytest step across all fastlane jobs, "
        f"got {all_paths}"
    )


def test_all_fastlane_jobs_have_always_run_summary_step() -> None:
    jobs = _jobs()
    for job_name in _FASTLANE_JOBS:
        job = jobs[job_name]
        steps = job["steps"]
        pytest_indices = [i for i, s in enumerate(steps) if s in _pytest_steps(job)]
        pytest_index = max(pytest_indices)
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
        pytest_step_objs = _pytest_steps(job)
        pytest_index = max(i for i, s in enumerate(steps) if s in pytest_step_objs)
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

        _assert_head_base_path_parity(job_name, pytest_step_objs, run_text)


def _tests_tokens(text: str) -> set[str]:
    return {token.rstrip("\\") for token in text.split() if token.startswith("tests/")}


def _assert_head_base_path_parity(job_name: str, pytest_step_objs: list[dict], base_run_text: str) -> None:
    head_paths = {
        token
        for step in pytest_step_objs
        for token in _tests_tokens(step.get("run") or "")
    }
    base_paths = _tests_tokens(base_run_text)
    assert base_paths == head_paths, (
        f"job {job_name!r}'s base-branch collect-only path list {base_paths} must match "
        f"its head 'Run' step(s) path list {head_paths} for the two ID sets to be comparable"
    )


def test_aggregated_head_base_path_parity_check_still_fails_on_a_mismatched_split_job() -> None:
    # Hard requirement (same rationale as the junit-xml adversarial test above): plant a
    # synthetic split job whose aggregated head tests/ tokens differ from the base-branch
    # collect-only step's own token set, and confirm the parity check still fails.
    pytest_step_objs = [
        {"name": "Run: tests/unit/domains", "run": "pytest tests/unit/domains --junit-xml=x.xml"},
        {"name": "Run: tests/unit/observability", "run": "pytest tests/unit/observability --junit-xml=y.xml"},
    ]
    # Base side is missing tests/unit/observability -- a real drift the check must catch.
    base_run_text = "cd /tmp/base-checkout && pytest tests/unit/domains --collect-only -q"
    try:
        _assert_head_base_path_parity("synthetic-unit-infra", pytest_step_objs, base_run_text)
    except AssertionError:
        return
    raise AssertionError(
        "expected _assert_head_base_path_parity to fail when the aggregated head token set "
        "differs from the base-branch collect-only token set, but it passed silently"
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
    # 'frontend' (TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP) is a deliberate new job, added to
    # close a real CI coverage gap -- it joins the exempt set alongside migration-lanes/typecheck/
    # slow (all non-pytest or pytest-reporting-exempt jobs), not _FASTLANE_JOBS, since it runs
    # npm/vitest, not pytest, and has no --junit-xml/base-branch-collect-only wiring to match.
    # 'simq-grade-drift' (TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS) is another
    # deliberate new job, same rationale as 'frontend': closes a real gap (test_grade_regression.py's
    # anchor-comparison tests have silently pytest.skip()'d in every real CI run to date, since
    # nothing ever populated data/calibration/) by wiring already-built tooling
    # (`make simq-full-audit-full`) in as a `continue-on-error: true` informational job, mirroring
    # the existing 'typecheck' job's own exempt informational pattern -- not _FASTLANE_JOBS, since
    # it's deliberately non-blocking and has no --junit-xml/base-branch-collect-only wiring either.
    expected_job_names = set(_FASTLANE_JOBS) | {
        "changed-files",
        "perf-cert-arena",
        "migration-lanes",
        "typecheck",
        "slow",
        "frontend",
        "simq-grade-drift",
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
