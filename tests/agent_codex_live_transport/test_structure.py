from __future__ import annotations

import ast
from pathlib import Path


_ROOT = Path(__file__).parents[2]
_HARNESS = _ROOT / "tools" / "agent_codex_realrepo_pilot_harness"
_TRANSPORT = _ROOT / "tools" / "agent_codex_live_transport"


def _calls(tree: ast.AST) -> list[str]:
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            result.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            result.append(node.func.attr)
    return result


def test_live_preflight_constructor_appears_only_in_its_private_factory():
    constructors: list[tuple[Path, int]] = []
    for path in list(_HARNESS.glob("*.py")) + list(_TRANSPORT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "LivePreflightResult":
                constructors.append((path, node.lineno))

    assert len(constructors) == 1
    path, line = constructors[0]
    assert path.name == "live_preflight.py", (path, line)
    source = path.read_text(encoding="utf-8")
    assert "def _create_live_preflight" in source


def test_transport_public_api_has_no_raw_root_or_prompt_parameter_and_no_bypass_flag():
    tree = ast.parse((_TRANSPORT / "invoker.py").read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "invoke_live_transport")
    names = [arg.arg for arg in function.args.args]
    assert "root" not in names
    assert "prompt" not in names
    assert "text" not in names
    source = (_TRANSPORT / "invoker.py").read_text(encoding="utf-8")
    assert "--dangerously-bypass-approvals-and-sandbox" not in source
    assert "--dangerously-bypass-hook-trust" not in source


def test_fresh_consent_check_is_the_first_call_in_transport_invocation_entry():
    tree = ast.parse((_TRANSPORT / "invoker.py").read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "invoke_live_transport")
    first_statement = function.body[0]
    assert isinstance(first_statement, ast.Expr)
    assert isinstance(first_statement.value, ast.Call)
    assert _calls(first_statement.value) == ["issue_live_authority"]


def test_opt_in_fixture_reuses_the_existing_realrepo_consent_variable():
    fixture_source = (_ROOT / "tests" / "agent_codex_live_transport" / "conftest.py").read_text(encoding="utf-8")
    assert "CODEX_REALREPO_PILOT_LIVE_CONSENT" in fixture_source
    assert "TEST_CONSENT" not in fixture_source
