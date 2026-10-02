"""Tests for tools/code_health/metrics.py and the offline scan subset (TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from tools.code_health import scan
from tools.code_health.findings import Finding
from tools.code_health.metrics import (
    CRAFT_LABELS,
    CRAFT_METRIC_KEYS,
    LIVE_KEYS,
    REGISTRY_KEYS,
    compute_craft_metrics,
)
from tools.code_health.registry import Row

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "code_health"


def _f(tool: str, rule: str, value: int, symbol: str | None = None, file: str = "a.py") -> Finding:
    return Finding(file, symbol, tool, rule, value)


def _row(tool: str, rule: str, value: int, reviewed: bool = False, file: str = "a.py", symbol: str | None = None) -> Row:
    return Row(file, symbol, tool, rule, value, value, "2026-10-02", reviewed, None)


def test_every_metric_is_present_and_an_int_for_empty_input():
    metrics = compute_craft_metrics([], [])
    assert set(metrics) == set(CRAFT_METRIC_KEYS)
    assert all(isinstance(v, int) and v == 0 for v in metrics.values())


def test_key_sets_are_disjoint_labelled_and_name_no_aggregate():
    assert set(LIVE_KEYS).isdisjoint(REGISTRY_KEYS)
    assert set(CRAFT_LABELS) == set(CRAFT_METRIC_KEYS)
    assert all(key.startswith("craft_") for key in CRAFT_METRIC_KEYS)
    assert all(key.startswith("craft_baseline_") for key in REGISTRY_KEYS)
    assert not any(key.startswith("craft_baseline_") for key in LIVE_KEYS)
    denylist = {"score", "overall", "combined", "summary", "health", "total"}
    for key in CRAFT_METRIC_KEYS:
        assert denylist.isdisjoint(set(key.split("_"))), key
    for label in CRAFT_LABELS.values():
        assert re.search(r"\b(score|overall|combined)\b", label.lower()) is None, label


def test_live_metrics_count_each_dimension_separately():
    findings = [
        _f("ruff", "F401", 4, file="a.py"),
        _f("ruff", "F821", 2, file="b.py"),
        _f("ruff", "E902", 1),
        _f("ruff", "D100", 3),
        _f("ruff", "D102", 5, file="b.py"),
        _f("ruff", "ANN001", 7),
        _f("ruff", "ANN201", 1),
        _f("ruff", "C901", 6),
        _f("complexipy", "cognitive-complexity", 40, symbol="f"),
        _f("complexipy", "cognitive-complexity", 18, symbol="g"),
        _f("line_count", "function-length", 120, symbol="f"),
        _f("line_count", "function-length", 90, symbol="g"),
        _f("line_count", "function-length", 85, symbol="h"),
        _f("line_count", "class-length", 600, symbol="K"),
        _f("line_count", "module-length", 1200),
        _f("jscpd", "duplicate-block", 99, symbol="dup:b.py"),  # a clone is not a live key here
    ]
    metrics = compute_craft_metrics(findings, [])
    assert metrics["craft_ruff_findings"] == 4 + 2 + 1 + 3 + 5 + 7 + 1 + 6
    assert metrics["craft_correctness_findings"] == 4 + 2 + 1  # F401, F821 and E902 (an E9 rule)
    assert metrics["craft_missing_public_docstrings"] == 8
    assert metrics["craft_missing_annotations"] == 8
    assert metrics["craft_functions_over_cognitive_limit"] == 2
    assert metrics["craft_functions_over_length_limit"] == 3
    assert metrics["craft_classes_over_length_limit"] == 1
    assert metrics["craft_modules_over_length_limit"] == 1
    assert metrics["craft_longest_function_lines"] == 120
    assert metrics["craft_highest_cognitive_complexity"] == 40


def test_correctness_matches_pyflakes_and_e9_exactly_not_any_f_prefix():
    findings = [_f("ruff", "F401", 1), _f("ruff", "FURB105", 10), _f("ruff", "FBT001", 100), _f("ruff", "E902", 1000)]
    metrics = compute_craft_metrics(findings, [])
    assert metrics["craft_correctness_findings"] == 1001
    assert metrics["craft_ruff_findings"] == 1111  # the total still counts every selected rule


def test_docstring_and_annotation_families_match_exactly():
    findings = [_f("ruff", "D100", 1), _f("ruff", "D104", 2), _f("ruff", "D105", 4), _f("ruff", "D200", 8),
                _f("ruff", "ANN001", 16), _f("ruff", "ANN401", 32), _f("ruff", "ANNOTATION", 64)]
    metrics = compute_craft_metrics(findings, [])
    assert metrics["craft_missing_public_docstrings"] == 3
    assert metrics["craft_missing_annotations"] == 48


def test_e9_syntax_errors_count_as_correctness():
    assert compute_craft_metrics([_f("ruff", "E902", 1)], [])["craft_correctness_findings"] == 1
    assert compute_craft_metrics([_f("ruff", "E722", 1)], [])["craft_correctness_findings"] == 0


def test_registry_metrics_come_from_the_rows_only():
    rows = [
        _row("ruff", "F401", 5, reviewed=True),
        _row("ruff", "D100", 1),
        _row("jscpd", "duplicate-block", 24, file="a.py", symbol="dup:b.py"),
        _row("jscpd", "duplicate-block", 10, file="a.py", symbol="dup:c.py", reviewed=True),
    ]
    metrics = compute_craft_metrics([_f("ruff", "F401", 1)], rows)
    assert metrics["craft_baseline_rows"] == 4
    assert metrics["craft_baseline_unreviewed_rows"] == 2
    assert metrics["craft_baseline_duplicate_file_pairs"] == 2
    assert metrics["craft_baseline_duplicated_lines"] == 34
    assert metrics["craft_ruff_findings"] == 1  # live keys ignore the registry


def test_offline_scan_subset_needs_no_jscpd_output(tmp_path):
    scan_dir = tmp_path / "scan"
    scan_dir.mkdir()
    ruff = (_FIXTURES / "ruff.json").read_text().replace("/FIXTURE_ROOT", str(tmp_path))
    (scan_dir / "ruff.json").write_text(ruff)
    shutil.copy(_FIXTURES / "complexipy.json", scan_dir / "complexipy.json")
    shutil.copy(_FIXTURES / "line_count.json", scan_dir / "line_count.json")  # no jscpd directory at all
    findings = scan.collect_findings(scan_dir, tmp_path, tools=scan.OFFLINE_TOOLS)
    assert findings and not any(f.tool == "jscpd" for f in findings)
    metrics = compute_craft_metrics(findings, [])
    assert metrics["craft_ruff_findings"] == 17
    assert metrics["craft_functions_over_cognitive_limit"] == 3
    assert metrics["craft_longest_function_lines"] == 86
    with pytest.raises(scan.ToolUnavailableError):
        scan.collect_findings(scan_dir, tmp_path)  # all four tools: the missing jscpd report is reported


def test_offline_tools_exclude_jscpd_and_all_tools_include_it():
    assert "jscpd" not in scan.OFFLINE_TOOLS and "jscpd" in scan.ALL_TOOLS
    assert set(scan.OFFLINE_TOOLS) < set(scan.ALL_TOOLS)


def test_complexity_limit_defaults_when_there_is_no_pyproject(tmp_path):
    assert scan.complexity_limit(tmp_path / "missing.toml") == scan.DEFAULT_COMPLEXITY_LIMIT
