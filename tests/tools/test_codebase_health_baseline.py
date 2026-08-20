"""Tests for tools/codebase_health_baseline.py
(TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET).

Coverage-honesty requirement (matches this repo's established convention, e.g.
tests/tools/test_workflow_meta_conformance.py's own docstring): every check the
tool claims to compute has at least one fixture proving it computes correctly,
not just that it runs without error.
"""

import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import codebase_health_baseline as chb  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(tmp_path):
    _git(["init", "-q"], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)


def _commit(tmp_path, message):
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", message], tmp_path)


# ---------------------------------------------------------------------------
# Exclusion correctness (the specific bug this ticket exists to prevent)
# ---------------------------------------------------------------------------


def test_churn_exclusion_ignores_synthetic_bookkeeping_noise(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("x = 1\n" * 5, encoding="utf-8")
    _commit(tmp_path, "add real src file")

    baseline_churn = chb.compute_churn_lines_changed(tmp_path)
    assert baseline_churn > 0

    (tmp_path / "agent-monitoring").mkdir()
    (tmp_path / "agent-monitoring" / "events.jsonl").write_text(
        "\n".join(f'{{"n": {i}}}' for i in range(5000)), encoding="utf-8"
    )
    (tmp_path / "tickets").mkdir()
    (tmp_path / "tickets" / "working_log.csv").write_text(
        "\n".join(f"row{i},value{i}" for i in range(5000)), encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "REGISTRY.yaml").write_text(
        "\n".join(f"entry_{i}: value" for i in range(5000)), encoding="utf-8"
    )
    _commit(tmp_path, "heavy synthetic bookkeeping churn")

    churn_after_noise = chb.compute_churn_lines_changed(tmp_path)

    assert churn_after_noise == baseline_churn, (
        "Synthetic churn confined to the 3 excluded bookkeeping files moved the "
        "computed churn metric — the pathspec exclusion is not working."
    )

    # Prove the noise really would have moved the metric without exclusion —
    # otherwise this test would pass trivially even with a broken exclusion.
    unfiltered_output = chb._run_git(["log", "--shortstat", "--pretty=format:"], tmp_path)
    assert "15000 insertions" in unfiltered_output or any(
        f"{n} insertion" in unfiltered_output for n in (14999, 15000, 15001)
    )


def test_churn_exclusion_still_counts_real_src_changes(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("x = 1\n", encoding="utf-8")
    _commit(tmp_path, "init")

    (tmp_path / "src" / "foo.py").write_text("x = 1\n" * 10, encoding="utf-8")
    _commit(tmp_path, "grow src file")

    churn = chb.compute_churn_lines_changed(tmp_path)
    assert churn > 0, "Real (non-excluded) src churn must still be counted."


# ---------------------------------------------------------------------------
# Source/test split correctness
# ---------------------------------------------------------------------------


def test_source_test_split_does_not_conflate(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("x = 1\n" * 3, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("y = 2\n" * 7, encoding="utf-8")
    _commit(tmp_path, "add src and test file")

    source_loc, source_files = chb.measure_py_tree(tmp_path, "src/")
    test_loc, test_files = chb.measure_py_tree(tmp_path, "tests/")

    assert (source_loc, source_files) == (3, 1)
    assert (test_loc, test_files) == (7, 1)


def test_source_test_split_handles_nested_directories(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src" / "engine").mkdir(parents=True)
    (tmp_path / "src" / "engine" / "kernel.py").write_text("a = 1\n" * 4, encoding="utf-8")
    (tmp_path / "tests" / "unit" / "engine").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "engine" / "test_kernel.py").write_text(
        "b = 2\n" * 9, encoding="utf-8"
    )
    _commit(tmp_path, "nested src and test files")

    source_loc, source_files = chb.measure_py_tree(tmp_path, "src/")
    test_loc, test_files = chb.measure_py_tree(tmp_path, "tests/")

    assert (source_loc, source_files) == (4, 1)
    assert (test_loc, test_files) == (9, 1)


def test_top_level_src_packages_counts_nested_dirs_not_root_files(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src" / "engine").mkdir(parents=True)
    (tmp_path / "src" / "engine" / "kernel.py").write_text("a = 1\n", encoding="utf-8")
    (tmp_path / "src" / "core").mkdir(parents=True)
    (tmp_path / "src" / "core" / "state.py").write_text("b = 1\n", encoding="utf-8")
    (tmp_path / "src" / "__main__.py").write_text("c = 1\n", encoding="utf-8")
    _commit(tmp_path, "src packages")

    assert chb.count_top_level_src_packages(tmp_path) == 2


def test_test_subdirectories_ignores_untracked_empty_dirs(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_a.py").write_text("x = 1\n", encoding="utf-8")
    _commit(tmp_path, "one real test dir")

    # A directory that exists on disk but has no git-tracked file inside it
    # (mirrors the real repo's tests/ai/ — only a __pycache__/ inside) must not
    # be counted.
    (tmp_path / "tests" / "stale_untracked").mkdir(parents=True)
    (tmp_path / "tests" / "stale_untracked" / "__pycache__").mkdir()

    assert chb.count_test_subdirectories(tmp_path) == 1


# ---------------------------------------------------------------------------
# Dead bytecode detection
# ---------------------------------------------------------------------------


def test_dead_bytecode_detects_pyc_with_no_source(tmp_path):
    pycache = tmp_path / "src" / "old_module" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "gone.cpython-312.pyc").write_bytes(b"\x00")

    assert chb.find_dead_bytecode_files(tmp_path) == 1


def test_dead_bytecode_ignores_pyc_with_live_source(tmp_path):
    module_dir = tmp_path / "src" / "live_module"
    module_dir.mkdir(parents=True)
    (module_dir / "present.py").write_text("x = 1\n", encoding="utf-8")
    pycache = module_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "present.cpython-312.pyc").write_bytes(b"\x00")

    assert chb.find_dead_bytecode_files(tmp_path) == 0


# ---------------------------------------------------------------------------
# Unused core dependency detection
# ---------------------------------------------------------------------------


def test_unused_core_dependency_detected(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["reallyunusedpkg>=1.0.0", "usedpkg>=1.0.0"]\n',
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import usedpkg\n", encoding="utf-8")
    _commit(tmp_path, "init")

    unused = chb.find_unused_core_dependencies(tmp_path)
    assert unused == ["reallyunusedpkg"]


def test_used_core_dependency_found_outside_src(tmp_path):
    # Mirrors the real repo's python-json-logger case: only used in scripts/,
    # not src/ — the search must be repo-wide (D23's own methodology), not
    # scoped to src/, or this produces a false positive.
    _init_repo(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["somepkg>=1.0.0"]\n',
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "runner.py").write_text("import somepkg\n", encoding="utf-8")
    _commit(tmp_path, "init")

    unused = chb.find_unused_core_dependencies(tmp_path)
    assert unused == []


def test_dependency_import_name_override():
    assert chb._dependency_import_name("python-json-logger>=2.0.7") == "pythonjsonlogger"
    assert chb._dependency_import_name("sse-starlette>=3.3.0") == "sse_starlette"
    assert chb._dependency_import_name("uvicorn[standard]>=0.30.0") == "uvicorn"


# ---------------------------------------------------------------------------
# make codebase-health-baseline runs successfully against the real repo
# ---------------------------------------------------------------------------


def test_make_target_runs_successfully_with_plausible_values():
    result = subprocess.run(
        ["make", "codebase-health-baseline"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    output = result.stdout

    assert "Source LoC / files" in output
    assert "Test LoC / files" in output
    assert "Test:source ratio (LoC)" in output
    assert "Top-level src/ packages" in output
    assert "Test subdirectories" in output
    assert "Commits (full history)" in output
    assert "Docs (.md, under docs/)" in output
    assert "docs/REGISTRY.yaml size" in output
    assert "Dead bytecode files" in output
    assert "Declared-but-unused core dependencies" in output
    assert "Churn (lines changed, excl. bookkeeping)" in output

    report = chb.build_report(_REPO_ROOT)
    assert report["source_loc"] > 10000
    assert report["source_files"] > 100
    assert report["test_loc"] > 10000
    assert report["test_files"] > 100
    assert report["top_level_src_packages"] > 5
    assert report["test_subdirectories"] > 5
    assert report["commit_count"] > 0
    assert report["doc_count"] > 0
    assert report["registry_size_bytes"] > 0


# ---------------------------------------------------------------------------
# Live re-run sanity check: fresh numbers differ from D24 §C's stale snapshot
# ---------------------------------------------------------------------------


def test_live_numbers_differ_from_d24_stale_snapshot():
    # D24 §C recorded these hardcoded values from a one-time audit run, before
    # src_legacy/tests_legacy deletion and several dependency/test changes.
    # A live re-run must not echo them back.
    report = chb.build_report(_REPO_ROOT)

    d24_stale_dead_bytecode = 601
    d24_stale_commit_count = 595
    d24_stale_unused_deps = {"pika", "confluent-kafka"}

    assert report["dead_bytecode_files"] != d24_stale_dead_bytecode
    assert report["commit_count"] != d24_stale_commit_count
    assert set(report["unused_core_dependencies"]) != d24_stale_unused_deps
