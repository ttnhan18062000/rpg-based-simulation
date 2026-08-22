"""Guards src/rendering/ against ever gaining a third-party dependency (e.g. numpy).

TCK-20260821-WORLD-RENDER-CORE: the renderer must stay pure-stdlib. This is a
permanent static check against the files on disk, mirroring
tests/architecture/test_phase18_import_boundaries.py's general shape — not a
one-time, hardcoded-import-list check.
"""
from __future__ import annotations

import ast
import os
import sys

_STDLIB_MODULE_NAMES = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()

_ALLOWED_TOP_LEVEL_PREFIXES = ("src",)


def _iter_py_files(root_dir: str):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                yield path, os.path.relpath(path).replace(os.sep, "/")


def _top_level_module(name: str) -> str:
    return name.split(".", 1)[0]


def _is_allowed(top_level: str) -> bool:
    if top_level in _STDLIB_MODULE_NAMES:
        return True
    if top_level == "__future__":
        return True
    if top_level.startswith(_ALLOWED_TOP_LEVEL_PREFIXES):
        return True
    return False


def test_render_no_new_third_party_dependency():
    violations = []
    for path, rel_path in _iter_py_files("src/rendering"):
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = _top_level_module(alias.name)
                    if not _is_allowed(top):
                        violations.append(f"{rel_path}:{node.lineno} imports {alias.name!r}")
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import within src.rendering itself
                module = node.module or ""
                top = _top_level_module(module)
                if not _is_allowed(top):
                    violations.append(f"{rel_path}:{node.lineno} imports from {module!r}")

    assert not violations, (
        "src/rendering/ must remain pure-stdlib (zero new third-party dependency, "
        "e.g. no numpy) per TCK-20260821-WORLD-RENDER-CORE's explicit Out of Scope — "
        f"found: {violations}"
    )
