import re
from pathlib import Path

import yaml

# Static architecture guard for TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS: proves the
# always-on `changed-files` gate job and the `perf-cert-arena` / `migration-lanes` job-level
# `if:` conditions it drives are wired correctly in .github/workflows/test.yml -- structure,
# fail-safe-to-run branches, and (tests 8/9) that the hand-rolled trigger path sets still cover
# every src/ top-level dir those jobs' tests actually import, re-derived live rather than
# hardcoded, so future dependency drift is caught instead of silently becoming a false negative.
# Follows the tests/static/test_corpus_diversity_ci_isolation.py precedent: parse the workflow
# YAML with yaml.safe_load and assert on job/step dict structure and `run:` step text -- no live
# GitHub Actions execution is possible from pytest.
#
# TCK-20260906-CI-FRONTEND-PATH-FILTER extended the same gate mechanism with a third gated job,
# `frontend` -- a fully separate (TypeScript/npm) toolchain with no Python import graph, so its
# trigger path set (`frontend/` itself) needs no live-import derivation the way 8/9 do for the
# Python jobs; see test 12 below.

_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOW_PATH = _ROOT / ".github" / "workflows" / "test.yml"

_OUT_OF_SCOPE_JOBS = [
    "unit-core-world",
    "unit-gameplay",
    "unit-infra",
    "integration",
    "api-tools",
    "agent-orchestration",
    "simulation-quality",
    "arch-docs",
    "typecheck",
]

_EXPECTED_SLOW_IF = (
    "github.ref == 'refs/heads/main' || github.event_name == 'schedule' || "
    "github.event_name == 'workflow_dispatch'"
)
_EXPECTED_SLOW_NEEDS = [
    "unit-core-world",
    "unit-gameplay",
    "unit-infra",
    "integration",
    "api-tools",
    "agent-orchestration",
    "simulation-quality",
    "arch-docs",
    "frontend",
    "perf-cert-arena",
    "migration-lanes",
]

_MARKER_RE = re.compile(
    r"pytest\.mark\.(catalog|content_graph|worldassembly|registry_projection|scenario_setup|architecture)\b"
)
# Matches investigation.md's exact derivation command (`grep -rhoE "^from src\." ...`):
# column-0 `from src.<dir>` only, not `import src.` and not indented (function-body-local)
# imports. Function-local imports inside @pytest.mark.slow test bodies are deliberately not
# counted here -- lane-all-fast excludes `slow`-marked tests, so an import that only exists
# inside a slow-marked test function is not actually exercised by the fast lane this filter
# gates, and counting it would falsely inflate the required trigger path set.
_SRC_IMPORT_RE = re.compile(r"^from src\.([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE)


def _workflow() -> dict:
    return yaml.safe_load(_WORKFLOW_PATH.read_text())


def _jobs() -> dict:
    return _workflow()["jobs"]


def _gate_job_name(jobs: dict) -> str:
    needs = jobs["perf-cert-arena"].get("needs")
    assert needs, (
        "perf-cert-arena must declare a needs: list referencing the changed-files gate job "
        "-- cannot locate the gate job dynamically without it"
    )
    if isinstance(needs, str):
        return needs
    assert len(needs) == 1, f"expected perf-cert-arena to need exactly one gate job, got {needs!r}"
    return needs[0]


def _gate_job(jobs: dict) -> dict:
    return jobs[_gate_job_name(jobs)]


def _gate_run_text(jobs: dict) -> str:
    gate_job = _gate_job(jobs)
    diff_step = next(
        (step for step in gate_job["steps"] if step.get("id") == "diff"),
        None,
    )
    assert diff_step is not None, "changed-files gate job must have a step with id: diff"
    return diff_step.get("run") or ""


def _extract_re_pattern(run_text: str, var_name: str) -> str:
    match = re.search(rf"{var_name}='([^']*)'", run_text)
    assert match, f"{var_name} not found in changed-files gate job's run: text"
    return match.group(1)


def _imported_src_top_level_dirs(paths: list[Path]) -> set[str]:
    found: set[str] = set()
    files: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        files.extend(p.rglob("*.py") if p.is_dir() else [p])
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in _SRC_IMPORT_RE.finditer(text):
            found.add(m.group(1))
    return found


def _marker_tagged_test_files() -> list[Path]:
    tests_dir = _ROOT / "tests"
    matched = []
    for path in tests_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _MARKER_RE.search(text):
            matched.append(path)
    return matched


# 1. All 3 in-scope jobs actually gained a truthy `if:` condition.
def test_perf_cert_arena_and_migration_lanes_have_if_conditions() -> None:
    jobs = _jobs()
    assert jobs["perf-cert-arena"].get("if"), "perf-cert-arena must have a truthy 'if' condition"
    assert jobs["migration-lanes"].get("if"), "migration-lanes must have a truthy 'if' condition"
    assert jobs["frontend"].get("if"), "frontend must have a truthy 'if' condition"


# 2. Primary anti-scope-creep guard: none of the 9 out-of-scope jobs gained an `if:`.
def test_no_other_fast_lane_job_gained_an_if_condition() -> None:
    jobs = _jobs()
    for job_name in _OUT_OF_SCOPE_JOBS:
        assert job_name in jobs, f"expected job {job_name!r} to still exist"
        assert "if" not in jobs[job_name], (
            f"job {job_name!r} is out of scope for this ticket but gained an 'if' condition "
            f"({jobs[job_name].get('if')!r})"
        )


# 3. slow job's if:/needs: are byte-identical to the pre-ticket values.
def test_slow_job_if_condition_is_unchanged() -> None:
    jobs = _jobs()
    slow = jobs["slow"]
    assert slow["if"] == _EXPECTED_SLOW_IF, (
        f"slow job's 'if' condition changed -- expected {_EXPECTED_SLOW_IF!r}, got {slow['if']!r}"
    )
    assert slow["needs"] == _EXPECTED_SLOW_NEEDS, (
        f"slow job's 'needs' list changed -- expected {_EXPECTED_SLOW_NEEDS!r}, got {slow['needs']!r}"
    )


# 4. The gate job itself (located dynamically via perf-cert-arena's needs:) must have no `if:`.
def test_changed_files_gate_job_has_no_if_condition() -> None:
    jobs = _jobs()
    gate_job = _gate_job(jobs)
    assert "if" not in gate_job, (
        "the changed-files gate job must never have its own 'if' condition -- it would "
        "cascade-skip both perf-cert-arena and migration-lanes via the needs-success mechanism"
    )


# 5a. perf-cert-arena's if: references the gate job's own output.
def test_perf_cert_arena_if_references_changed_files_gate_output() -> None:
    jobs = _jobs()
    condition = jobs["perf-cert-arena"]["if"]
    assert "needs." in condition
    assert ".outputs." in condition
    assert "run_perf_cert_arena" in condition


# 5b. migration-lanes' if: references its own distinct output.
def test_migration_lanes_if_references_changed_files_gate_output() -> None:
    jobs = _jobs()
    condition = jobs["migration-lanes"]["if"]
    assert "needs." in condition
    assert ".outputs." in condition
    assert "run_migration_lanes" in condition


# 5c. frontend's if: references its own distinct output (TCK-20260906-CI-FRONTEND-PATH-FILTER).
def test_frontend_if_references_changed_files_gate_output() -> None:
    jobs = _jobs()
    condition = jobs["frontend"]["if"]
    assert "needs." in condition
    assert ".outputs." in condition
    assert "run_frontend" in condition


# 6. Non-pull_request events force both outputs true before any git diff is attempted.
def test_gate_job_fails_open_on_non_pull_request_events() -> None:
    jobs = _jobs()
    run_text = _gate_run_text(jobs)
    non_pr_branch_index = run_text.find("!= \"pull_request\"")
    if non_pr_branch_index == -1:
        non_pr_branch_index = run_text.find("!= 'pull_request'")
    assert non_pr_branch_index != -1, (
        "expected an explicit github.event_name != 'pull_request' branch in the gate job's "
        "run: text"
    )
    diff_index = run_text.find("git diff")
    assert diff_index != -1, "expected a git diff invocation in the gate job's run: text"
    assert non_pr_branch_index < diff_index, (
        "the non-pull_request event check must run and exit before any git diff is attempted"
    )
    branch_text = run_text[non_pr_branch_index:diff_index]
    assert "run_perf_cert_arena=true" in branch_text
    assert "run_migration_lanes=true" in branch_text
    assert "run_frontend=true" in branch_text
    assert "exit 0" in branch_text


# 7. A failing git diff command also forces both outputs true and exits 0 (not job failure).
def test_gate_job_fails_open_on_diff_command_failure() -> None:
    jobs = _jobs()
    run_text = _gate_run_text(jobs)
    assert "if ! CHANGED=$(git diff" in run_text, (
        "expected the git diff invocation to be guarded with 'if ! CHANGED=$(git diff ...)' "
        "so a non-zero exit is distinguished from a successful empty diff"
    )
    failure_branch_match = re.search(
        r"if ! CHANGED=\$\(git diff.*?\bfi\b", run_text, re.DOTALL
    )
    assert failure_branch_match, "could not locate the diff-failure branch body"
    branch_text = failure_branch_match.group(0)
    assert "run_perf_cert_arena=true" in branch_text
    assert "run_migration_lanes=true" in branch_text
    assert "run_frontend=true" in branch_text
    assert "exit 0" in branch_text


# 8. perf-cert-arena's trigger path set covers every src/ top-level dir its tests actually
# import, re-derived live from tests/perf, tests/certification, tests/arena rather than
# hardcoded -- catches future dependency drift instead of silently becoming a false negative.
def test_perf_cert_arena_path_set_covers_all_actually_imported_src_dirs() -> None:
    imported = _imported_src_top_level_dirs(
        [_ROOT / "tests" / "perf", _ROOT / "tests" / "certification", _ROOT / "tests" / "arena"]
    )
    assert imported, "expected at least one src/ import in tests/perf, tests/certification, tests/arena"

    jobs = _jobs()
    run_text = _gate_run_text(jobs)
    perf_pattern = _extract_re_pattern(run_text, "PERF_RE")

    missing = sorted(d for d in imported if d not in perf_pattern)
    assert not missing, (
        f"perf-cert-arena's trigger path set (PERF_RE) is missing coverage for src/ dirs "
        f"actually imported by tests/perf, tests/certification, tests/arena: {missing} -- "
        f"update PERF_RE in .github/workflows/test.yml's changed-files gate job"
    )


# 9. migration-lanes' trigger path set covers every src/ top-level dir imported by the
# marker-tagged (catalog/content_graph/worldassembly/registry_projection/scenario_setup/
# architecture) test files, re-derived live, plus test_expansion_gate.py's imports (it is not
# marker-tagged but is run by gate-expansion in the same job via a hardcoded file path).
def test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies() -> None:
    marker_files = _marker_tagged_test_files()
    assert marker_files, "expected at least one marker-tagged test file under tests/"

    expansion_gate_file = (
        _ROOT / "tests" / "integration" / "content" / "test_expansion_gate.py"
    )
    assert expansion_gate_file.exists(), "test_expansion_gate.py not found"

    imported = _imported_src_top_level_dirs(marker_files + [expansion_gate_file])
    assert imported, "expected at least one src/ import across the marker-tagged test files"

    jobs = _jobs()
    run_text = _gate_run_text(jobs)
    mig_pattern = _extract_re_pattern(run_text, "MIG_RE")

    missing = sorted(d for d in imported if d not in mig_pattern)
    assert not missing, (
        f"migration-lanes' trigger path set (MIG_RE) is missing coverage for src/ dirs "
        f"actually imported by the marker-tagged tests and test_expansion_gate.py: {missing} -- "
        f"update MIG_RE in .github/workflows/test.yml's changed-files gate job"
    )


# 10. (Added at Review, closes AC #4 gap) A gate-job failure/non-success -- not just a clean
# run_X == 'false' result -- must still allow the downstream job to run.
def test_gated_jobs_fail_open_on_gate_job_non_success() -> None:
    jobs = _jobs()
    for job_name, output_key in (
        ("perf-cert-arena", "run_perf_cert_arena"),
        ("migration-lanes", "run_migration_lanes"),
        ("frontend", "run_frontend"),
    ):
        condition = jobs[job_name]["if"]
        assert "!cancelled()" in condition, (
            f"{job_name}'s 'if' must include !cancelled() alongside the custom boolean, since "
            "overriding the default success()-AND-on-needs behavior requires explicitly "
            "restating cancelled/failure handling"
        )
        assert "needs.changed-files.result != 'success'" in condition, (
            f"{job_name}'s 'if' must OR in a needs.changed-files.result != 'success' clause so "
            "a gate-job failure (not just a clean false result) still forces this job to run"
        )
        assert output_key in condition


# 11. (Added at Review, closes the two-dot/three-dot diff gap) The diff must use three-dot
# range semantics or an explicit merge-base, not a plain two-dot diff against base.sha.
def test_gate_job_diff_uses_three_dot_range() -> None:
    jobs = _jobs()
    run_text = _gate_run_text(jobs)
    three_dot = 'git diff --name-only "$BASE...$HEAD"' in run_text
    merge_base = "git merge-base" in run_text
    assert three_dot or merge_base, (
        "expected the gate job's diff to use three-dot range semantics "
        '(git diff --name-only "$BASE...$HEAD") or an explicit git merge-base call -- a plain '
        "two-dot diff against base.sha would pick up files changed on main after the PR "
        "branched but never touched by the PR itself"
    )
    two_dot_plain = re.search(r'git diff --name-only "\$BASE" "\$HEAD"', run_text)
    assert two_dot_plain is None, (
        "found a plain two-dot 'git diff --name-only \"$BASE\" \"$HEAD\"' -- must be three-dot "
        "range or an explicit merge-base, not a plain two-dot diff against the base branch's "
        "current tip"
    )


# 12. (TCK-20260906-CI-FRONTEND-PATH-FILTER) frontend's trigger path set covers its own directory
# and the workflow file. Unlike tests 8/9, this needs no live-import derivation -- frontend/ is a
# separate (TypeScript/npm) toolchain with no Python import graph, so its dependency set is
# definitionally the directory itself, not something to re-derive from src/ imports.
def test_frontend_path_set_covers_frontend_directory_and_workflow_file() -> None:
    jobs = _jobs()
    run_text = _gate_run_text(jobs)
    frontend_pattern = _extract_re_pattern(run_text, "FRONTEND_RE")

    assert "frontend/" in frontend_pattern, (
        f"frontend's trigger path set (FRONTEND_RE) must cover the frontend/ directory itself: "
        f"{frontend_pattern!r}"
    )
    assert r"\.github/workflows/test\.yml" in frontend_pattern, (
        f"frontend's trigger path set (FRONTEND_RE) must cover .github/workflows/test.yml itself "
        f"(editing the workflow must always re-run every gated job): {frontend_pattern!r}"
    )
