#!/usr/bin/env python3
"""
Conservative codemod for migrating old V2EntityBuilder test usage to the fresh builder API.

It rewrites only builder chains that are proven to be rooted at:
- V2EntityBuilder(...)
- an import alias of V2EntityBuilder(...)
- a variable assigned from a V2EntityBuilder(...) chain

It does NOT globally replace method names like .items(), .position(), .inventory(), etc.

Dry-run:
    python scripts/migrate_v2_builder_chains.py tests

Write:
    python scripts/migrate_v2_builder_chains.py tests --write --backup
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path


SIMPLE_CHAIN_RENAMES = {
    ".with_identity(": ".identity(",
    ".with_inventory(": ".inventory(",
    ".with_inventory_component(": ".replace_inventory(",
    ".with_combat(": ".combat(",
    ".with_biological(": ".biological(",
    ".with_lifecycle(": ".lifecycle(",
    ".with_attributes(": ".attributes(",
    ".with_aptitude(": ".aptitude(",
    ".with_aptitudes(": ".aptitude(",
    ".with_navigation(": ".navigation(",
    ".with_strategic(": ".strategic(",
    ".with_strategic_profile(": ".cognition(",
    ".with_social(": ".social(",
    ".with_task(": ".task(",
    ".with_stamina(": ".stamina(",
    ".with_equipment(": ".equipment(",
}


MICRO_METHOD_REWRITES = [
    (r"\.readiness\(([^()]+?)\)", r".combat(readiness=\1)"),
    (r"\.atk\(([^()]+?)\)", r".combat(atk=\1)"),
    (r"\.def_stat\(([^()]+?)\)", r".combat(def_stat=\1)"),
    (r"\.move_cost\(([^()]+?)\)", r".combat(move_cost=\1)"),
    (r"\.alive\(([^()]+?)\)", r".combat(alive=\1)"),
    (r"\.faction\(([^()]+?)\)", r".identity(faction=\1)"),
    (r"\.role\(([^()]+?)\)", r".identity(role=\1)"),
    (r"\.evolution_level\(([^()]+?)\)", r".identity(evolution_level=\1)"),
]


MANUAL_REVIEW_METHODS = [
    ".item(",
    ".items(",
    ".gold(",
    ".max_slots(",
    ".with_property(",
    ".with_properties(",
    ".evolution(",
    ".current_project(",
    ".strategic_project(",
    ".strategic_contract(",
    ".with_contract(",
    ".strategic_directive(",
    ".with_directive(",
    ".source_trust(",
    ".social_bond(",
    ".bond(",
    ".bonds(",
    ".trust(",
]


@dataclass(frozen=True)
class Replacement:
    start: int
    end: int
    new_text: str


class BuilderChainScanner(ast.NodeVisitor):
    def __init__(self, source: str):
        self.source = source
        self.builder_constructor_names: set[str] = {"V2EntityBuilder"}
        self.builder_constructor_attrs: set[tuple[str, str]] = set()
        self.builder_variables: set[str] = set()
        self.builder_chain_calls: list[ast.Call] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module in {"src.core.builder", "src.core"}:
            for alias in node.names:
                if alias.name == "V2EntityBuilder":
                    self.builder_constructor_names.add(alias.asname or alias.name)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            # import src.core.builder as builder_mod
            if alias.name == "src.core.builder" and alias.asname:
                self.builder_constructor_attrs.add((alias.asname, "V2EntityBuilder"))

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._is_builder_chain(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.builder_variables.add(target.id)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None and self._is_builder_chain(node.value):
            if isinstance(node.target, ast.Name):
                self.builder_variables.add(node.target.id)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_builder_chain(node):
            self.builder_chain_calls.append(node)

        self.generic_visit(node)

    def _is_builder_constructor_call(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False

        func = node.func

        if isinstance(func, ast.Name):
            return func.id in self.builder_constructor_names

        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return (func.value.id, func.attr) in self.builder_constructor_attrs

        return False

    def _is_builder_variable(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Name) and node.id in self.builder_variables

    def _is_builder_chain(self, node: ast.AST) -> bool:
        """
        True for:
            V2EntityBuilder(...)
            V2EntityBuilder(...).kind(...).position(...)
            builder.kind(...)
        where builder is known to be assigned from V2EntityBuilder(...).
        """
        if self._is_builder_constructor_call(node):
            return True

        if self._is_builder_variable(node):
            return True

        if isinstance(node, ast.Call):
            return self._is_builder_chain(node.func)

        if isinstance(node, ast.Attribute):
            return self._is_builder_chain(node.value)

        return False


def line_offsets(source: str) -> list[int]:
    offsets = [0]
    total = 0

    for line in source.splitlines(keepends=True):
        total += len(line)
        offsets.append(total)

    return offsets


def node_span(source: str, node: ast.AST) -> tuple[int, int] | None:
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return None

    offsets = line_offsets(source)

    start = offsets[node.lineno - 1] + node.col_offset
    end = offsets[node.end_lineno - 1] + node.end_col_offset

    return start, end


def rewrite_builder_chain_text(text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []

    original = text

    for old, new in SIMPLE_CHAIN_RENAMES.items():
        text = text.replace(old, new)

    # .position((x, y)) / .at((x, y)) -> .location(x, y)
    text = re.sub(
        r"\.(position|at)\(\s*\(([^,\n()]+)\s*,\s*([^)]+?)\)\s*\)",
        r".location(\2, \3)",
        text,
    )

    # .position(x, y) / .at(x, y) -> .location(x, y)
    text = re.sub(
        r"\.(position|at)\(\s*([^,\n()]+)\s*,\s*([^)]+?)\s*\)",
        r".location(\2, \3)",
        text,
    )

    # .position(pos) / .at(pos) -> .location(*pos)
    text = re.sub(
        r"\.(position|at)\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
        r".location(*\2)",
        text,
    )

    # .hp(100, 100) -> .combat(hp=100, max_hp=100)
    text = re.sub(
        r"\.hp\(\s*([^,\n()]+)\s*,\s*([^)]+?)\s*\)",
        r".combat(hp=\1, max_hp=\2)",
        text,
    )

    # .hp(100) -> .combat(hp=100)
    text = re.sub(
        r"\.hp\(\s*([^,\n()]+)\s*\)",
        r".combat(hp=\1)",
        text,
    )

    for pattern, replacement in MICRO_METHOD_REWRITES:
        text = re.sub(pattern, replacement, text)

    for method in MANUAL_REVIEW_METHODS:
        if method in original:
            warnings.append(f"manual review required for builder-chain method {method}")

    return text, warnings


def collect_replacements(source: str, path: Path) -> tuple[list[Replacement], list[str]]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [], [f"{path}: cannot parse Python: {exc}"]

    scanner = BuilderChainScanner(source)
    scanner.visit(tree)

    replacements: list[Replacement] = []
    warnings: list[str] = []

    seen_spans: set[tuple[int, int]] = set()

    for node in scanner.builder_chain_calls:
        span = node_span(source, node)
        if span is None:
            continue

        start, end = span

        # Avoid rewriting nested sub-calls twice.
        # Keep only the widest chain for overlapping spans.
        if any(existing_start <= start and end <= existing_end for existing_start, existing_end in seen_spans):
            continue

        segment = source[start:end]
        rewritten, segment_warnings = rewrite_builder_chain_text(segment)

        for warning in segment_warnings:
            warnings.append(f"{path}:{node.lineno}: {warning}")

        if rewritten != segment:
            replacements.append(Replacement(start=start, end=end, new_text=rewritten))
            seen_spans.add((start, end))

    # Sort widest / later replacements safely.
    replacements.sort(key=lambda r: r.start, reverse=True)
    return replacements, warnings


def apply_replacements(source: str, replacements: list[Replacement]) -> str:
    result = source

    for replacement in replacements:
        result = (
            result[:replacement.start]
            + replacement.new_text
            + result[replacement.end:]
        )

    return result


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []

    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.py")))

    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--backup", action="store_true")
    args = parser.parse_args()

    files = iter_python_files([Path(p) for p in args.paths])

    changed: list[Path] = []
    all_warnings: list[str] = []

    for path in files:
        source = path.read_text()
        replacements, warnings = collect_replacements(source, path)
        all_warnings.extend(warnings)

        if not replacements:
            continue

        migrated = apply_replacements(source, replacements)

        if migrated != source:
            changed.append(path)

            if args.write:
                if args.backup:
                    path.with_suffix(path.suffix + ".bak").write_text(source)
                path.write_text(migrated)

    print(f"Scanned files: {len(files)}")
    print(f"Changed files: {len(changed)}")

    if changed:
        print("\nChanged files:")
        for path in changed:
            print(f"  {path}")

    if all_warnings:
        print("\nManual review required:")
        for warning in all_warnings:
            print(f"  {warning}")

    if not args.write:
        print("\nDry-run only. Re-run with --write to modify files.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())