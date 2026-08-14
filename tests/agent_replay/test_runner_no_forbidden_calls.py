"""AST-based no-forbidden-calls scan of tools/agent_replay/**.py (TCK-20260721-CODEX-REPLAY-PROOF, AC #2).

Process-level (source-code) evidence that the replay runner never invokes
`tools/agent-monitoring/{pre_tool_hook,post_tool_hook,record_run,record_events}.py` — a
structurally distinct assertion from tests/agent_replay/test_no_mutation_snapshot.py's
output-diffing, per the ticket's explicit "verified by process-level evidence... not merely by
output-diffing" wording. Follows this repo's own `ast`-based static-check precedent
(`tools/gate_checks/architecture_reviewer_static.py`) over a plain substring/`grep` style, chosen
because this is the single most containment-sensitive check in the ticket and AST resolves both
literal-string and import forms unambiguously, including across f-strings a substring scan could
miss.

Scans only tools/agent_replay/ — never `.claude/workflows/implement-ticket.js`, which legitimately
references these four script names in its own real, unrelated code path; scanning it would be a
false positive and is explicitly not what AC #2 asks for.
"""
import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_AGENT_REPLAY_DIR = _REPO_ROOT / "tools" / "agent_replay"

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


def _agent_replay_py_files() -> list[Path]:
    files = sorted(_AGENT_REPLAY_DIR.glob("*.py"))
    assert files, f"no .py files found under {_AGENT_REPLAY_DIR} — scan would be vacuous"
    return files


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _dotted_call_name(func_node: ast.expr) -> str | None:
    """Dotted name for a Call node's `func` (e.g. `subprocess.run` -> "subprocess.run"), else None."""
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
    for path in _agent_replay_py_files():
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
    for path in _agent_replay_py_files():
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
    for path in _agent_replay_py_files():
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
    """Widened per architecture-review advisory (not just call-argument-scoped nodes): scans
    EVERY ast.Constant string node in the file, catching indirect variable-based construction —
    e.g. `SCRIPT = "record_run.py"` followed by `subprocess.run([sys.executable, SCRIPT])` — which
    the call-argument-scoped tests above would miss since the literal never appears inside the
    Call node itself. Strictly more conservative, consistent with this ticket's fail-closed
    philosophy. Also means this package's own source must never name these four scripts with a
    literal `.py` suffix anywhere, including comments/docstrings — see runner.py's module
    docstring, which deliberately avoids doing so and points here instead."""
    for path in _agent_replay_py_files():
        tree = _parse(path)
        for literal in _string_constants_in(tree):
            for forbidden in _FORBIDDEN_FILENAMES:
                assert forbidden not in literal, (
                    f"{path}: string constant {literal!r} contains forbidden filename substring "
                    f"{forbidden!r}"
                )


def test_fake_stand_ins_exist_and_are_actually_called_inside_replay_slice():
    runner_path = _AGENT_REPLAY_DIR / "runner.py"
    assert runner_path.exists()
    tree = _parse(runner_path)

    function_defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "_fake_write_monitoring" in function_defs, "runner.py must define _fake_write_monitoring"
    assert "_fake_hook_boundary" in function_defs, "runner.py must define _fake_hook_boundary"
    assert "replay_slice" in function_defs, "runner.py must define replay_slice"

    called_names = set()
    for node in ast.walk(function_defs["replay_slice"]):
        if isinstance(node, ast.Call):
            dotted = _dotted_call_name(node.func)
            if dotted:
                called_names.add(dotted.rsplit(".", 1)[-1])

    assert "_fake_write_monitoring" in called_names, (
        "replay_slice defines but never calls _fake_write_monitoring — a positive control this "
        "ticket requires: the fake stand-in must be actually wired in, not merely present-but-unused"
    )
    assert "_fake_hook_boundary" in called_names, (
        "replay_slice defines but never calls _fake_hook_boundary — a positive control this "
        "ticket requires: the fake stand-in must be actually wired in, not merely present-but-unused"
    )
