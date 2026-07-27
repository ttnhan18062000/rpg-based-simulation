"""AST-based no-forbidden-calls scan of tools/agent_replay_codex/**.py
(TCK-20260721-CODEX-REPLAY-PARITY, Step 7).

Mirrors tests/agent_replay/test_runner_no_forbidden_calls.py's technique exactly, scoped to the
new tools/agent_replay_codex/ package's own source. This is a new instance of the existing guard
for the new package's own Python source — distinct from, and not a substitute for, the
process-level containment proof in test_containment_real_process.py /
test_no_production_hook_invocation.py. Run this first: it costs zero API usage and must pass
before any real invocation is attempted.
"""
import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_PACKAGE_DIR = _REPO_ROOT / "tools" / "agent_replay_codex"

_FORBIDDEN_MODULE_NAMES = {"record_run", "record_events", "post_tool_hook", "pre_tool_hook"}
_FORBIDDEN_FILENAMES = ("record_run.py", "record_events.py", "post_tool_hook.py", "pre_tool_hook.py")
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


def test_no_forbidden_import_statements():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    tail = alias.name.rsplit(".", 1)[-1]
                    assert tail not in _FORBIDDEN_MODULE_NAMES, f"{path}: forbidden `import {alias.name}`"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                tail = module.rsplit(".", 1)[-1]
                assert tail not in _FORBIDDEN_MODULE_NAMES, f"{path}: forbidden `from {module} import ...`"


def test_no_forbidden_importlib_import_module_calls():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_call_name(node.func)
            if dotted not in ("importlib.import_module", "import_module"):
                continue
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    for forbidden_name in _FORBIDDEN_MODULE_NAMES:
                        assert forbidden_name not in arg.value, (
                            f"{path}: forbidden importlib.import_module({arg.value!r})"
                        )


def test_no_subprocess_or_os_system_calls_reference_forbidden_filenames():
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
            for literal in _string_constants_in(node):
                for forbidden in _FORBIDDEN_FILENAMES:
                    assert forbidden not in literal, (
                        f"{path}: {dotted}(...) call argument references forbidden filename "
                        f"{forbidden!r}"
                    )


def test_no_forbidden_filename_substring_in_any_string_constant_in_the_file():
    for path in _package_py_files():
        tree = _parse(path)
        for literal in _string_constants_in(tree):
            for forbidden in _FORBIDDEN_FILENAMES:
                assert forbidden not in literal, (
                    f"{path}: string constant {literal!r} contains forbidden filename substring "
                    f"{forbidden!r}"
                )
