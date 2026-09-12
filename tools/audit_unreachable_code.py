#!/usr/bin/env python3
"""
tools/audit_unreachable_code.py

Finds implemented-but-unreferenced code in src/: module-level functions/classes and class
methods with no real call site anywhere in the repo, outside their own definition.

TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT.

Method
------
AST-based definition collection (not grep-based). This repo's own prior dead-code audit
(docs/audits/D11_dead_code.md, 2026-06-18) used directory-level, grep-based import counting and
was later found to have a 100% false-positive rate (docs/audits/D11_dead_code.md's own
"Post-Audit Correction", 2026-06-23) -- every flagged "orphan" directory had a real importer the
grep missed, almost entirely from lazy/deferred imports (imports inside function bodies, which
this codebase uses heavily). This tool avoids that failure mode by tokenizing whole-file content
(catching every occurrence of an identifier regardless of where in the file it appears, lazy
imports included) rather than pattern-matching only `from X import` lines.

Two real methodology bugs were found and fixed while building this tool -- documented here so a
future revision doesn't reintroduce them:

1. **Same-file usage.** An early version only checked whether a name was referenced OUTSIDE its
   own defining file. This is wrong: a private helper called by a sibling function in the same
   module is alive, not dead (caught via `src/ai/coming_of_age.py::_personality_weight`, called
   from the same file at a different line). Fixed: count occurrences everywhere including the
   same file, then subtract only the definition line(s) themselves.

2. **Test-only usage.** An early version counted any occurrence anywhere in src/, tests/, or
   tools/ as "used" -- reachable. But this ticket's own definition of "unreachable" is code with
   "no live call site outside their own definition and their own tests": a function called ONLY
   by its own unit test, never from live production src/ code, is still "not actually reachable
   at runtime" by that definition. Counting test usage as "live" silently hid a known, already-
   confirmed instance (`effective_certainty()` in src/cognition/knowledge_model.py -- tested,
   never called from production) until this was fixed. Fixed: split occurrences into src/-only
   vs. tests/+tools/-only; a definition is a candidate if it has zero SRC references outside its
   own definition, regardless of test coverage. Test coverage is reported as a separate column
   (`has_test_coverage`), not folded into the reachability verdict.

False-positive exclusion (automated, decorator-based)
-------------------------------------------------------
Two categories are excluded automatically, with the excluding decorator recorded per entry so the
reasoning can be checked, not just trusted (per this ticket's own AC):

- **FastAPI route/websocket handlers** (`@router.get/post/put/delete/patch/websocket/options/head`,
  `@app.get` etc.) -- real entry points, invoked by the ASGI framework via URL routing, never
  called by their Python name anywhere in the codebase. This is exactly the "framework-invoked
  hooks" exclusion category named in the ticket's own Scope.
- **Pydantic validators** (`@field_validator`, `@model_validator`, `@validator`) -- real entry
  points, invoked automatically by Pydantic during model construction/validation, never called by
  name. Same exclusion category.

Known limitation (cannot be fixed by this tool's own approach)
----------------------------------------------------------------
Generic/common method names collide across many unrelated classes and defeat pure text-token
matching -- a real, structural limitation, not a bug. Confirmed directly:
`BiologicalSystem.update()` (src/systems/lifecycle_systems/biological.py) is a known, already-
confirmed dead method, but the bare identifier "update" appears thousands of times across this
codebase (every class with an `update()` method, plus the English word itself in comments/strings),
so it can never register as a zero-occurrence candidate here. This tool can only reliably flag
*distinctively-named* dead code. A collision can only produce a FALSE NEGATIVE (missing a real
dead method because its name is shared elsewhere), never a false positive (a zero-hit result
means the literal identifier text appears nowhere else in the whole corpus, regardless of
collision risk) -- the safer failure direction, but real coverage is still incomplete for common
names. A real fix would require type-aware call-graph analysis, out of this tool's own scope.

Usage
-----
    python3 tools/audit_unreachable_code.py [--json OUT.json] [--csv OUT.csv]

Prints a human-readable summary to stdout; --json/--csv write the full structured inventory.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SRC_ROOTS = [Path("src")]
TEST_TOOL_ROOTS = [Path("tests"), Path("tools")]
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

FASTAPI_DECORATORS = {"get", "post", "put", "delete", "patch", "websocket", "options", "head"}
PYDANTIC_VALIDATOR_DECORATORS = {"field_validator", "model_validator", "validator"}

# Dunder methods implicitly invoked by Python itself (construction, comparison, context
# management, iteration, etc.) -- excluded from Tier 2 (method) collection entirely, since
# "never called by name" is expected and meaningless for these.
DUNDER_SKIP = {
    "__init__", "__post_init__", "__repr__", "__str__", "__eq__", "__hash__", "__lt__", "__le__",
    "__gt__", "__ge__", "__ne__", "__call__", "__enter__", "__exit__", "__aenter__", "__aexit__",
    "__iter__", "__next__", "__len__", "__getitem__", "__setitem__", "__delitem__", "__contains__",
    "__bool__", "__new__", "__del__", "__copy__", "__deepcopy__", "__reduce__", "__getstate__",
    "__setstate__", "__aiter__", "__anext__",
}


def iter_py_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def decorator_names(dec_list: list[ast.expr]) -> list[str]:
    names = []
    for d in dec_list:
        if isinstance(d, ast.Name):
            names.append(d.id)
        elif isinstance(d, ast.Attribute):
            names.append(d.attr)
        elif isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
            names.append(d.func.attr)
        elif isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
            names.append(d.func.id)
    return names


def classify_decorators(dec: list[str]) -> str:
    dset = set(dec)
    if dset & FASTAPI_DECORATORS:
        return "fastapi_route"
    if dset & PYDANTIC_VALIDATOR_DECORATORS:
        return "pydantic_validator"
    return "real"


def collect_definitions() -> tuple[list[tuple], list[tuple]]:
    """Returns (toplevel_defs, methods). Each toplevel def is
    (name, file, lineno, kind, decorators). Each method is
    (name, file, lineno, class_name, decorators)."""
    toplevel_defs = []
    methods = []
    for root in SRC_ROOTS:
        for f in iter_py_files(root):
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            except SyntaxError as e:
                print(f"SYNTAX ERROR skipped: {f}: {e}", file=sys.stderr)
                continue
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    toplevel_defs.append((node.name, f, node.lineno, "function", decorator_names(node.decorator_list)))
                elif isinstance(node, ast.ClassDef):
                    toplevel_defs.append((node.name, f, node.lineno, "class", decorator_names(node.decorator_list)))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name in DUNDER_SKIP:
                                continue
                            methods.append((item.name, f, item.lineno, node.name, decorator_names(item.decorator_list)))
    return toplevel_defs, methods


def build_occurrence_index() -> tuple[dict, dict]:
    """Returns (src_occurrences, test_tool_occurrence_counts).
    src_occurrences: identifier -> {file: count}, scanning src/ only.
    test_tool_occurrence_counts: identifier -> total count, scanning tests/+tools/."""
    src_occurrences: dict[str, dict[Path, int]] = defaultdict(lambda: defaultdict(int))
    for root in SRC_ROOTS:
        for f in iter_py_files(root):
            try:
                content = f.read_text(encoding="utf-8")
            except Exception:
                continue
            for tok in IDENT_RE.findall(content):
                src_occurrences[tok][f] += 1

    test_tool_occurrences: dict[str, int] = defaultdict(int)
    for root in TEST_TOOL_ROOTS:
        for f in iter_py_files(root):
            try:
                content = f.read_text(encoding="utf-8")
            except Exception:
                continue
            for tok in IDENT_RE.findall(content):
                test_tool_occurrences[tok] += 1

    return src_occurrences, test_tool_occurrences


def run_audit() -> list[dict[str, Any]]:
    toplevel_defs, methods = collect_definitions()
    src_occurrences, test_tool_occurrences = build_occurrence_index()

    def_counts_per_file: dict[str, dict[Path, int]] = defaultdict(lambda: defaultdict(int))
    for name, deffile, lineno, kind, dec in toplevel_defs:
        def_counts_per_file[name][deffile] += 1
    for name, deffile, lineno, cls, dec in methods:
        def_counts_per_file[name][deffile] += 1

    def analyze(name: str, deffile: Path) -> tuple[bool, bool]:
        src_counts = src_occurrences.get(name, {})
        src_total = sum(src_counts.values())
        own = def_counts_per_file[name][deffile]
        real_src_call_sites = src_total - own
        is_candidate = real_src_call_sites <= 0
        has_test_coverage = test_tool_occurrences.get(name, 0) > 0
        return is_candidate, has_test_coverage

    rows: list[dict[str, Any]] = []

    for name, deffile, lineno, kind, dec in toplevel_defs:
        if name == "main":
            continue
        is_cand, has_tests = analyze(name, deffile)
        if not is_cand:
            continue
        rows.append({
            "tier": 1,
            "kind": kind,
            "class": None,
            "name": name,
            "file": str(deffile),
            "line": lineno,
            "decorators": dec,
            "exclusion": classify_decorators(dec),
            "has_test_coverage": has_tests,
        })

    for name, deffile, lineno, cls, dec in methods:
        is_cand, has_tests = analyze(name, deffile)
        if not is_cand:
            continue
        rows.append({
            "tier": 2,
            "kind": "method",
            "class": cls,
            "name": name,
            "file": str(deffile),
            "line": lineno,
            "decorators": dec,
            "exclusion": classify_decorators(dec),
            "has_test_coverage": has_tests,
        })

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", type=Path, default=None, help="Write full structured inventory as JSON")
    parser.add_argument("--csv", type=Path, default=None, help="Write full structured inventory as CSV")
    args = parser.parse_args()

    rows = run_audit()

    real = [r for r in rows if r["exclusion"] == "real"]
    excluded = [r for r in rows if r["exclusion"] != "real"]
    real_no_tests = [r for r in real if not r["has_test_coverage"]]
    real_test_only = [r for r in real if r["has_test_coverage"]]

    print(f"Total raw candidates (zero real src/ call sites outside own definition): {len(rows)}")
    print(f"  Excluded (framework-invoked hooks): {len(excluded)}")
    fastapi_n = sum(1 for r in excluded if r["exclusion"] == "fastapi_route")
    pydantic_n = sum(1 for r in excluded if r["exclusion"] == "pydantic_validator")
    print(f"    - FastAPI route/websocket handlers: {fastapi_n}")
    print(f"    - Pydantic validators: {pydantic_n}")
    print(f"  Real candidates: {len(real)}")
    print(f"    - Zero references anywhere (not even own tests): {len(real_no_tests)}")
    print(f"    - Test-only (tested, zero production callers): {len(real_test_only)}")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=2, default=str))
        print(f"\nWrote {len(rows)} rows to {args.json}")

    if args.csv:
        with args.csv.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=[
                "tier", "kind", "class", "name", "file", "line", "decorators",
                "exclusion", "has_test_coverage",
            ])
            writer.writeheader()
            for r in rows:
                row = dict(r)
                row["decorators"] = ";".join(row["decorators"])
                writer.writerow(row)
        print(f"Wrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
