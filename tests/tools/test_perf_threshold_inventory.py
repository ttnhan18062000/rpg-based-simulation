"""Tests for tools/perf/perf_threshold_inventory.py (TCK-20261003-PERF-M2-CLAUSE-INVENTORY).

The real-tree test checks properties (determinism, the helper module is excluded, the known soft
wrappers are reported as pass-through), never a line number or a total count: tests/perf keeps changing.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.perf import perf_threshold_inventory as pti

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "perf" / "perf_threshold_inventory.py"

SYNTHETIC = '''
import pytest
from tests.tools.perf_assertions import assert_perf_threshold, perf_check

pytestmark = [pytest.mark.perf]


@pytest.mark.slow
def test_soft_default():
    assert_perf_threshold(1.0, 2.0, "soft by default")


def test_hard_literal():
    assert_perf_threshold(1.0, 2.0, "hard", op="<", hard=True)


def test_explicit_false():
    assert_perf_threshold(3.0, 2.0, "explicit", op=">=", hard=False)


def helper(hard):
    perf_check(1 < 2, "wrapper", hard=hard)


class TestGroup:
    @pytest.mark.extra_slow
    def test_in_class(self):
        assert_perf_threshold(1.0, 2.0 * 3, "class marker")
'''


def _scan(tmp_path: Path, source: str):
    tests_dir = tmp_path / "tests" / "perf"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_synthetic.py").write_text(source, encoding="utf-8")
    return pti.build_report(tmp_path)


def _row(report, function):
    return next(r for r in report["call_sites"] if r["function"] == function)


def test_synthetic_hard_argument_forms(tmp_path):
    report = _scan(tmp_path, SYNTHETIC)
    assert _row(report, "test_soft_default")["hard"] == "absent"
    assert _row(report, "test_hard_literal")["hard"] == "True"
    assert _row(report, "test_explicit_false")["hard"] == "False"
    assert _row(report, "helper")["hard"] == "expr: hard"


def test_synthetic_op_limit_and_helper(tmp_path):
    report = _scan(tmp_path, SYNTHETIC)
    assert _row(report, "test_soft_default")["op"] == "<="
    assert _row(report, "test_hard_literal")["op"] == "<"
    assert _row(report, "test_explicit_false")["op"] == ">="
    assert _row(report, "TestGroup.test_in_class")["limit"] == "2.0 * 3"
    wrapper = _row(report, "helper")
    assert wrapper["helper"] == "perf_check"
    assert wrapper["op"] == ""
    assert wrapper["limit"] == "1 < 2"


def test_synthetic_markers_come_from_function_class_and_module(tmp_path):
    report = _scan(tmp_path, SYNTHETIC)
    assert _row(report, "test_soft_default")["markers"] == ["perf", "slow"]
    assert _row(report, "test_hard_literal")["markers"] == ["perf"]
    assert _row(report, "TestGroup.test_in_class")["markers"] == ["extra_slow", "perf"]


def test_synthetic_totals(tmp_path):
    totals = _scan(tmp_path, SYNTHETIC)["totals"]
    assert totals["all"] == 5
    assert totals["assert_perf_threshold"] == 4
    assert totals["perf_check"] == 1
    assert totals["hard_true"] == 1
    assert totals["hard_expression"] == 1
    assert totals["hard_false_or_absent"] == 3
    assert totals["slow_marked"] == 2


def test_helper_module_and_unparsable_files_are_skipped(tmp_path):
    tools_dir = tmp_path / "tests" / "tools"
    tools_dir.mkdir(parents=True)
    (tools_dir / "perf_assertions.py").write_text(
        "def assert_perf_threshold(a, b, m):\n    perf_check(True, m)\n", encoding="utf-8"
    )
    (tools_dir / "test_broken.py").write_text("assert_perf_threshold(\n", encoding="utf-8")
    assert pti.build_report(tmp_path)["call_sites"] == []


def test_markdown_escapes_pipes_in_limits(tmp_path):
    report = _scan(tmp_path, "def test_x():\n    assert_perf_threshold(1, a | b, 'm')\n")
    assert "a \\| b" in pti.to_markdown(report)


def test_real_tree_report_is_deterministic_and_well_formed():
    first = pti.to_json(pti.build_report(REPO_ROOT))
    second = pti.to_json(pti.build_report(REPO_ROOT))
    assert first == second
    report = json.loads(first)
    assert report["totals"]["all"] == len(report["call_sites"])
    assert all(r["file"] != pti.HELPER_MODULE for r in report["call_sites"])
    pass_through = [r for r in report["call_sites"] if r["hard"].startswith("expr:")]
    assert {r["file"] for r in pass_through} <= {
        "tests/perf/conftest.py",
        "tests/perf/test_perf_regression_baseline.py",
    }


def test_cli_markdown_and_json_runs_are_byte_identical():
    def run(fmt):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--format", fmt],
            check=True, capture_output=True, text=True, cwd=REPO_ROOT,
        ).stdout

    assert run("md") == run("md")
    assert json.loads(run("json"))["call_sites"]
