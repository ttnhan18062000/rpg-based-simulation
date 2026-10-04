"""Pick `exemplar_modules` for the package registry by a written, repeatable criterion.

A module qualifies as an exemplar when it is a `src/<package>/**/*.py` file that is not an
`__init__.py`, is 60 to 400 lines long, has a module docstring whose first line is not a path banner
(does not start with `src/` and does not end in `.py`; standard rule D2), has no row of any tool in
`codebase/baselines/code_health_exceptions.jsonl`, and is not in any registry row's `do_not_imitate`.
Qualifying modules are ranked by how many other `src` modules import them, then by path, and at most
`MAX_EXEMPLARS` are kept. Importing is a ranking preference, not a filter. `legacy` and `frozen`
packages get none. A package with no qualifying module gets `[]`, which is a valid result.

    python3 -m codebase.structure.exemplars measure   # print the picks per package, change nothing
    python3 -m codebase.structure.exemplars apply     # write them into package_registry.jsonl

`apply` rewrites only the `exemplar_modules` of rows whose picks change; every other row stays
byte-identical, so running it twice gives the same file. `reviewed` is never touched.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

from codebase.structure.packages import (
    MAX_EXEMPLARS,
    REPO_ROOT,
    load_rows,
    registry_path,
)

EXCEPTIONS_REL_PATH = Path("codebase/baselines/code_health_exceptions.jsonl")
MIN_LINES = 60
MAX_LINES = 400


def _dotted(path: Path, root: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _targets(tree: ast.AST, own: str, is_package: bool, modules: set[str]) -> set[str]:
    """Dotted names of the `src` modules this tree imports (absolute, relative and submodule forms)."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names if a.name in modules)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = own.split(".")
                if not is_package:
                    base.pop()
                base = base[: len(base) - (node.level - 1)]
                prefix = ".".join(base + ([node.module] if node.module else []))
            else:
                prefix = node.module or ""
            if prefix in modules:
                found.add(prefix)
            found.update(f"{prefix}.{a.name}" for a in node.names if f"{prefix}.{a.name}" in modules)
    return found


def importer_counts(root: Path) -> dict[str, int]:
    """How many other `src` modules import each repo-relative `src/...py` path."""
    files = sorted((root / "src").rglob("*.py"))
    modules = {_dotted(f, root): f.relative_to(root).as_posix() for f in files}
    counts: dict[str, int] = {}
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        own = _dotted(f, root)
        for name in _targets(tree, own, f.name == "__init__.py", set(modules)) - {own}:
            counts[modules[name]] = counts.get(modules[name], 0) + 1
    return counts


def _debt_files(root: Path) -> set[str]:
    path = root / EXCEPTIONS_REL_PATH
    if not path.is_file():
        return set()
    rows = (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return {row["file"] for row in rows}


def _qualifies(path: Path, root: Path) -> bool:
    if path.name == "__init__.py":
        return False
    text = path.read_text(encoding="utf-8")
    if not MIN_LINES <= len(text.splitlines()) <= MAX_LINES:
        return False
    try:
        doc = ast.get_docstring(ast.parse(text))
    except SyntaxError:
        return False
    if not doc:
        return False
    first = doc.splitlines()[0].strip()
    return not (first.startswith("src/") or first.endswith(".py"))  # a path banner is not a D2 sentence


def measure(root: Path = REPO_ROOT) -> dict[str, list[str]]:
    """Picks per package name for every row in the registry (`[]` for non-`active` rows)."""
    rows = load_rows(registry_path(root), root)
    avoid = {item["path"] for row in rows for item in row["do_not_imitate"]}
    debt = _debt_files(root)
    counts = importer_counts(root)
    picks: dict[str, list[str]] = {}
    for row in rows:
        name = row["package"]
        candidates = []
        if row["status"] == "active":
            for f in sorted((root / "src" / name).rglob("*.py")):
                rel = f.relative_to(root).as_posix()
                if rel not in debt and rel not in avoid and _qualifies(f, root):
                    candidates.append(rel)
        candidates.sort(key=lambda rel: (-counts.get(rel, 0), rel))
        picks[name] = candidates[:MAX_EXEMPLARS]
    return picks


def apply(root: Path = REPO_ROOT) -> int:
    """Rewrite `exemplar_modules` where the picks changed; returns the number of rows changed."""
    path = registry_path(root)
    picks = measure(root)
    out: list[str] = []
    changed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line) if line.strip() else None
        if row is not None and row["exemplar_modules"] != picks[row["package"]]:
            row["exemplar_modules"] = picks[row["package"]]
            line = json.dumps(row, sort_keys=True)
            changed += 1
        out.append(line)
    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    """Run `measure` or `apply`; exit 0."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("measure", "apply"))
    args = parser.parse_args(argv)
    if args.command == "apply":
        print(f"{apply()} row(s) changed")
        return 0
    for name, paths in measure().items():
        print(f"{name}: {', '.join(paths) if paths else '[]'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
