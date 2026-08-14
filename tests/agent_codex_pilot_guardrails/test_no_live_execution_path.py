"""No-live-execution-path architecture guard (TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 7).

AST/import-graph scan over every .py file in tools/agent_codex_pilot_guardrails/, mirroring
tests/agent_orchestration/test_validator_no_network_calls.py's _SCOPE_CREEP_MARKERS pattern and
tests/agent_replay_codex/test_no_forbidden_calls.py's forbidden-call scan.

Per plan.md's Anti-Drift Notes, this is the single most important test in this ticket's entire
suite — this ticket is "the only concern touching genuinely irreversible-risk territory" in the
whole 7-ticket batch. Do not weaken, skip, or defer any assertion here. If a future change to
this test's target package needs this test to *pass* by deleting/renaming a function to dodge a
denylist, that is a signal the function itself is out-of-scope, not that this test should be
loosened.

Must run last (module collection order is irrelevant to correctness here — this test scans
Steps 1-6's already-written files on disk, so it is safe to run in any order alongside them, but
is documented as the final verification step per plan.md's Dependency Map).
"""
from __future__ import annotations

import ast
from pathlib import Path

from tools.agent_replay_codex.codex_config_guard import assert_committed_config_hook_free

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PACKAGE_DIR = _REPO_ROOT / "tools" / "agent_codex_pilot_guardrails"

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
_EXECUTION_SHAPED_NAME_SUBSTRINGS = ("run_pilot", "execute_pilot", "invoke_codex")


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
                if module == "tools.agent_replay_codex" or module.endswith(
                    ".agent_replay_codex"
                ):
                    imported_names = {alias.name for alias in node.names}
                    assert "invoker" not in imported_names, (
                        f"{path}: forbidden `from {module} import invoker`"
                    )


def test_no_dynamic_load_of_invoker_or_agent_replay_codex():
    # This package's own Step 4 (baseline_manifest_gate.py) legitimately normalizes dynamic
    # module loading via importlib.util.spec_from_file_location to reach tools/agent-monitoring
    # (a hyphenated, non-dotted-importable directory). A static-import check alone would miss a
    # hidden entry point using that same idiomatic technique to reach invoker.py instead — this
    # scans every such dynamic-load call site's string arguments for the forbidden substrings.
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
    # Blanket ban, unconditional — not scoped to calls containing the literal substring "codex".
    # Nothing in Steps 1-6 has any legitimate reason to spawn a subprocess at all, so a blanket
    # ban is strictly stronger than a substring-matched one and closes the indirection gap where
    # a binary name supplied via an env var, string concatenation, or a config-assembled argument
    # list would never contain the literal substring "codex" in source.
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
    # Stronger than the call-level ban above: this package has no legitimate reason to even
    # import subprocess, mirroring consent_gate.py's own "zero dependency on subprocess" test.
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
    # Guard against accidental scope creep, not a general-purpose linter — a simple denylist
    # substring check on top-level function names is sufficient per plan.md Step 7.
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
    # A second, independent confirmation beyond Step 5's own suite-level check
    # (test_config_rollback.py::test_real_committed_config_never_touched_by_this_suite).
    assert_committed_config_hook_free(_REPO_ROOT)
