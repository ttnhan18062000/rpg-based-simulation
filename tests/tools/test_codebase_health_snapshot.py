"""Tests for tools/codebase_health_snapshot.py
(TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD).

Coverage-honesty requirement (matches this repo's established convention, e.g.
tests/tools/test_codebase_health_baseline.py's own docstring): every check the
tool claims to compute has at least one fixture proving it computes correctly,
not just that it runs without error.

Anti-drift test guard: every test in this file passes an explicit
tmp_path-derived history_path — never the module's own DEFAULT_HISTORY_PATH,
even indirectly. `write_snapshot`/`build_snapshot_record` have no default for
this parameter (load-bearing, see the module's own docstring), so an omitted
keyword argument would be a hard TypeError, not a silent real-file write; this
file's own `test_no_test_target_path_resolves_under_real_agent_monitoring_dir`
below is defense-in-depth on top of that, mirroring
tests/tools/test_monitoring_writer.py:31-51's literal-source-scan pattern.
"""

import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import codebase_health_snapshot as chs  # noqa: E402
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


def _make_minimal_repo(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("x = 1\n" * 3, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("y = 2\n" * 5, encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("hello\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = []\n', encoding="utf-8"
    )
    _commit(tmp_path, "init minimal repo")


def _synthetic_snapshot(**overrides):
    base = {
        "source_loc": 100,
        "source_files": 10,
        "test_loc": 50,
        "test_files": 5,
        "test_source_ratio": 0.5,
        "top_level_src_packages": 3,
        "test_subdirectories": 2,
        "commit_count": 20,
        "doc_count": 8,
        "registry_size_bytes": 1000,
        "registry_size_lines": 40,
        "dead_bytecode_files": 0,
        "unused_core_dependencies": [],
        "churn_lines_changed_excl_bookkeeping": 500,
        "snapshot_schema_version": chs.SNAPSHOT_SCHEMA_VERSION,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Guard: no test in this file may target the real agent-monitoring/ directory
# ---------------------------------------------------------------------------


def test_no_test_target_path_resolves_under_real_agent_monitoring_dir():
    """Guard: no test in this file may hardcode a path under the real repo's
    agent-monitoring/ directory — every target below must be tmp_path-rooted.

    Mirrors tests/tools/test_monitoring_writer.py:31-51's literal-source-scan
    pattern exactly (same style forbidden-string list, same
    inspect.getsource() scan over every other test function in this file).
    """
    module = sys.modules[__name__]
    this_function_name = "test_no_test_target_path_resolves_under_real_agent_monitoring_dir"
    real_dir = str((_REPO_ROOT / "agent-monitoring").resolve())
    forbidden = [real_dir, "Path(" + '"agent-monitoring"' + ")", "Path(" + "'agent-monitoring'" + ")"]

    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if name == this_function_name or obj.__module__ != __name__:
            continue
        source = inspect.getsource(obj)
        for pattern in forbidden:
            assert pattern not in source, f"{name} references a real-corpus-shaped path: {pattern!r}"


# ---------------------------------------------------------------------------
# Persistence / append-only behavior (AC #1)
# ---------------------------------------------------------------------------


def test_two_invocations_append_two_separate_records_without_truncation(tmp_path):
    _make_minimal_repo(tmp_path)
    history_path = tmp_path / "history" / "codebase_health_history.jsonl"

    assert chs.write_snapshot(tmp_path, history_path) is True
    lines_after_first = history_path.read_text().splitlines()
    assert len(lines_after_first) == 1
    first_line = lines_after_first[0]

    assert chs.write_snapshot(tmp_path, history_path) is True
    lines_after_second = history_path.read_text().splitlines()
    assert len(lines_after_second) == 2
    assert lines_after_second[0] == first_line


def test_appended_record_is_valid_json_matching_frozen_schema_allowlist(tmp_path):
    _make_minimal_repo(tmp_path)
    history_path = tmp_path / "history.jsonl"

    chs.write_snapshot(tmp_path, history_path)
    lines = history_path.read_text().splitlines()
    record = json.loads(lines[0])

    record_keys_minus_version = set(record.keys()) - {"snapshot_schema_version"}
    assert record_keys_minus_version == chs.EXPECTED_SNAPSHOT_KEYS


def test_write_failure_does_not_crash_caller(tmp_path, monkeypatch):
    _make_minimal_repo(tmp_path)
    history_path = tmp_path / "history.jsonl"

    monkeypatch.setattr(chs, "write_line", lambda target_path, line: False)

    result = chs.write_snapshot(tmp_path, history_path)
    assert result is False


# ---------------------------------------------------------------------------
# Schema freeze / versioning (Scope item 3, AC #4)
# ---------------------------------------------------------------------------


def test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented(tmp_path):
    _make_minimal_repo(tmp_path)

    record = chs.build_snapshot_record(tmp_path)
    live_report = chb.build_report(tmp_path)

    record_without_version = {k: v for k, v in record.items() if k != "snapshot_schema_version"}
    assert record_without_version == live_report


def test_schema_mismatch_raises_loudly_not_silently(tmp_path, monkeypatch):
    _make_minimal_repo(tmp_path)

    valid_report = chb.build_report(tmp_path)

    added_key_report = dict(valid_report)
    added_key_report["a_brand_new_field"] = 123
    monkeypatch.setattr(chs, "build_report", lambda repo_root: added_key_report)
    with pytest.raises(RuntimeError):
        chs.build_snapshot_record(tmp_path)

    removed_key_report = dict(valid_report)
    del removed_key_report["source_loc"]
    monkeypatch.setattr(chs, "build_report", lambda repo_root: removed_key_report)
    with pytest.raises(RuntimeError):
        chs.build_snapshot_record(tmp_path)

    renamed_key_report = dict(valid_report)
    renamed_key_report["source_lines_of_code"] = renamed_key_report.pop("source_loc")
    monkeypatch.setattr(chs, "build_report", lambda repo_root: renamed_key_report)
    with pytest.raises(RuntimeError):
        chs.build_snapshot_record(tmp_path)


def test_schema_version_field_present_and_stable_across_writes(tmp_path):
    _make_minimal_repo(tmp_path)
    history_path = tmp_path / "history.jsonl"

    chs.write_snapshot(tmp_path, history_path)
    chs.write_snapshot(tmp_path, history_path)

    records = [json.loads(line) for line in history_path.read_text().splitlines()]
    assert len(records) == 2
    for record in records:
        assert record["snapshot_schema_version"] == chs.SNAPSHOT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Trend-arrow rendering (AC #2)
# ---------------------------------------------------------------------------


def test_scorecard_renders_per_dimension_trend_arrow_for_two_snapshots():
    older = _synthetic_snapshot(source_loc=100, test_loc=50, commit_count=20)
    newer = _synthetic_snapshot(source_loc=120, test_loc=50, commit_count=18)

    scorecard = chs.build_scorecard([older, newer])
    dimensions = scorecard["dimensions"]

    assert dimensions["source_loc"]["arrow"] == "↑"
    assert dimensions["source_loc"]["diff"] == 20
    assert dimensions["test_loc"]["arrow"] == "→"
    assert dimensions["test_loc"]["diff"] == 0
    assert dimensions["commit_count"]["arrow"] == "↓"
    assert dimensions["commit_count"]["diff"] == -2


def test_scorecard_output_has_no_aggregate_or_combined_score_field():
    older = _synthetic_snapshot(source_loc=100)
    newer = _synthetic_snapshot(source_loc=120)
    scorecard = chs.build_scorecard([older, newer])

    denylist = {"score", "overall", "combined", "summary", "health_score", "up_count", "down_count"}
    top_level_keys = {k.lower() for k in scorecard.keys()}
    assert top_level_keys.isdisjoint(denylist)
    dimension_keys = {k.lower() for k in scorecard["dimensions"].keys()}
    assert dimension_keys.isdisjoint(denylist)
    for row in scorecard["dimensions"].values():
        assert set(row.keys()).isdisjoint(denylist)

    # "scorecard" is this feature's own name (used in headers/docs) and
    # legitimately contains "score" as a substring — the denylist check must
    # use word boundaries so it doesn't false-positive on that, while still
    # catching a real standalone "score"/"overall"/etc. line or key.
    formatted = chs.format_scorecard(scorecard)
    lowered = formatted.lower()
    for forbidden in denylist:
        assert re.search(rf"\b{re.escape(forbidden)}\b", lowered) is None, forbidden

    # The positive half of AC #2: per-dimension directional indicators are
    # actually present.
    assert "↑" in formatted or "↓" in formatted or "→" in formatted


def test_non_scalar_dimension_unused_core_dependencies_does_not_get_forced_arrow():
    older = _synthetic_snapshot(unused_core_dependencies=["pika"])
    newer_changed = _synthetic_snapshot(unused_core_dependencies=["pika", "confluent-kafka"])
    newer_unchanged = _synthetic_snapshot(unused_core_dependencies=["pika"])

    scorecard_changed = chs.build_scorecard([older, newer_changed])
    row_changed = scorecard_changed["dimensions"]["unused_core_dependencies"]
    assert "arrow" not in row_changed
    assert row_changed["changed"] is True
    assert row_changed["latest"] == ["pika", "confluent-kafka"]
    assert row_changed["previous"] == ["pika"]

    scorecard_unchanged = chs.build_scorecard([older, newer_unchanged])
    row_unchanged = scorecard_unchanged["dimensions"]["unused_core_dependencies"]
    assert "arrow" not in row_unchanged
    assert row_unchanged["changed"] is False

    formatted = chs.format_scorecard(scorecard_changed)
    assert "confluent-kafka" in formatted


# ---------------------------------------------------------------------------
# Single-snapshot / zero-snapshot degradation (AC #3)
# ---------------------------------------------------------------------------


def test_scorecard_with_one_snapshot_labels_no_trend_data_without_crashing():
    only_snapshot = _synthetic_snapshot()
    scorecard = chs.build_scorecard([only_snapshot])

    assert scorecard["no_snapshots_yet"] is False
    for key, row in scorecard["dimensions"].items():
        assert row["trend_label"] == chs.NO_TREND_DATA_LABEL, key
        assert row.get("diff") is None or key == chs.NON_SCALAR_DIMENSION_KEY

    formatted = chs.format_scorecard(scorecard)
    assert chs.NO_TREND_DATA_LABEL in formatted


def test_scorecard_with_zero_snapshots_does_not_crash():
    scorecard = chs.build_scorecard([])
    assert scorecard["no_snapshots_yet"] is True
    assert scorecard["dimensions"] == {}

    formatted = chs.format_scorecard(scorecard)
    assert "no snapshots yet" in formatted.lower()

    # read_snapshots on a missing history file must also degrade cleanly.
    history_path = Path("/nonexistent-tmp-path-for-test/history.jsonl")
    assert chs.read_snapshots(history_path) == []


# ---------------------------------------------------------------------------
# Makefile wiring (Scope item 6)
# ---------------------------------------------------------------------------


def test_make_target_runs_successfully_end_to_end(tmp_path):
    history_path = tmp_path / "history.jsonl"

    snapshot_result = chs.main(["snapshot", "--repo-root", str(_REPO_ROOT), "--history-path", str(history_path)])
    assert snapshot_result == 0
    assert history_path.exists()
    assert len(history_path.read_text().splitlines()) == 1

    scorecard_result = chs.main(["scorecard", "--history-path", str(history_path)])
    assert scorecard_result == 0

    # The Makefile targets have no built-in path override, so pass one via
    # ARGS (mirroring codebase-health-impact's own ARGS="..." precedent) — the
    # real agent-monitoring/ directory must never be written to by this test.
    make_history_path = tmp_path / "make_history.jsonl"
    make_result = subprocess.run(
        ["make", "codebase-health-snapshot", f'ARGS=--history-path {make_history_path}'],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert make_result.returncode == 0, make_result.stderr
    assert "DONE" in make_result.stdout
    assert make_history_path.exists()

    scorecard_make_result = subprocess.run(
        ["make", "codebase-health-scorecard", f'ARGS=--history-path {make_history_path}'],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert scorecard_make_result.returncode == 0, scorecard_make_result.stderr
    assert "Codebase Health Scorecard" in scorecard_make_result.stdout
