"""No-subprocess / no-live-wiring architecture guard (Step 9).

AST scan over every .py file in tools/agent_codex_posttool_adapter/, mirroring
tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py's technique. Per plan.md's
Anti-Drift Notes, this is the single most important test in this ticket's entire suite — do not
weaken, skip, or defer any denylist entry here.
"""
from __future__ import annotations

import ast
from pathlib import Path

from tools.agent_replay_codex.codex_config_guard import assert_committed_config_hook_free

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PACKAGE_DIR = _REPO_ROOT / "tools" / "agent_codex_posttool_adapter"

_FORBIDDEN_STATIC_IMPORT_MODULE = "tools.agent_replay_codex.invoker"
_FORBIDDEN_DYNAMIC_LOAD_SUBSTRINGS = ("invoker", "agent_replay_codex")
_SUBPROCESS_CALL_TAILS = {
    ("subprocess", "run"),
    ("subprocess", "Popen"),
    ("subprocess", "call"),
    ("subprocess", "check_call"),
    ("subprocess", "check_output"),
    ("os", "system"),
}
_EXECUTION_SHAPED_NAME_SUBSTRINGS = (
    "run_pilot",
    "execute_pilot",
    "invoke_codex",
    "run_codex",
    "invoke_codex_exec",
)


def _package_py_files() -> list[Path]:
    files = sorted(_PACKAGE_DIR.glob("*.py"))
    assert files, f"no .py files found under {_PACKAGE_DIR} — scan would be vacuous"
    return files


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _dotted_call_name(func_node: ast.expr) -> str | None:
    parts: list[str] = []
    node = func_node
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _string_constants_in(node: ast.AST):
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            yield child.value
        elif isinstance(child, ast.JoinedStr):
            for value_node in child.values:
                if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
                    yield value_node.value


def test_no_static_import_of_invoker():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != _FORBIDDEN_STATIC_IMPORT_MODULE, (
                        f"{path}: forbidden `import {alias.name}`"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module != _FORBIDDEN_STATIC_IMPORT_MODULE, (
                    f"{path}: forbidden `from {module} import ...`"
                )
                if module == "tools.agent_replay_codex" or module.endswith(".agent_replay_codex"):
                    imported_names = {alias.name for alias in node.names}
                    assert "invoker" not in imported_names, (
                        f"{path}: forbidden `from {module} import invoker`"
                    )


def test_no_dynamic_load_of_invoker_or_agent_replay_codex():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_call_name(node.func)
            if dotted not in (
                "importlib.util.spec_from_file_location",
                "spec_from_file_location",
                "importlib.import_module",
                "import_module",
            ):
                continue
            for literal in _string_constants_in(node):
                for forbidden in _FORBIDDEN_DYNAMIC_LOAD_SUBSTRINGS:
                    assert forbidden not in literal, (
                        f"{path}: {dotted}(...) call argument {literal!r} references forbidden "
                        f"substring {forbidden!r}"
                    )


def test_no_subprocess_or_os_system_calls_anywhere_in_package():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_call_name(node.func)
            if dotted is None:
                continue
            call_parts = dotted.split(".")
            if len(call_parts) < 2:
                continue
            assert (call_parts[-2], call_parts[-1]) not in _SUBPROCESS_CALL_TAILS, (
                f"{path}: forbidden unconditional call `{dotted}(...)` — this package has no "
                "legitimate reason to spawn a subprocess"
            )


def test_no_subprocess_module_imported_anywhere_in_package():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "subprocess", f"{path}: forbidden `import {alias.name}`"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module != "subprocess", f"{path}: forbidden `from {module} import ...`"


def test_no_execution_shaped_function_names():
    for path in _package_py_files():
        tree = _parse(path)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lowered = node.name.lower()
                for forbidden in _EXECUTION_SHAPED_NAME_SUBSTRINGS:
                    assert forbidden not in lowered, (
                        f"{path}: function name {node.name!r} matches execution-shaped denylist "
                        f"substring {forbidden!r}"
                    )


def test_committed_codex_config_remains_hook_free():
    assert_committed_config_hook_free(_REPO_ROOT)
