"""Report the length of every module, class and function under the given paths.

No other tool in the toolchain measures lines per function, class and module with a stable
symbol name, so this does (python_code_craft_roadmap.md section 6.2; python_code_standard.md
rules S1, S8 and S9). It is a measurement, not a gate: it always exits 0 for a readable tree.
The ratchet that fails on new or worse violations is TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY.

Symbol names follow Python's own `__qualname__` convention, so two things that share a bare name
in one file stay distinct:

- a method:           `Worker.step`
- a module function:  `step`
- a nested function:  `step.<locals>.step`
- a nested class:     `Outer.Inner.method`

Length is physical lines from the first decorator (or the `def`/`class` line) to the last line of
the body, inclusive, so a function's length includes anything nested inside it. A module's length
is the number of lines in the file.

Thresholds come from `[tool.code_health.size]` in pyproject.toml, the single place they are
configured; the defaults below apply only when the table or a key is missing.

    python3 -m tools.code_health.line_count src --flagged-only
    python3 -m tools.code_health.line_count src --format json
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator, Sequence

DEFAULT_PYPROJECT = Path("pyproject.toml")

LEVEL_OK = "ok"
LEVEL_WARN = "warn"
LEVEL_FAIL = "fail"
LEVEL_FLAG = "flag"

KIND_MODULE = "module"
KIND_CLASS = "class"
KIND_FUNCTION = "function"

MODULE_SYMBOL = "<module>"


@dataclass(frozen=True)
class Thresholds:
    """Length limits for new or changed code (python_code_standard.md section 4)."""

    function_warn_lines: int = 50
    function_fail_lines: int = 80
    class_lines: int = 500
    module_lines: int = 1000


@dataclass(frozen=True)
class SizeRecord:
    """One measured module, class or function."""

    path: str
    kind: str
    symbol: str
    start_line: int
    end_line: int
    lines: int
    level: str


@dataclass(frozen=True)
class Report:
    """Every record found under the scanned paths, plus files that could not be parsed."""

    thresholds: Thresholds
    records: tuple[SizeRecord, ...]
    errors: tuple[str, ...]


def load_thresholds(pyproject: Path = DEFAULT_PYPROJECT) -> Thresholds:
    """Read `[tool.code_health.size]`; fall back to the defaults for anything missing."""
    defaults = Thresholds()
    if not pyproject.is_file():
        return defaults
    with pyproject.open("rb") as handle:
        table = tomllib.load(handle).get("tool", {}).get("code_health", {}).get("size", {})
    return Thresholds(
        function_warn_lines=int(table.get("function-warn-lines", defaults.function_warn_lines)),
        function_fail_lines=int(table.get("function-fail-lines", defaults.function_fail_lines)),
        class_lines=int(table.get("class-lines", defaults.class_lines)),
        module_lines=int(table.get("module-lines", defaults.module_lines)),
    )


def _function_level(lines: int, limits: Thresholds) -> str:
    if lines > limits.function_fail_lines:
        return LEVEL_FAIL
    if lines > limits.function_warn_lines:
        return LEVEL_WARN
    return LEVEL_OK


def _flag_level(lines: int, limit: int) -> str:
    return LEVEL_FLAG if lines > limit else LEVEL_OK


def _span(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> tuple[int, int]:
    start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    return start, node.end_lineno or node.lineno


def _walk(
    body: Sequence[ast.stmt], prefix: str, path: str, limits: Thresholds
) -> Iterator[SizeRecord]:
    for node in body:
        if isinstance(node, ast.ClassDef):
            symbol = f"{prefix}{node.name}"
            start, end = _span(node)
            lines = end - start + 1
            yield SizeRecord(
                path, KIND_CLASS, symbol, start, end, lines, _flag_level(lines, limits.class_lines)
            )
            yield from _walk(node.body, f"{symbol}.", path, limits)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbol = f"{prefix}{node.name}"
            start, end = _span(node)
            lines = end - start + 1
            yield SizeRecord(
                path, KIND_FUNCTION, symbol, start, end, lines, _function_level(lines, limits)
            )
            yield from _walk(node.body, f"{symbol}.<locals>.", path, limits)
        else:
            # Definitions can sit inside if/try/with/for blocks (conditional imports, fallbacks).
            for child_body in _child_bodies(node):
                yield from _walk(child_body, prefix, path, limits)


def _child_bodies(node: ast.stmt) -> Iterator[list[ast.stmt]]:
    for field in ("body", "orelse", "finalbody"):
        value = getattr(node, field, None)
        if isinstance(value, list) and value and isinstance(value[0], ast.stmt):
            yield value
    for handler in getattr(node, "handlers", []):
        yield handler.body
    for case in getattr(node, "cases", []):
        yield case.body


def measure_source(source: str, path: str, limits: Thresholds | None = None) -> list[SizeRecord]:
    """Measure one module's source text. Raises SyntaxError if it does not parse."""
    limits = limits or Thresholds()
    tree = ast.parse(source, filename=path)
    total = len(source.splitlines())
    module = SizeRecord(
        path, KIND_MODULE, MODULE_SYMBOL, 1, total, total, _flag_level(total, limits.module_lines)
    )
    return [module, *_walk(tree.body, "", path, limits)]


def _python_files(paths: Sequence[Path]) -> list[Path]:
    found: set[Path] = set()
    for root in paths:
        if root.is_file():
            found.add(root)
        else:
            found.update(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(found, key=lambda p: p.as_posix())


def measure_paths(paths: Sequence[Path], limits: Thresholds | None = None) -> Report:
    """Measure every `.py` file under `paths`, in a stable order."""
    limits = limits or Thresholds()
    records: list[SizeRecord] = []
    errors: list[str] = []
    for file in _python_files(paths):
        posix = file.as_posix()
        try:
            records.extend(measure_source(file.read_text(encoding="utf-8"), posix, limits))
        except (SyntaxError, UnicodeDecodeError, ValueError) as exc:
            errors.append(f"{posix}: {type(exc).__name__}: {exc}")
    records.sort(key=lambda r: (r.path, r.start_line, r.symbol))
    return Report(limits, tuple(records), tuple(errors))


def _format_text(report: Report, flagged_only: bool) -> str:
    shown = [r for r in report.records if not (flagged_only and r.level == LEVEL_OK)]
    lines = [
        f"{r.path}:{r.start_line} {r.kind} {r.symbol} {r.lines} lines [{r.level}]" for r in shown
    ]
    counts: dict[str, int] = {}
    for record in report.records:
        counts[record.level] = counts.get(record.level, 0) + 1
    summary = ", ".join(f"{level}={counts[level]}" for level in sorted(counts))
    lines.append(f"-- {len(report.records)} symbols measured ({summary}); {len(report.errors)} unreadable")
    lines.extend(f"unreadable: {error}" for error in report.errors)
    return "\n".join(lines)


def _format_json(report: Report, flagged_only: bool) -> str:
    return json.dumps(
        {
            "thresholds": asdict(report.thresholds),
            "records": [
                asdict(r) for r in report.records if not (flagged_only and r.level == LEVEL_OK)
            ],
            "errors": list(report.errors),
        },
        indent=2,
        sort_keys=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point. Returns 0, or 2 if a given path does not exist."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("src")])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--flagged-only", action="store_true", help="omit symbols within limits")
    parser.add_argument("--pyproject", type=Path, default=DEFAULT_PYPROJECT)
    args = parser.parse_args(argv)

    missing = [p for p in args.paths if not p.exists()]
    if missing:
        print(f"error: no such path: {', '.join(str(p) for p in missing)}", file=sys.stderr)
        return 2

    report = measure_paths(args.paths, load_thresholds(args.pyproject))
    formatter = _format_json if args.format == "json" else _format_text
    print(formatter(report, args.flagged_only))
    return 0


if __name__ == "__main__":
    sys.exit(main())
