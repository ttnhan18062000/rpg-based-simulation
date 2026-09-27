"""Tests for tools/agent-monitoring/monitoring_shard_paths.py
(TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION).
"""
import re
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from monitoring_shard_paths import shard_paths, per_identifier_shard_paths  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent


def test_shard_paths_finds_bare_canonical_only(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    (week_dir / "tools.jsonl").write_text("{}\n")
    result = shard_paths(tmp_path, "tools")
    assert result == [week_dir / "tools.jsonl"]


def test_shard_paths_finds_per_identifier_only(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    (week_dir / "TCK-A.tools.jsonl").write_text("{}\n")
    result = shard_paths(tmp_path, "tools")
    assert result == [week_dir / "TCK-A.tools.jsonl"]


def test_shard_paths_finds_both_shapes_combined(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    (week_dir / "tools.jsonl").write_text("{}\n")
    (week_dir / "TCK-A.tools.jsonl").write_text("{}\n")
    (week_dir / "TCK-B.tools.jsonl").write_text("{}\n")
    result = shard_paths(tmp_path, "tools")
    assert set(result) == {
        week_dir / "tools.jsonl", week_dir / "TCK-A.tools.jsonl", week_dir / "TCK-B.tools.jsonl",
    }


def test_shard_paths_spans_multiple_weeks(tmp_path):
    w1 = tmp_path / "2026-W01"
    w2 = tmp_path / "2026-W02"
    w1.mkdir()
    w2.mkdir()
    (w1 / "TCK-A.tools.jsonl").write_text("{}\n")
    (w2 / "TCK-B.tools.jsonl").write_text("{}\n")
    result = shard_paths(tmp_path, "tools")
    assert set(result) == {w1 / "TCK-A.tools.jsonl", w2 / "TCK-B.tools.jsonl"}


def test_shard_paths_empty_when_neither_exists(tmp_path):
    (tmp_path / "2026-W01").mkdir()
    assert shard_paths(tmp_path, "tools") == []


def test_shard_paths_missing_data_root_returns_empty(tmp_path):
    assert shard_paths(tmp_path / "does-not-exist", "tools") == []


def test_shard_paths_data_root_is_a_regular_file_returns_empty_not_raise(tmp_path):
    """Design-peer review finding: `.exists()` passes for a regular file, and `.iterdir()` on one
    raises `NotADirectoryError` -- `.is_dir()` correctly returns False for this case instead."""
    not_a_dir = tmp_path / "some_file"
    not_a_dir.write_text("not a directory")
    assert shard_paths(not_a_dir, "tools") == []


def test_per_identifier_shard_paths_excludes_bare_canonical(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    (week_dir / "tools.jsonl").write_text("{}\n")
    (week_dir / "TCK-A.tools.jsonl").write_text("{}\n")
    result = per_identifier_shard_paths(week_dir, "tools")
    assert result == [week_dir / "TCK-A.tools.jsonl"]


def test_per_identifier_shard_paths_only_matches_the_given_kind(tmp_path):
    week_dir = tmp_path / "2026-W01"
    week_dir.mkdir()
    (week_dir / "TCK-A.tools.jsonl").write_text("{}\n")
    (week_dir / "TCK-A.runs.jsonl").write_text("{}\n")
    result = per_identifier_shard_paths(week_dir, "tools")
    assert result == [week_dir / "TCK-A.tools.jsonl"]


# ---------------------------------------------------------------------------
# AC5 — "demonstrated not asserted": a 10th independent copy of the double-glob idiom fails at
# test time rather than being found by inspection two weeks later.
# ---------------------------------------------------------------------------

# The idiom's two halves, matched independently rather than as one combined pattern -- every
# known variant (bare `return`, an intermediate local variable, an f-string vs. a plain literal
# string, a bare filename variable vs. one with a literal `.jsonl` suffix already in the glob
# call) puts these two shapes within a few lines of each other, but combines them differently.
# The WIDE half is the specific, low-false-positive marker (`*/*.` alone also matches unrelated
# `*/*.md`/`**/*.yaml` globs elsewhere in the repo -- requiring "jsonl" too excludes those); the
# NARROW half only needs to exist nearby to confirm this is a paired narrow+wide idiom, not a
# lone JSONL glob like `working_log_writer.py`'s own single-shape shard glob.
_NARROW_GLOB_RE = re.compile(r'\.glob\([^)]*\*/(?!\*)[^)]*\)')
_WIDE_GLOB_RE = re.compile(r'\.glob\([^)]*\*/\*\.[^)]*jsonl[^)]*\)')
_WINDOW = 3  # lines


def _scan_for_double_glob(directory: Path) -> list:
    hits = []
    for py_file in sorted(directory.rglob("*.py")):
        if "tests" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        lines = py_file.read_text(encoding="utf-8").splitlines()
        narrow_lines = {i for i, l in enumerate(lines) if _NARROW_GLOB_RE.search(l)}
        wide_lines = {i for i, l in enumerate(lines) if _WIDE_GLOB_RE.search(l)}
        if any(abs(n - w) <= _WINDOW for n in narrow_lines for w in wide_lines):
            hits.append(py_file.relative_to(_REPO_ROOT).as_posix())
    return hits


def test_double_glob_idiom_appears_nowhere():
    """`monitoring_shard_paths.shard_paths()` doesn't reproduce the fragile idiom in one
    centralized place -- it eliminates it structurally (explicit per-week-directory iteration,
    never a second repo-wide `data_root.glob("*/*.<kind>.jsonl")` call), so the correct guard
    after migration is zero occurrences anywhere, a strictly stronger guarantee than "exactly
    one." Before migration, this correctly fails loudly against every site still holding the old
    shape -- confirmed by running it pre-migration and seeing the real hit list, not assumed."""
    hits = _scan_for_double_glob(_REPO_ROOT / "tools") + _scan_for_double_glob(_REPO_ROOT / "src")
    assert hits == [], hits
