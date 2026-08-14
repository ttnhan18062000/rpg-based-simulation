"""Architecture guard (Step 5): the shared append writer is reached only through
writer_bridge.py's single spec_from_file_location import, never a second append mechanism."""
from __future__ import annotations

import ast
from pathlib import Path

_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent / "tools" / "agent_codex_posttool_adapter"
)
_WRITER_BRIDGE_FILE = "writer_bridge.py"


def _package_py_files() -> list[Path]:
    files = sorted(_PACKAGE_DIR.glob("*.py"))
    assert files, f"no .py files found under {_PACKAGE_DIR} — scan would be vacuous"
    return files


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


def _string_constants_in_call(node: ast.Call) -> list[str]:
    values = []
    for arg in list(node.args) + [kw.value for kw in node.keywords]:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            values.append(arg.value)
    return values


def test_adapter_calls_write_line_not_a_new_append_mechanism():
    for path in _package_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_call_name(node.func)

            if dotted in ("importlib.util.spec_from_file_location", "spec_from_file_location"):
                literals = _string_constants_in_call(node)
                references_writer = any(
                    "agent-monitoring" in v or "writer.py" in v for v in literals
                )
                assert not references_writer or path.name == _WRITER_BRIDGE_FILE, (
                    f"{path}: only {_WRITER_BRIDGE_FILE} may load tools/agent-monitoring/writer.py"
                )

            if isinstance(node.func, ast.Name) and node.func.id == "open":
                for i, arg in enumerate(node.args):
                    if (
                        i == 1
                        and isinstance(arg, ast.Constant)
                        and isinstance(arg.value, str)
                        and "a" in arg.value
                    ):
                        raise AssertionError(
                            f"{path}: forbidden direct open(..., {arg.value!r}) append call"
                        )
                for kw in node.keywords:
                    if (
                        kw.arg == "mode"
                        and isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, str)
                        and "a" in kw.value.value
                    ):
                        raise AssertionError(
                            f"{path}: forbidden direct open(..., mode={kw.value.value!r}) append call"
                        )

            if dotted == "os.open":
                for arg in list(node.args) + [kw.value for kw in node.keywords]:
                    for sub in ast.walk(arg):
                        if isinstance(sub, ast.Attribute) and sub.attr == "O_APPEND":
                            raise AssertionError(
                                f"{path}: forbidden os.open(..., os.O_APPEND...) call"
                            )

    writer_bridge_source = (_PACKAGE_DIR / _WRITER_BRIDGE_FILE).read_text(encoding="utf-8")
    assert "write_line" in writer_bridge_source
    assert "spec_from_file_location" in writer_bridge_source
