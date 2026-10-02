"""Tests for tools/code_health/line_count.py and the code-health tool configuration
(TCK-20261002-CODE-HEALTH-TOOL-CONFIG).
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

from tools.code_health.line_count import (
    LEVEL_FAIL,
    LEVEL_FLAG,
    LEVEL_OK,
    LEVEL_WARN,
    Thresholds,
    load_thresholds,
    main,
    measure_paths,
    measure_source,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_LIMITS = Thresholds()


def _by_symbol(records):
    return {(r.kind, r.symbol): r for r in records}


def _function_of(n_lines: int, name: str = "f") -> str:
    """A function whose definition spans exactly n_lines physical lines."""
    return f"def {name}():\n" + "".join("    x = 1\n" for _ in range(n_lines - 1))


# ── Symbol naming ─────────────────────────────────────────────────────────────


def test_nested_function_and_method_with_same_name_get_distinct_symbols():
    source = (
        "class Worker:\n"
        "    def step(self):\n"
        "        return 1\n"
        "\n"
        "def step():\n"
        "    def step():\n"
        "        return 2\n"
        "    return step\n"
    )
    records = _by_symbol(measure_source(source, "m.py", _LIMITS))

    assert ("function", "Worker.step") in records
    assert ("function", "step") in records
    assert ("function", "step.<locals>.step") in records
    # Three different things, three different lengths and lines.
    assert records[("function", "Worker.step")].start_line == 2
    assert records[("function", "step")].start_line == 5
    assert records[("function", "step.<locals>.step")].start_line == 6
    assert records[("function", "step")].lines == 4
    assert records[("function", "step.<locals>.step")].lines == 2


def test_nested_class_method_and_async_function_symbols():
    source = (
        "class Outer:\n"
        "    class Inner:\n"
        "        def method(self):\n"
        "            pass\n"
        "\n"
        "async def run():\n"
        "    pass\n"
    )
    records = _by_symbol(measure_source(source, "m.py", _LIMITS))
    assert ("class", "Outer") in records
    assert ("class", "Outer.Inner") in records
    assert ("function", "Outer.Inner.method") in records
    assert ("function", "run") in records


def test_definitions_inside_conditional_blocks_are_found():
    source = (
        "try:\n"
        "    import fast\n"
        "except ImportError:\n"
        "    def helper():\n"
        "        pass\n"
        "if True:\n"
        "    class K:\n"
        "        def m(self):\n"
        "            pass\n"
    )
    records = _by_symbol(measure_source(source, "m.py", _LIMITS))
    assert ("function", "helper") in records
    assert ("function", "K.m") in records


def test_decorator_lines_count_towards_length():
    source = "@one\n@two\ndef f():\n    pass\n"
    record = _by_symbol(measure_source(source, "m.py", _LIMITS))[("function", "f")]
    assert (record.start_line, record.end_line, record.lines) == (1, 4, 4)


# ── Thresholds (roadmap 6.1: function warn >50 / fail >80, class >500, module >1,000) ──


@pytest.mark.parametrize(
    ("n_lines", "level"),
    [(50, LEVEL_OK), (51, LEVEL_WARN), (80, LEVEL_WARN), (81, LEVEL_FAIL)],
)
def test_function_length_levels_at_the_boundaries(n_lines, level):
    records = _by_symbol(measure_source(_function_of(n_lines), "m.py", _LIMITS))
    record = records[("function", "f")]
    assert record.lines == n_lines
    assert record.level == level


@pytest.mark.parametrize(("n_lines", "level"), [(500, LEVEL_OK), (501, LEVEL_FLAG)])
def test_class_length_levels_at_the_boundary(n_lines, level):
    source = "class C:\n" + "    x = 1\n" * (n_lines - 1)
    record = _by_symbol(measure_source(source, "m.py", _LIMITS))[("class", "C")]
    assert (record.lines, record.level) == (n_lines, level)


@pytest.mark.parametrize(("n_lines", "level"), [(1000, LEVEL_OK), (1001, LEVEL_FLAG)])
def test_module_length_levels_at_the_boundary(n_lines, level):
    source = "x = 1\n" * n_lines
    record = _by_symbol(measure_source(source, "m.py", _LIMITS))[("module", "<module>")]
    assert (record.lines, record.level) == (n_lines, level)


def test_empty_module_has_zero_lines():
    (record,) = measure_source("", "m.py", _LIMITS)
    assert (record.kind, record.lines, record.level) == ("module", 0, LEVEL_OK)


def test_outer_function_length_includes_nested_function():
    source = "def outer():\n    def inner():\n        pass\n    return inner\n"
    records = _by_symbol(measure_source(source, "m.py", _LIMITS))
    assert records[("function", "outer")].lines == 4
    assert records[("function", "outer.<locals>.inner")].lines == 2


# ── Paths, errors, determinism, CLI ───────────────────────────────────────────


def test_unparseable_file_is_reported_not_raised(tmp_path):
    (tmp_path / "good.py").write_text("def f():\n    pass\n")
    (tmp_path / "bad.py").write_text("def f(:\n")
    report = measure_paths([tmp_path])
    assert any(r.symbol == "f" for r in report.records)
    assert len(report.errors) == 1 and "bad.py" in report.errors[0]


def test_pycache_is_skipped_and_order_is_stable(tmp_path):
    (tmp_path / "b.py").write_text("def b():\n    pass\n")
    (tmp_path / "a.py").write_text("def a():\n    pass\n")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "c.py").write_text("def c():\n    pass\n")
    first = measure_paths([tmp_path])
    second = measure_paths([tmp_path])
    assert first == second
    paths = [r.path for r in first.records]
    assert paths == sorted(paths)
    assert not any("__pycache__" in p for p in paths)


def test_cli_json_flagged_only(tmp_path, capsys):
    (tmp_path / "big.py").write_text(_function_of(81, "huge") + _function_of(3, "tiny"))
    assert main([str(tmp_path), "--format", "json", "--flagged-only", "--pyproject", "none.toml"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [r["symbol"] for r in payload["records"]] == ["huge"]
    assert payload["records"][0]["level"] == LEVEL_FAIL
    assert payload["thresholds"]["function_fail_lines"] == 80


def test_cli_missing_path_exits_2(capsys):
    assert main(["definitely/not/here"]) == 2
    assert "no such path" in capsys.readouterr().err


# ── Configuration: thresholds live in one place and match roadmap 6.1 ─────────


def _pyproject() -> dict:
    return tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_size_thresholds_in_pyproject_match_roadmap_6_1():
    assert load_thresholds(_REPO_ROOT / "pyproject.toml") == Thresholds(
        function_warn_lines=50, function_fail_lines=80, class_lines=500, module_lines=1000
    )


def test_ruff_thresholds_match_roadmap_6_1_and_no_formatter_is_configured():
    ruff = _pyproject()["tool"]["ruff"]
    assert ruff["lint"]["mccabe"]["max-complexity"] == 10
    assert ruff["lint"]["pylint"]["max-args"] == 5
    assert ruff["lint"]["pylint"]["max-branches"] == 12
    assert ruff["lint"]["pylint"]["max-statements"] == 50
    assert ruff["lint"]["pylint"]["max-nested-blocks"] == 5
    assert "format" not in ruff, "no formatter is adopted (roadmap decision 8.3)"


def test_complexipy_cognitive_threshold_matches_roadmap_6_1():
    assert _pyproject()["tool"]["complexipy"]["max-complexity-allowed"] == 15


def test_lint_py_make_target_is_check_only():
    makefile = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^\.PHONY:.*\blint-py\b", makefile, re.M)
    recipe = re.search(r"^lint-py:.*\n((?:\t.*\n)+)", makefile, re.M)
    assert recipe, "lint-py target is missing"
    body = recipe.group(1)
    assert "ruff check" in body
    assert "ruff format" not in body
    assert "--fix" not in body
