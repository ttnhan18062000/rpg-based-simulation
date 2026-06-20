"""
Architecture guard: no API route/ws/server file may directly import AuthoritativeState
outside a TYPE_CHECKING block.
"""
from __future__ import annotations
import ast
import pathlib
import pytest

_API_ROOTS = [
    pathlib.Path("src/api/routes"),
    pathlib.Path("src/api/ws"),
    pathlib.Path("src/api/server.py"),
]

_FORBIDDEN_NAMES = {"AuthoritativeState", "EntityState"}


def _source_files():
    files = []
    for root in _API_ROOTS:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(root.rglob("*.py"))
    return files


def _imports_forbidden_name_outside_type_checking(path: pathlib.Path) -> list[str]:
    """Return list of violation descriptions found in the file."""
    source = path.read_text()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    violations = []
    inside_type_checking: set[int] = set()

    # Identify line ranges covered by `if TYPE_CHECKING:` blocks
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_tc = (
                (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING")
                or (isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")
            )
            if is_tc:
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        inside_type_checking.add(child.lineno)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if node.lineno in inside_type_checking:
                continue
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in _FORBIDDEN_NAMES:
                        violations.append(
                            f"{path}:{node.lineno} imports {alias.name} from {node.module}"
                        )
            else:
                for alias in node.names:
                    if alias.name in _FORBIDDEN_NAMES:
                        violations.append(
                            f"{path}:{node.lineno} imports {alias.name}"
                        )
    return violations


def test_no_api_route_directly_imports_authoritative_state():
    all_violations = []
    for f in _source_files():
        all_violations.extend(_imports_forbidden_name_outside_type_checking(f))
    assert not all_violations, (
        "API routes/ws/server files must not import AuthoritativeState or EntityState outside TYPE_CHECKING:\n"
        + "\n".join(all_violations)
    )
