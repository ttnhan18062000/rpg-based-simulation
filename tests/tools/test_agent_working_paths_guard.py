"""Guard: live Python never spells an agent-working root; it imports tools/agent_working_paths.py.

A moved root (``tickets``, ``stored_artifacts``, ...) named in a path expression would silently keep pointing
at the pre-move location. This test parses every live ``.py`` file and flags a string literal that is used as
a path segment (right operand of ``/``, argument of ``Path(...)``/``os.path.join``/``glob``-style calls) or that
starts with ``<root>/``. Plain dictionary keys, prose and docstrings are not path uses and are ignored.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Tuple

import pytest

from tools.agent_working_paths import (
    AGENT_WORKING_ROOT,
    LEGACY_INDEX_NAMES,
    LEGACY_ROOT_NAMES,
    resolve_legacy_citation,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_DIRS = ("tools", "src", "tests")
CONSTANTS_MODULE = Path("tools/agent_working_paths.py")
THIS_TEST = Path("tests/tools/test_agent_working_paths_guard.py")
_ROOTS = frozenset(LEGACY_ROOT_NAMES) | frozenset(LEGACY_INDEX_NAMES)
_PATH_CALLS = frozenset({"Path", "PurePath", "join", "joinpath", "glob", "rglob", "exists", "is_dir", "is_file"})
# Left operands that denote the tool-script tree: ``tools/agent-monitoring/`` is a different folder from the
# ``agent-monitoring/`` data root and stays where it is; ``docs/agent-monitoring/`` is documentation.
_TOOL_TREE_HINTS = ("tools", "_tools", "TOOLS", "script", "docs")


def _name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _name_of(node.func)
    if isinstance(node, ast.BinOp):
        return _name_of(node.left)
    return ""


def _is_root_literal(node: ast.AST) -> bool:
    if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
        return False
    value = node.value
    return value in _ROOTS or any(value.startswith(f"{r}/") for r in _ROOTS)


def _under_tool_tree(left: ast.AST) -> bool:
    text = ast.unparse(left)
    return any(hint in text for hint in _TOOL_TREE_HINTS) or "parent" in text


def find_violations(source: str) -> List[Tuple[int, str]]:
    """Return ``(line, literal)`` for every root literal used as a path expression."""
    tree = ast.parse(source)
    found: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            if _is_root_literal(node.right) and not _under_tool_tree(node.left):
                found.append((node.right.lineno, node.right.value))
            elif _is_root_literal(node.left):
                found.append((node.left.lineno, node.left.value))
        elif isinstance(node, ast.Call) and _name_of(node.func) in _PATH_CALLS:
            for arg in node.args:
                if _is_root_literal(arg) and not _under_tool_tree(node.func):
                    found.append((arg.lineno, arg.value))
    return sorted(set(found))


def _live_python_files() -> List[Path]:
    files: List[Path] = []
    for top in LIVE_DIRS:
        files.extend(p for p in (REPO_ROOT / top).rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(files)


def test_no_live_code_names_a_moved_root() -> None:
    offenders = []
    for path in _live_python_files():
        rel = path.relative_to(REPO_ROOT)
        if rel in (CONSTANTS_MODULE, THIS_TEST):
            continue
        for line, literal in find_violations(path.read_text(encoding="utf-8")):
            offenders.append(f"{rel}:{line}: {literal!r}")
    assert not offenders, "hardcoded agent-working root (use tools.agent_working_paths):\n" + "\n".join(offenders)


@pytest.mark.parametrize(
    "snippet",
    [
        'x = root / "tickets" / "done"\n',
        'x = Path("stored_artifacts")\n',
        'x = os.path.join(base, "agent-monitoring", "data")\n',
        'x = sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl"))\n',
        'x = "tickets/working_log.csv"\n' + 'y = Path("tickets/working_log.csv")\n',
    ],
)
def test_guard_flags_seeded_hardcoded_root(snippet: str) -> None:
    assert find_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        'x = {"tickets": 3}\n',
        'x = _TOOLS_DIR / "agent-monitoring"\n',
        'x = Path(__file__).resolve().parent / "agent-monitoring" / "writer.py"\n',
        'from tools.agent_working_paths import TICKETS\nx = root / TICKETS / "done"\n',
    ],
)
def test_guard_ignores_non_path_uses_and_the_constants(snippet: str) -> None:
    assert not find_violations(snippet), snippet


def test_legacy_citation_resolves_for_each_root() -> None:
    for name in LEGACY_ROOT_NAMES:
        expected = (AGENT_WORKING_ROOT / name / "x.md").as_posix()
        assert resolve_legacy_citation(f"{name}/x.md") == expected
    assert resolve_legacy_citation("docs/x.md") == "docs/x.md"
