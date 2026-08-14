"""AST-based no-write-mode/no-subprocess guard against `.claude/workflows/implement-ticket.js`
(TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, AC #6).

Mirrors tests/agent_replay/test_runner_no_forbidden_calls.py's `_dotted_call_name`/
`_string_constants_in`/whole-file-string-constant-scan pattern exactly, applied to every `.py`
file under tools/agent_orchestration_claude_adapter/ (all files from Steps 2, 3, 6 of this
ticket's plan). Scans for:
  - Any write-capable-mode `open(...)` call whose path argument string constants reference
    `implement-ticket.js` ("w", "a", "x", "w+", "a+", "r+", or any mode string containing one of
    those write-capable characters).
  - Any `subprocess.run`/`Popen`/`call`/`check_call`/`check_output`/`os.system`/`os.popen` call
    anywhere that references `implement-ticket.js` in any string constant in the call — read or
    write, subprocessing the file for any reason is disallowed by this ticket's containment
    constraint, not just write-mode opens.
  - Whole-file string-constant scan (not just call-argument-scoped nodes), catching an indirect
    `PATH = "...implement-ticket.js"` followed by a dynamic call.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_PACKAGE_DIR = _REPO_ROOT / "tools" / "agent_orchestration_claude_adapter"

_FORBIDDEN_FILENAME = "implement-ticket.js"
_WRITE_CAPABLE_MODE_CHARS = ("w", "a", "x", "+")
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


def _is_write_capable_mode(mode: str) -> bool:
    return any(ch in mode for ch in _WRITE_CAPABLE_MODE_CHARS)


def _references_forbidden_filename(node: ast.AST) -> bool:
    return any(_FORBIDDEN_FILENAME in literal for literal in _string_constants_in(node))


def test_no_write_mode_open_calls_reference_implement_ticket_js():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_call_name(node.func)
            if dotted not in ("open",):
                continue
            if not _references_forbidden_filename(node):
                continue

            mode_arg = None
            if len(node.args) >= 2:
                mode_arg = node.args[1]
            else:
                for keyword in node.keywords:
                    if keyword.arg == "mode":
                        mode_arg = keyword.value
            mode = mode_arg.value if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str) else "r"

            assert not _is_write_capable_mode(mode), (
                f"{path}: open(...) call referencing {_FORBIDDEN_FILENAME!r} uses write-capable "
                f"mode {mode!r}"
            )


def test_no_subprocess_or_os_system_calls_reference_implement_ticket_js():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_call_name(node.func)
            if dotted is None:
                continue
            call_parts = dotted.split(".")
            if len(call_parts) < 2 or (call_parts[-2], call_parts[-1]) not in _SUBPROCESS_CALL_TAILS:
                continue

            assert not _references_forbidden_filename(node), (
                f"{path}: {dotted}(...) call references forbidden filename {_FORBIDDEN_FILENAME!r} "
                "— subprocessing implement-ticket.js is disallowed for any reason"
            )


def test_no_forbidden_filename_substring_in_any_string_constant_in_the_file():
    """Widened per precedent (test_runner_no_forbidden_calls.py) beyond call-argument-scoped
    nodes: scans EVERY ast.Constant string node in the file, catching indirect variable-based
    construction — e.g. `PATH = "...implement-ticket.js"` followed by a dynamic
    subprocess/open call — which the call-argument-scoped tests above would miss."""
    for path in _package_py_files():
        tree = _parse(path)
        for literal in _string_constants_in(tree):
            assert _FORBIDDEN_FILENAME not in literal, (
                f"{path}: string constant {literal!r} contains forbidden filename substring "
                f"{_FORBIDDEN_FILENAME!r} — this package must never reference "
                "implement-ticket.js at all, not even as a read-only path constant, since none "
                "of this ticket's tooling has a legitimate reason to open it directly (the live "
                "extraction target is always passed in by the caller/test)"
            )
