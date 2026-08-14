from __future__ import annotations

import ast
from pathlib import Path


_ROOT = Path(__file__).parents[2]
_PACKAGE = _ROOT / "tools" / "agent_codex_pilot_orchestration"


def test_production_capability_has_one_production_constructor_path():
    constructors = []
    for path in _PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "_ProductionConfigCapability":
                    constructors.append(path.name)

    assert constructors == ["production_config.py"]


def test_public_orchestration_api_accepts_only_reviewed_context():
    tree = ast.parse((_PACKAGE / "orchestrator.py").read_text())
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "execute_controlled_pilot"
    )

    assert [argument.arg for argument in function.args.args] == ["context"]


def test_orchestration_package_has_no_direct_process_or_monitoring_writer_import():
    forbidden = {"subprocess", "record_events", "record_run", "writer"}
    for path in _PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text())
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert imported.isdisjoint(forbidden), path
