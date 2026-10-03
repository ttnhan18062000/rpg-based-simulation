"""Tests for the craft metrics in tools/codebase_health_snapshot.py (TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS).

Every history path here is rooted in tmp_path, never the real agent-monitoring/ directory.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import codebase_health_baseline as chb  # noqa: E402
import codebase_health_snapshot as chs  # noqa: E402
from tools.code_health.metrics import CRAFT_METRIC_KEYS, REGISTRY_KEYS  # noqa: E402


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _minimal_repo(tmp_path):
    _git(["init", "-q"], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("x = 1\n" * 3, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("y = 2\n" * 5, encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("hello\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = []\n", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)


def _craft(**overrides):
    base = {key: 1 for key in CRAFT_METRIC_KEYS}
    base.update(overrides)
    return base


def _v1_record():
    keys = chs.EXPECTED_BASELINE_KEYS
    record = {key: 10 for key in keys}
    record.update(test_source_ratio=0.5, unused_core_dependencies=[], snapshot_schema_version=1)
    return record


def _v2_record(**craft_overrides):
    return {**_v1_record(), **_craft(**craft_overrides), "snapshot_schema_version": chs.SNAPSHOT_SCHEMA_VERSION}


# ── Schema contract ───────────────────────────────────────────────────────────


def test_schema_version_is_bumped_and_expected_keys_are_baseline_plus_craft():
    assert chs.SNAPSHOT_SCHEMA_VERSION == 2
    assert chs.EXPECTED_SNAPSHOT_KEYS == chs.EXPECTED_BASELINE_KEYS | frozenset(CRAFT_METRIC_KEYS)
    assert chs.EXPECTED_BASELINE_KEYS.isdisjoint(CRAFT_METRIC_KEYS)


def test_build_report_is_unchanged_so_the_baseline_target_does_not_need_the_code_health_tools(tmp_path):
    _minimal_repo(tmp_path)
    assert set(chb.build_report(tmp_path)) == chs.EXPECTED_BASELINE_KEYS


def test_record_carries_baseline_keys_and_every_craft_key_as_a_number(tmp_path):
    _minimal_repo(tmp_path)
    record = chs.build_snapshot_record(tmp_path, craft_metrics=_craft(craft_ruff_findings=42))
    assert set(record) - {"snapshot_schema_version"} == chs.EXPECTED_SNAPSHOT_KEYS
    assert record["snapshot_schema_version"] == 2
    assert record["craft_ruff_findings"] == 42
    for key in CRAFT_METRIC_KEYS:
        assert isinstance(record[key], (int, float)) and not isinstance(record[key], bool), key


def test_a_prepared_craft_dict_means_no_tool_is_run(tmp_path, monkeypatch):
    _minimal_repo(tmp_path)

    def boom(_repo_root):
        raise AssertionError("measure_craft_metrics must not run when craft_metrics is given")

    monkeypatch.setattr(chs, "measure_craft_metrics", boom)
    history = tmp_path / "h" / "history.jsonl"
    assert chs.write_snapshot(tmp_path, history, craft_metrics=_craft()) is True
    assert json.loads(history.read_text())["snapshot_schema_version"] == 2


def test_without_a_prepared_dict_the_craft_metrics_are_measured_from_the_repository(tmp_path):
    _minimal_repo(tmp_path)
    record = chs.build_snapshot_record(tmp_path)
    assert all(isinstance(record[key], int) for key in CRAFT_METRIC_KEYS)
    assert record["craft_baseline_rows"] == 0  # a repository with no registry has no baseline rows


def test_craft_key_mismatch_raises_loudly(tmp_path):
    _minimal_repo(tmp_path)
    missing = _craft()
    del missing["craft_ruff_findings"]
    with pytest.raises(RuntimeError):
        chs.build_snapshot_record(tmp_path, craft_metrics=missing)
    with pytest.raises(RuntimeError):
        chs.build_snapshot_record(tmp_path, craft_metrics={**_craft(), "craft_surprise": 1})


# ── Scorecard over mixed and craft-bearing history ────────────────────────────


def test_scorecard_trends_each_craft_dimension_between_two_v2_records():
    scorecard = chs.build_scorecard([_v2_record(craft_ruff_findings=100), _v2_record(craft_ruff_findings=90)])
    row = scorecard["dimensions"]["craft_ruff_findings"]
    assert (row["arrow"], row["diff"]) == ("↓", -10)
    assert set(CRAFT_METRIC_KEYS) <= set(scorecard["dimensions"])


def test_a_v2_record_after_a_v1_record_does_not_raise_and_shows_no_trend_for_craft():
    scorecard = chs.build_scorecard([_v1_record(), _v2_record()])
    craft_row = scorecard["dimensions"]["craft_ruff_findings"]
    assert craft_row["trend_label"] == chs.NO_TREND_DATA_LABEL and craft_row["diff"] is None
    assert scorecard["dimensions"]["source_loc"]["arrow"] == "→"  # the baseline dimensions still trend


def test_a_v1_latest_record_simply_has_no_craft_rows():
    scorecard = chs.build_scorecard([_v2_record(), _v1_record()])
    assert not set(CRAFT_METRIC_KEYS) & set(scorecard["dimensions"])
    assert "Source LoC" in chs.format_scorecard(scorecard)


def test_formatted_scorecard_shows_craft_dimensions_with_labels_and_no_aggregate():
    text = chs.format_scorecard(chs.build_scorecard([_v2_record(), _v2_record(craft_ruff_findings=5)]))
    assert "Craft: ruff findings" in text and "Craft: baseline rows (registry)" in text
    for forbidden in ("score", "overall", "combined", "health_score", "up_count", "down_count"):
        assert re.search(rf"\b{forbidden}\b", text.lower()) is None, forbidden
    registry_labels = [chs.DIMENSION_LABELS[key] for key in REGISTRY_KEYS]
    assert all("(registry)" in label for label in registry_labels), "registry-derived keys must say so"


def test_the_first_snapshot_history_round_trips_through_the_scorecard(tmp_path):
    _minimal_repo(tmp_path)
    history = tmp_path / "history.jsonl"
    assert chs.write_snapshot(tmp_path, history, craft_metrics=_craft()) is True
    scorecard = chs.build_scorecard(chs.read_snapshots(history))
    assert scorecard["no_snapshots_yet"] is False
    assert scorecard["dimensions"]["craft_baseline_rows"]["trend_label"] == chs.NO_TREND_DATA_LABEL
