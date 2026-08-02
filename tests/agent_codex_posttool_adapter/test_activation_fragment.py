"""Tests for tools/agent_codex_posttool_adapter/activation_fragment.py (Step 8)."""
from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

from tools.agent_codex_posttool_adapter.activation_fragment import (
    PROPOSED_HOOK_BLOCK,
    assert_scratch_target,
    render_proposed_fragment,
)
from tools.agent_codex_posttool_adapter.errors import ActivationFragmentGuardError

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PACKAGE_DIR = _REPO_ROOT / "tools" / "agent_codex_posttool_adapter"


def test_proposed_fragment_registers_only_post_tool_use():
    rendered = render_proposed_fragment(b'# base config\nfoo = "bar"\n')
    data = tomllib.loads(rendered.decode("utf-8"))
    assert set(data["hooks"].keys()) == {"PostToolUse"}
    assert len(data["hooks"]["PostToolUse"]) == 1
    assert data["hooks"]["PostToolUse"][0]["matcher"] == "*"


def test_proposed_fragment_never_applied_to_real_config(tmp_path):
    real_config_path = _REPO_ROOT / ".codex" / "config.toml"
    with pytest.raises(ActivationFragmentGuardError):
        assert_scratch_target(real_config_path, _REPO_ROOT)

    scratch_path = tmp_path / "scratch-config.toml"
    assert_scratch_target(scratch_path, _REPO_ROOT)  # does not raise


def test_no_test_or_default_code_path_invokes_the_proposed_fragment():
    forbidden_apply_targets = {"render_proposed_fragment"}
    files = list(_PACKAGE_DIR.glob("*.py")) + list(
        (_REPO_ROOT / "tests" / "agent_codex_posttool_adapter").glob("*.py")
    )
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name in forbidden_apply_targets and path.name != "activation_fragment.py" and path.name != "test_activation_fragment.py":
                raise AssertionError(
                    f"{path}: unexpected call to {name!r} outside activation_fragment.py's own "
                    "definition and this test module's own scratch-only exercise of it"
                )
    assert PROPOSED_HOOK_BLOCK not in (_REPO_ROOT / ".codex" / "config.toml").read_bytes()
