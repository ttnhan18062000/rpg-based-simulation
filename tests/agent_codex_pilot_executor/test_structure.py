from __future__ import annotations

import ast
from pathlib import Path


_PACKAGE = Path(__file__).resolve().parents[2] / "tools" / "agent_codex_pilot_executor"


def test_executor_is_library_only_and_has_no_live_or_config_execution_surface():
    forbidden_import_roots = {"subprocess", "shlex"}
    forbidden_calls = {"os.system", "os.popen", "os.spawnv", "os.spawnve"}
    for path in _PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not ({name.name.split(".")[0] for name in node.names} & forbidden_import_roots)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_import_roots
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = node.func.value.id if isinstance(node.func.value, ast.Name) else ""
                assert f"{owner}.{node.func.attr}" not in forbidden_calls
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
                # A library package must not grow a command-line main guard.
                assert not any(
                    isinstance(value, ast.Constant) and value.value == "__main__"
                    for value in [node.test.left, *node.test.comparators]
                )
