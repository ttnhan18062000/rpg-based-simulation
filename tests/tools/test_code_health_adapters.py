"""Tests for tools/code_health/adapters.py and findings.py (TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY).

The JSON fixtures in tests/fixtures/code_health/ are the real output of ruff 0.16.10, complexipy
8.0.1, jscpd 5.4.0 and `tools.code_health.line_count`, run over tests/fixtures/code_health/sample_src/
(a few files with deliberate violations). To recapture: copy sample_src, pyproject.toml and
.jscpd.json to a scratch directory, run each tool there (ruff `check sample_src --output-format
json`; `complexipy sample_src -q --output-format json --output complexipy.json`; `npx jscpd@5.4.0
sample_src --config .jscpd.json --output jscpd`; `python3 -m tools.code_health.line_count
sample_src --format json`), and replace the scratch directory in ruff.json with `/FIXTURE_ROOT`
(ruff prints absolute paths; that substitution is the only edit).
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.code_health.adapters import (
    RULE_COGNITIVE,
    RULE_DUPLICATE,
    adapt_complexipy,
    adapt_jscpd,
    adapt_line_count,
    adapt_ruff,
)
from tools.code_health.findings import Finding, aggregate

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "code_health"


def _fixture(name: str):
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


# ── ruff ──────────────────────────────────────────────────────────────────────


def test_ruff_adapter_normalises_real_output_to_one_count_per_file_and_rule():
    raw = _fixture("ruff.json")
    findings = adapt_ruff(raw, "/FIXTURE_ROOT")

    assert sum(f.value for f in findings) == len(raw) == 17
    assert all(f.tool == "ruff" and f.symbol is None for f in findings)
    assert all(not f.file.startswith("/") for f in findings), "paths are relative to the root"
    by_key = {f.key: f for f in findings}
    assert by_key[("sample_src/bad.py", None, "ruff", "E722")].value == 1
    assert by_key[("sample_src/bad.py", None, "ruff", "B006")].value == 1
    assert ("sample_src/bad.py", None, "ruff", "C901") in by_key
    assert ("sample_src/long.py", None, "ruff", "PLR0915") in by_key
    # Several findings of one rule in one file collapse to a single record with a count.
    assert by_key[("sample_src/bad.py", None, "ruff", "ANN001")].value == 2


def test_ruff_adapter_is_independent_of_line_numbers():
    raw = _fixture("ruff.json")
    moved = json.loads(json.dumps(raw))
    for record in moved:
        record["location"]["row"] += 100
    assert adapt_ruff(raw, "/FIXTURE_ROOT") == adapt_ruff(moved, "/FIXTURE_ROOT")


def test_ruff_adapter_keeps_path_outside_root_and_reports_syntax_errors():
    records = [
        {"code": None, "filename": "/elsewhere/x.py", "location": {"row": 1, "column": 1}},
        {"code": "F401", "filename": "/elsewhere/x.py", "location": {"row": 3, "column": 1}},
    ]
    findings = {f.rule: f for f in adapt_ruff(records, "/FIXTURE_ROOT")}
    assert findings["syntax-error"].file == "/elsewhere/x.py"
    assert findings["F401"].value == 1


# ── complexipy ────────────────────────────────────────────────────────────────


def test_complexipy_adapter_keeps_only_functions_over_the_limit():
    findings = adapt_complexipy(_fixture("complexipy.json"), max_allowed=15)
    got = {f.key: f.value for f in findings}
    assert got == {
        ("sample_src/bad.py", "risky", "complexipy", RULE_COGNITIVE): 41,
        ("sample_src/dup_a.py", "first_copy", "complexipy", RULE_COGNITIVE): 18,
        ("sample_src/dup_b.py", "second_copy", "complexipy", RULE_COGNITIVE): 18,
    }


def test_complexipy_adapter_qualifies_method_names_and_keeps_the_larger_of_a_repeated_name():
    records = [
        {"complexity": 20, "function_name": "Worker::step", "path": "src/w.py"},
        {"complexity": 30, "function_name": "prop", "path": "src/w.py"},
        {"complexity": 17, "function_name": "prop", "path": "src/w.py"},
    ]
    got = {f.symbol: f.value for f in adapt_complexipy(records, max_allowed=15)}
    assert got == {"Worker.step": 20, "prop": 30}


# ── jscpd ─────────────────────────────────────────────────────────────────────


def test_jscpd_adapter_keys_a_clone_by_its_ordered_file_pair():
    findings = adapt_jscpd(_fixture("jscpd-report.json"), scan_root="sample_src")
    assert findings == [
        Finding("sample_src/dup_a.py", "dup:sample_src/dup_b.py", "jscpd", RULE_DUPLICATE, 24)
    ]


def test_jscpd_adapter_gives_the_same_key_whichever_file_is_listed_first_and_sums_a_pair():
    def clone(first: str, second: str, lines: int) -> dict:
        return {"firstFile": {"name": first, "start": 1}, "secondFile": {"name": second, "start": 9}, "lines": lines}

    forward = adapt_jscpd({"duplicates": [clone("a.py", "b.py", 10), clone("a.py", "b.py", 5)]}, "src")
    backward = adapt_jscpd({"duplicates": [clone("b.py", "a.py", 10), clone("b.py", "a.py", 5)]}, "src")
    assert [f.key for f in forward] == [f.key for f in backward] == [("src/a.py", "dup:src/b.py", "jscpd", RULE_DUPLICATE)]
    assert forward[0].value == backward[0].value == 15


# ── line count ────────────────────────────────────────────────────────────────


def test_line_count_adapter_keeps_functions_over_the_fail_limit_only():
    findings = adapt_line_count(_fixture("line_count.json"))
    assert findings == [Finding("sample_src/long.py", "long_function", "line_count", "function-length", 86)]


def test_line_count_adapter_maps_classes_and_modules_and_takes_the_max_for_a_repeated_symbol():
    def record(kind: str, symbol: str, lines: int, level: str, start: int = 1) -> dict:
        return {"path": "src/m.py", "kind": kind, "symbol": symbol, "lines": lines, "level": level, "start_line": start}

    report = {
        "records": [
            record("module", "<module>", 1200, "flag"),
            record("class", "Big", 600, "flag"),
            record("class", "Small", 10, "ok"),
            record("function", "Big.value", 90, "fail", start=10),  # property getter
            record("function", "Big.value", 120, "fail", start=200),  # property setter, same key
            record("function", "Big.other", 60, "warn"),
        ]
    }
    got = {(f.symbol, f.rule): f.value for f in adapt_line_count(report)}
    assert got == {
        (None, "module-length"): 1200,
        ("Big", "class-length"): 600,
        ("Big.value", "function-length"): 120,
    }


# ── findings ──────────────────────────────────────────────────────────────────


def test_finding_equality_and_key_ignore_the_display_line():
    assert Finding("a.py", None, "ruff", "F401", 2, line=3) == Finding("a.py", None, "ruff", "F401", 2, line=900)
    assert Finding("a.py", "f", "t", "r", 1).key == ("a.py", "f", "t", "r")


def test_aggregate_sums_counts_or_keeps_the_max_and_is_sorted():
    items = [Finding("b.py", None, "ruff", "X", 1), Finding("a.py", None, "ruff", "X", 2), Finding("a.py", None, "ruff", "X", 3)]
    assert [(f.file, f.value) for f in aggregate(items, "sum")] == [("a.py", 5), ("b.py", 1)]
    assert [(f.file, f.value) for f in aggregate(items, "max")] == [("a.py", 3), ("b.py", 1)]
