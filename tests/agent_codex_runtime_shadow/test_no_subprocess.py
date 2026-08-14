"""No-`codex exec` / no-subprocess architecture guard (TCK-20260730-CODEX-RUNTIME-SHADOW, Step 9).

AST scan over every .py file in tools/agent_codex_runtime_shadow/, mirroring
tests/agent_replay/test_runner_no_forbidden_calls.py and
tests/agent_codex_posttool_adapter/test_no_subprocess_and_no_live_wiring.py's existing technique
(reuse the technique, not the code — a fresh, package-scoped copy). Per plan.md's Anti-Drift
Notes, this is the single highest-value test in this ticket's entire suite: its failure is the
earliest, cheapest signal that this package has regressed into a second copy of
`tools/agent_replay_codex/`'s real-CLI responsibility.

The CLI-invocation-shaped scan (`test_no_codex_exec_argv_construction_anywhere_in_package`) looks
for the exact `["codex", "exec", ...]` argv-list shape `tools/agent_replay_codex/invoker.py`'s real
invocation constructs — not a ban on the word "codex" appearing in prose. Docstrings in this
package's own source (and in `tools/agent_replay_codex/invoker.py`'s own docstring) legitimately
say "codex exec" as prose when describing what this package does NOT do; banning that prose
outright would be a false positive unrelated to this guard's actual purpose (proving no real
invocation mechanism exists).
"""
from __future__ import annotations

import ast
from pathlib import Path

import tools.agent_codex_runtime_shadow as package_under_test

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PACKAGE_DIR = _REPO_ROOT / "tools" / "agent_codex_runtime_shadow"

_FORBIDDEN_DYNAMIC_LOAD_SUBSTRINGS = ("invoker", "wrapper_script")
_SUBPROCESS_CALL_TAILS = {
    ("subprocess", "run"),
    ("subprocess", "Popen"),
    ("subprocess", "call"),
    ("subprocess", "check_call"),
    ("subprocess", "check_output"),
    ("os", "system"),
    ("os", "popen"),
}


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


def test_no_os_system_import_of_system_call_functions():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "os":
                imported_names = {alias.name for alias in node.names}
                assert "system" not in imported_names, f"{path}: forbidden `from os import system`"
                assert "popen" not in imported_names, f"{path}: forbidden `from os import popen`"


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


def test_no_dynamic_load_of_invoker_or_wrapper_script():
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


def test_no_codex_exec_argv_construction_anywhere_in_package():
    """Scans every List/Tuple literal in the package for the exact `["codex", "exec", ...]` argv
    shape `tools/agent_replay_codex/invoker.py`'s real subprocess.run() call constructs — the
    single most direct structural signature of a real Codex CLI invocation."""
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.List, ast.Tuple)):
                continue
            elt_strings = [
                elt.value
                for elt in node.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
            for i in range(len(elt_strings) - 1):
                assert not (elt_strings[i] == "codex" and elt_strings[i + 1] == "exec"), (
                    f"{path}: forbidden argv-shaped literal [..., 'codex', 'exec', ...] found — "
                    "this package must never construct a real Codex CLI invocation"
                )


def test_shadow_comparison_never_invokes_codex_exec():
    """Named per test_plan.md's AC #3 test list: the composed guard proving
    shadow_comparison.py's whole call graph (and every other module in this package) never
    imports subprocess, never calls a subprocess/os.system-family function, and never constructs
    the `["codex", "exec", ...]` argv shape."""
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "subprocess", f"{path}: forbidden `import {alias.name}`"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module != "subprocess", f"{path}: forbidden `from {module} import ...`"
            elif isinstance(node, ast.Call):
                dotted = _dotted_call_name(node.func)
                if dotted:
                    call_parts = dotted.split(".")
                    if len(call_parts) >= 2:
                        assert (call_parts[-2], call_parts[-1]) not in _SUBPROCESS_CALL_TAILS, (
                            f"{path}: forbidden unconditional call `{dotted}(...)`"
                        )
            elif isinstance(node, (ast.List, ast.Tuple)):
                elt_strings = [
                    elt.value
                    for elt in node.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
                for i in range(len(elt_strings) - 1):
                    assert not (elt_strings[i] == "codex" and elt_strings[i + 1] == "exec"), (
                        f"{path}: forbidden argv-shaped literal [..., 'codex', 'exec', ...] found"
                    )


def test_package_docstring_is_non_empty_and_disambiguates_from_siblings():
    doc = package_under_test.__doc__
    assert doc and doc.strip(), "tools/agent_codex_runtime_shadow/__init__.py must not ship empty"
    assert "agent_replay_codex" in doc
    assert "agent_codex_pilot_guardrails" in doc


def test_no_forbidden_import_of_agent_replay_codex_invoker_module():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.endswith("agent_replay_codex.invoker"), (
                        f"{path}: forbidden `import {alias.name}`"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.endswith("agent_replay_codex.invoker"), (
                    f"{path}: forbidden `from {module} import ...`"
                )
                if module.endswith("agent_replay_codex"):
                    imported_names = {alias.name for alias in node.names}
                    assert "invoker" not in imported_names, (
                        f"{path}: forbidden `from {module} import invoker`"
                    )
