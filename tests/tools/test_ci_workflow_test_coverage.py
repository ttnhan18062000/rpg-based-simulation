"""Tests for tools/gate_checks/ci_workflow_test_coverage.py
(TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK).

Coverage-honesty requirement (see tests/tools/test_workflow_meta_conformance.py's own docstring,
the established convention this ticket follows): every check function below has at least one
fixture proving it catches a real violation it claims to catch, not just that it runs on the
happy path.
"""

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import gate_checks.ci_workflow_test_coverage as ci_workflow_test_coverage  # noqa: E402
from gate_checks.ci_workflow_test_coverage import (  # noqa: E402
    check_ci_workflow_test_coverage,
    directories_from_test_files,
    directory_is_covered_by_file_listings,
    directory_is_excluded_from_pytest_collection,
    directory_is_slow_only_legitimate,
    file_is_fully_slow_marked,
    is_directory_covered,
    parse_job_pytest_paths,
    pytest_norecursedirs,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_REAL_WORKFLOW_PATH = _REPO_ROOT / ".github" / "workflows" / "test.yml"


# ---------------------------------------------------------------------------
# parse_job_pytest_paths — real, live workflow file (not a fixture copy)
# ---------------------------------------------------------------------------


def test_parses_real_workflow_fastlane_job_paths():
    job_paths = parse_job_pytest_paths(_REAL_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert "tests/unit/core" in job_paths["unit-core-world"]
    assert "tests/unit/domains" in job_paths["unit-infra"]
    assert "tests/integration" in job_paths["integration"]
    assert "tests/tools" in job_paths["api-tools"]


def test_parses_real_workflow_slow_job_blanket():
    job_paths = parse_job_pytest_paths(_REAL_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert "tests" in job_paths["slow"]


def test_ignore_flag_token_is_not_collected_as_a_covered_path():
    job_paths = parse_job_pytest_paths(_REAL_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert "tests/unit/worldassembly/test_corpus_diversity.py" not in job_paths["slow"]


def test_non_pytest_jobs_contribute_no_paths():
    job_paths = parse_job_pytest_paths(_REAL_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert job_paths["typecheck"] == set()
    assert job_paths["changed-files"] == set()


# ---------------------------------------------------------------------------
# parse_job_pytest_paths — small synthetic fixtures (multi-line and single-line forms)
# ---------------------------------------------------------------------------


def test_parses_multiline_backslash_continued_pytest_invocation():
    text = (
        "jobs:\n"
        "  sample:\n"
        "    steps:\n"
        "      - run: |\n"
        "          pytest tests/unit/foo \\\n"
        "                 tests/unit/bar \\\n"
        '                 -m "not slow" --tb=short -q\n'
    )
    job_paths = parse_job_pytest_paths(text)
    assert job_paths["sample"] == {"tests/unit/foo", "tests/unit/bar"}


def test_parses_single_line_blanket_pytest_tests():
    text = (
        "jobs:\n"
        "  slow:\n"
        "    steps:\n"
        "      - run: |\n"
        '          pytest tests/ -m "slow or extra_slow" --tb=short -q\n'
    )
    job_paths = parse_job_pytest_paths(text)
    assert job_paths["slow"] == {"tests"}


def test_deeper_indented_keys_are_not_mistaken_for_job_headers():
    text = (
        "jobs:\n"
        "  real-job:\n"
        "    steps:\n"
        "      - run: |\n"
        "          pytest tests/unit/real \\\n"
        '                 -m "not slow"\n'
    )
    job_paths = parse_job_pytest_paths(text)
    assert list(job_paths.keys()) == ["real-job"]
    assert "steps" not in job_paths


# ---------------------------------------------------------------------------
# directories_from_test_files
# ---------------------------------------------------------------------------


def test_directories_from_test_files_groups_by_immediate_parent():
    grouped = directories_from_test_files([
        "tests/unit/core/test_a.py",
        "tests/unit/core/test_b.py",
        "tests/unit/test_loose.py",
    ])
    assert grouped == {
        "tests/unit/core": ["tests/unit/core/test_a.py", "tests/unit/core/test_b.py"],
        "tests/unit": ["tests/unit/test_loose.py"],
    }


# ---------------------------------------------------------------------------
# is_directory_covered
# ---------------------------------------------------------------------------


def test_is_directory_covered_direct_and_descendant_match():
    fastlane = {"tests/unit/domains"}
    assert is_directory_covered("tests/unit/domains", fastlane)
    assert is_directory_covered("tests/unit/domains/campaigns", fastlane)


def test_is_directory_covered_flags_unrelated_directory_as_uncovered():
    fastlane = {"tests/unit/domains"}
    assert not is_directory_covered("tests/unit/other", fastlane)
    # a sibling that merely shares a string prefix must not count as covered
    assert not is_directory_covered("tests/unit/domainsx", fastlane)


# ---------------------------------------------------------------------------
# directory_is_covered_by_file_listings — loose-files-directly-under-a-parent case
# (the real TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK finding: tests/unit/test_dirty_
# refresh.py and two siblings had no themed subdirectory and no directory-level job entry).
# ---------------------------------------------------------------------------


def test_directory_covered_by_file_listings_when_every_file_individually_listed():
    fastlane = {"tests/unit/test_a.py", "tests/unit/test_b.py"}
    assert directory_is_covered_by_file_listings(
        ["tests/unit/test_a.py", "tests/unit/test_b.py"], fastlane
    )


def test_directory_not_covered_by_file_listings_when_one_file_missing():
    fastlane = {"tests/unit/test_a.py"}
    assert not directory_is_covered_by_file_listings(
        ["tests/unit/test_a.py", "tests/unit/test_b.py"], fastlane
    )


def test_real_repo_tests_unit_loose_files_are_individually_covered():
    real_workflow_job_paths = parse_job_pytest_paths(_REAL_WORKFLOW_PATH.read_text(encoding="utf-8"))
    fastlane_union = set()
    for job_name, paths in real_workflow_job_paths.items():
        if job_name != "slow":
            fastlane_union |= paths
    assert directory_is_covered_by_file_listings(
        [
            "tests/unit/test_dirty_refresh.py",
            "tests/unit/test_memory_probe.py",
            "tests/unit/test_queue_worker_singleton.py",
        ],
        fastlane_union,
    )


# ---------------------------------------------------------------------------
# file_is_fully_slow_marked
# ---------------------------------------------------------------------------


def test_file_is_fully_slow_marked_via_decorator(tmp_path):
    f = tmp_path / "test_x.py"
    f.write_text(
        "import pytest\n"
        "@pytest.mark.slow\n"
        "def test_one():\n"
        "    pass\n"
        "@pytest.mark.extra_slow\n"
        "def test_two():\n"
        "    pass\n"
    )
    assert file_is_fully_slow_marked(f)


def test_file_is_fully_slow_marked_via_module_pytestmark(tmp_path):
    f = tmp_path / "test_x.py"
    f.write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.extra_slow\n"
        "def test_one():\n"
        "    pass\n"
        "def test_two():\n"
        "    pass\n"
    )
    assert file_is_fully_slow_marked(f)


def test_file_is_fully_slow_marked_via_class_decorator(tmp_path):
    f = tmp_path / "test_x.py"
    f.write_text(
        "import pytest\n"
        "@pytest.mark.slow\n"
        "class TestThing:\n"
        "    def test_one(self):\n"
        "        pass\n"
        "    def test_two(self):\n"
        "        pass\n"
    )
    assert file_is_fully_slow_marked(f)


def test_file_with_one_unmarked_test_is_not_fully_slow_marked(tmp_path):
    """The critical negative case: a mix of marked and unmarked tests must NOT be treated as
    fully slow -- the unmarked test would silently never run under -m 'slow or extra_slow'."""
    f = tmp_path / "test_x.py"
    f.write_text(
        "import pytest\n"
        "@pytest.mark.slow\n"
        "def test_one():\n"
        "    pass\n"
        "def test_two():\n"
        "    pass\n"
    )
    assert not file_is_fully_slow_marked(f)


def test_file_with_zero_test_functions_is_not_fully_slow_marked(tmp_path):
    f = tmp_path / "test_x.py"
    f.write_text("def helper():\n    pass\n")
    assert not file_is_fully_slow_marked(f)


def test_real_regression_behavioral_5k_is_fully_slow_marked():
    real_file = _REPO_ROOT / "tests" / "regression" / "test_behavioral_5k.py"
    assert real_file.exists()
    assert file_is_fully_slow_marked(real_file)


# ---------------------------------------------------------------------------
# directory_is_slow_only_legitimate
# ---------------------------------------------------------------------------


def test_directory_is_slow_only_legitimate_true_when_all_files_slow_marked(tmp_path):
    f = tmp_path / "tests" / "regression" / "test_a.py"
    f.parent.mkdir(parents=True)
    f.write_text("import pytest\n@pytest.mark.extra_slow\ndef test_one():\n    pass\n")
    assert directory_is_slow_only_legitimate(["tests/regression/test_a.py"], tmp_path)


def test_directory_is_slow_only_legitimate_false_with_any_unmarked_file(tmp_path):
    marked = tmp_path / "tests" / "mixed" / "test_a.py"
    unmarked = tmp_path / "tests" / "mixed" / "test_b.py"
    marked.parent.mkdir(parents=True)
    marked.write_text("import pytest\n@pytest.mark.slow\ndef test_one():\n    pass\n")
    unmarked.write_text("def test_two():\n    pass\n")
    assert not directory_is_slow_only_legitimate(
        ["tests/mixed/test_a.py", "tests/mixed/test_b.py"], tmp_path
    )


# ---------------------------------------------------------------------------
# check_ci_workflow_test_coverage — aggregate, against the real repo state
# ---------------------------------------------------------------------------


def test_check_against_real_repo_state_passes_cleanly():
    results = check_ci_workflow_test_coverage(_REAL_WORKFLOW_PATH, _REPO_ROOT)
    failing = [r for r in results if r["status"] == "FAIL"]
    assert failing == [], (
        f"Orphaned test director{'y' if len(failing) == 1 else 'ies'} not referenced by any "
        f"fast-lane CI job path list: {[r['condition'] for r in failing]}"
    )


def test_check_against_real_repo_state_recognizes_regression_as_slow_only_legitimate():
    results = check_ci_workflow_test_coverage(_REAL_WORKFLOW_PATH, _REPO_ROOT)
    by_condition = {r["condition"]: r for r in results}
    regression = by_condition["ci_test_dir_covered:tests/regression"]
    assert regression["status"] == "PASS"
    assert "slow" in regression["evidence"]


# ---------------------------------------------------------------------------
# check_ci_workflow_test_coverage — coverage-honesty fixture: a deliberate, injected violation
# ---------------------------------------------------------------------------

_FIXTURE_WORKFLOW_TEXT = (
    "jobs:\n"
    "  fast-lane:\n"
    "    steps:\n"
    "      - run: |\n"
    "          pytest tests/unit/covered \\\n"
    '                 -m "not slow and not extra_slow" --tb=short -q\n'
    "  slow:\n"
    "    steps:\n"
    "      - run: |\n"
    '          pytest tests/ -m "slow or extra_slow" --tb=short -q\n'
)


def _write_fixture_tree(tmp_path):
    covered = tmp_path / "tests" / "unit" / "covered" / "test_a.py"
    covered.parent.mkdir(parents=True)
    covered.write_text("def test_one():\n    pass\n")

    slow_only = tmp_path / "tests" / "slowdir" / "test_b.py"
    slow_only.parent.mkdir(parents=True)
    slow_only.write_text("import pytest\n@pytest.mark.extra_slow\ndef test_one():\n    pass\n")

    orphaned = tmp_path / "tests" / "orphan" / "test_c.py"
    orphaned.parent.mkdir(parents=True)
    orphaned.write_text("def test_one():\n    pass\n")

    workflow_path = tmp_path / "test.yml"
    workflow_path.write_text(_FIXTURE_WORKFLOW_TEXT)
    return workflow_path, [
        "tests/unit/covered/test_a.py",
        "tests/slowdir/test_b.py",
        "tests/orphan/test_c.py",
    ]


def test_fixture_catches_a_real_orphaned_fast_directory():
    """The core acceptance-criterion proof: a directory with an unmarked test that no fast-lane
    job references must FAIL, even while a legitimately slow-only directory and a properly
    covered directory both PASS in the same run."""
    with __import__("tempfile").TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        workflow_path, files = _write_fixture_tree(tmp_path)

        results = check_ci_workflow_test_coverage(workflow_path, tmp_path, test_files=files)
        by_condition = {r["condition"]: r for r in results}

        assert by_condition["ci_test_dir_covered:tests/unit/covered"]["status"] == "PASS"
        assert by_condition["ci_test_dir_covered:tests/slowdir"]["status"] == "PASS"

        orphan = by_condition["ci_test_dir_covered:tests/orphan"]
        assert orphan["status"] == "FAIL"
        assert "tests/orphan" in orphan["evidence"]


def test_fixture_violation_is_resolved_once_the_directory_is_added_to_a_fastlane_job():
    """Same fixture as above, but proves the check's before/after behavior directly: FAILs
    without the fast-lane path entry, PASSes once it's added -- not just that a passing case
    exists somewhere else."""
    with __import__("tempfile").TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        workflow_path, files = _write_fixture_tree(tmp_path)

        before = check_ci_workflow_test_coverage(workflow_path, tmp_path, test_files=files)
        before_by_condition = {r["condition"]: r for r in before}
        assert before_by_condition["ci_test_dir_covered:tests/orphan"]["status"] == "FAIL"

        fixed_text = _FIXTURE_WORKFLOW_TEXT.replace(
            "pytest tests/unit/covered \\\n",
            "pytest tests/unit/covered \\\n"
            "                 tests/orphan \\\n",
        )
        workflow_path.write_text(fixed_text)

        after = check_ci_workflow_test_coverage(workflow_path, tmp_path, test_files=files)
        after_by_condition = {r["condition"]: r for r in after}
        assert after_by_condition["ci_test_dir_covered:tests/orphan"]["status"] == "PASS"


def test_fixture_loose_files_need_every_one_individually_listed_to_pass():
    """Aggregate-level proof for the file-listing fallback: a directory with two loose files and
    no directory-level entry FAILs while only one file is listed, and PASSes once both are."""
    with __import__("tempfile").TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        loose_a = tmp_path / "tests" / "loose" / "test_a.py"
        loose_b = tmp_path / "tests" / "loose" / "test_b.py"
        loose_a.parent.mkdir(parents=True)
        loose_a.write_text("def test_one():\n    pass\n")
        loose_b.write_text("def test_two():\n    pass\n")
        files = ["tests/loose/test_a.py", "tests/loose/test_b.py"]

        partial_text = (
            "jobs:\n"
            "  fast-lane:\n"
            "    steps:\n"
            "      - run: |\n"
            "          pytest tests/loose/test_a.py \\\n"
            '                 -m "not slow" --tb=short -q\n'
            "  slow:\n"
            "    steps:\n"
            "      - run: |\n"
            '          pytest tests/ -m "slow or extra_slow" --tb=short -q\n'
        )
        workflow_path = tmp_path / "test.yml"
        workflow_path.write_text(partial_text)

        partial = check_ci_workflow_test_coverage(workflow_path, tmp_path, test_files=files)
        assert {r["condition"]: r for r in partial}["ci_test_dir_covered:tests/loose"]["status"] == "FAIL"

        complete_text = partial_text.replace(
            "pytest tests/loose/test_a.py \\\n",
            "pytest tests/loose/test_a.py \\\n"
            "                 tests/loose/test_b.py \\\n",
        )
        workflow_path.write_text(complete_text)

        complete = check_ci_workflow_test_coverage(workflow_path, tmp_path, test_files=files)
        assert {r["condition"]: r for r in complete}["ci_test_dir_covered:tests/loose"]["status"] == "PASS"


# ---------------------------------------------------------------------------
# pytest_norecursedirs / directory_is_excluded_from_pytest_collection --
# TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE's own archival of tests/archive/ (excluded from
# pytest collection via pyproject.toml's norecursedirs, still containing real test_*.py files)
# surfaced a real gap this checker's original design didn't anticipate: a norecursedirs-excluded
# directory is never collected in ANY job, so it cannot be a "silently orphaned" violation this
# checker exists to catch, but the checker had no way to know that.
# TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY later hard-deleted tests/archive/ itself and removed
# the now-dead "archive" norecursedirs entry, completing the cleanup this region tracks.
# ---------------------------------------------------------------------------


def test_pytest_norecursedirs_reads_real_pyproject_toml():
    norecursedirs = pytest_norecursedirs(_REPO_ROOT / "pyproject.toml")
    assert "archive" not in norecursedirs
    assert "stored_artifacts" in norecursedirs


def test_pytest_norecursedirs_returns_empty_set_for_missing_file(tmp_path):
    assert pytest_norecursedirs(tmp_path / "does-not-exist.toml") == set()


def test_directory_is_excluded_from_pytest_collection_matches_any_path_segment():
    norecursedirs = {"archive", "scratch"}
    assert directory_is_excluded_from_pytest_collection("tests/archive", norecursedirs) is True
    assert directory_is_excluded_from_pytest_collection("tests/tools", norecursedirs) is False


def test_directory_is_excluded_from_pytest_collection_false_for_no_match():
    assert directory_is_excluded_from_pytest_collection("tests/orphan", {"archive"}) is False


def test_fixture_norecursedirs_excluded_directory_passes_instead_of_failing():
    """The core acceptance-criterion proof for the new exclusion: without norecursedirs, the
    orphan directory FAILs exactly as it always did; injecting norecursedirs containing its
    basename flips it to PASS with distinct, honest evidence -- proving this is a real behavior
    change, not a no-op."""
    with __import__("tempfile").TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        workflow_path, files = _write_fixture_tree(tmp_path)

        without_exclusion = check_ci_workflow_test_coverage(
            workflow_path, tmp_path, test_files=files, norecursedirs=set()
        )
        by_condition = {r["condition"]: r for r in without_exclusion}
        assert by_condition["ci_test_dir_covered:tests/orphan"]["status"] == "FAIL"

        with_exclusion = check_ci_workflow_test_coverage(
            workflow_path, tmp_path, test_files=files, norecursedirs={"orphan"}
        )
        by_condition = {r["condition"]: r for r in with_exclusion}
        excluded = by_condition["ci_test_dir_covered:tests/orphan"]
        assert excluded["status"] == "PASS"
        assert "norecursedirs" in excluded["evidence"]

        # Directories outside the exclusion set are completely unaffected by it.
        assert by_condition["ci_test_dir_covered:tests/unit/covered"]["status"] == "PASS"
        assert by_condition["ci_test_dir_covered:tests/slowdir"]["status"] == "PASS"



# ---------------------------------------------------------------------------
# Architecture guard — module has no CLI/argparse entry point (pytest-consumed only, matching
# test_scope_coverage_static.py's stated no-CLI convention for this check family)
# ---------------------------------------------------------------------------


def test_module_has_no_argparse_entry_point():
    source = Path(ci_workflow_test_coverage.__file__).read_text(encoding="utf-8")
    assert "argparse" not in source
    assert "__main__" not in source
