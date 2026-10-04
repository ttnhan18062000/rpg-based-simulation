#!/usr/bin/env python3
"""Re-runnable table of every ``assert_perf_threshold`` / ``perf_check`` call site under ``tests/``.

Scans ``tests/`` with ``ast`` -- test code is never imported or executed -- and records for each
call: file, line, enclosing test function, which helper, the ``hard`` argument as written in source
(``True`` / ``False`` / absent / some other expression), the comparison operator, and the pytest
markers in force (function, enclosing class, and module-level ``pytestmark``). Markers matter
because ``.github/workflows/test.yml`` selects with ``-m "not slow and not extra_slow"`` on PRs.

Evidence only: nothing here measures anything, changes a threshold, or edits a test. Output has no
timestamps, so two runs on one tree are byte-identical.

    python3 tools/perf/perf_threshold_inventory.py --format json
    python3 tools/perf/perf_threshold_inventory.py --format md

Ticket: TCK-20261003-PERF-M2-CLAUSE-INVENTORY.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

TEST_ROOT = "tests"
HELPERS = ("assert_perf_threshold", "perf_check")
# The helper's own module defines the functions; its call sites are not checks.
HELPER_MODULE = "tests/tools/perf_assertions.py"


def _call_name(node: ast.Call) -> Optional[str]:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _marker_names(decorators: List[ast.expr]) -> List[str]:
    names: List[str] = []
    for dec in decorators:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Attribute):
            if target.value.attr == "mark":
                names.append(target.attr)
    return names


def _module_markers(tree: ast.Module) -> List[str]:
    names: List[str] = []
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in stmt.targets
        ):
            values = stmt.value.elts if isinstance(stmt.value, (ast.List, ast.Tuple)) else [stmt.value]
            names.extend(_marker_names(list(values)))
    return names


def _hard_argument(call: ast.Call) -> str:
    for kw in call.keywords:
        if kw.arg == "hard":
            if isinstance(kw.value, ast.Constant):
                return repr(kw.value.value)
            return "expr: " + ast.unparse(kw.value)
    return "absent"


def _limit_argument(call: ast.Call, helper: str) -> str:
    """Second positional argument (the limit) for assert_perf_threshold; the boolean expression for perf_check."""
    if helper == "assert_perf_threshold":
        arg = call.args[1] if len(call.args) > 1 else next((k.value for k in call.keywords if k.arg == "limit"), None)
    else:
        arg = call.args[0] if call.args else next((k.value for k in call.keywords if k.arg == "ok"), None)
    return ast.unparse(arg) if arg is not None else ""


def _op_argument(call: ast.Call, helper: str) -> str:
    if helper != "assert_perf_threshold":
        return ""
    for kw in call.keywords:
        if kw.arg == "op":
            if isinstance(kw.value, ast.Constant):
                return str(kw.value.value)
            return "expr: " + ast.unparse(kw.value)
    return "<="


class _Scanner(ast.NodeVisitor):
    def __init__(self, rel: str, module_markers: List[str]) -> None:
        self.rel = rel
        self.module_markers = module_markers
        self.stack: List[ast.AST] = []
        self.rows: List[Dict[str, Any]] = []

    def _visit_scope(self, node: ast.AST) -> None:
        self.stack.append(node)
        self.generic_visit(node)
        self.stack.pop()

    visit_ClassDef = _visit_scope
    visit_FunctionDef = _visit_scope
    visit_AsyncFunctionDef = _visit_scope

    def visit_Call(self, node: ast.Call) -> None:
        helper = _call_name(node)
        if helper in HELPERS:
            funcs = [n for n in self.stack if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            markers = list(self.module_markers)
            for scope in self.stack:
                markers.extend(_marker_names(scope.decorator_list))
            self.rows.append(
                {
                    "file": self.rel,
                    "line": node.lineno,
                    "function": ".".join(n.name for n in self.stack) if self.stack else "<module>",
                    "helper": helper,
                    "hard": _hard_argument(node),
                    "op": _op_argument(node, helper),
                    "limit": _limit_argument(node, helper),
                    "markers": sorted(set(markers) & {"slow", "extra_slow", "perf", "arena", "certification"}),
                    "in_test_function": bool(funcs) and funcs[-1].name.startswith("test"),
                }
            )
        self.generic_visit(node)


def build_report(root: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for path in sorted((root / TEST_ROOT).rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel == HELPER_MODULE:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not any(h in text for h in HELPERS):
            continue
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError:
            continue
        scanner = _Scanner(rel, _module_markers(tree))
        scanner.visit(tree)
        rows.extend(scanner.rows)
    rows.sort(key=lambda r: (r["file"], r["line"]))
    return {
        "call_sites": rows,
        "totals": {
            "all": len(rows),
            "assert_perf_threshold": sum(r["helper"] == "assert_perf_threshold" for r in rows),
            "perf_check": sum(r["helper"] == "perf_check" for r in rows),
            "hard_true": sum(r["hard"] == "True" for r in rows),
            "hard_false_or_absent": sum(r["hard"] in ("False", "absent") for r in rows),
            "hard_expression": sum(r["hard"].startswith("expr:") for r in rows),
            "slow_marked": sum(bool({"slow", "extra_slow"} & set(r["markers"])) for r in rows),
        },
    }


def to_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def to_markdown(report: Dict[str, Any]) -> str:
    totals = report["totals"]
    lines = [
        "| File | Line | Function | Helper | Limit (as written) | `hard` | `op` | Markers |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in report["call_sites"]:
        lines.append(
            f"| `{r['file']}` | {r['line']} | `{r['function']}` | `{r['helper']}` | "
            f"`{r['limit'].replace('|', chr(92) + '|')}` | `{r['hard']}` | {('`' + r['op'] + '`') if r['op'] else ''} | {', '.join(r['markers']) or '-'} |"
        )
    lines.append("")
    lines.append(
        "Totals: " + ", ".join(f"{k}={v}" for k, v in totals.items())
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root to scan (default: this checkout)")
    args = parser.parse_args(argv)
    report = build_report(Path(args.root).resolve())
    sys.stdout.write(to_json(report) if args.format == "json" else to_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
