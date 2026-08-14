"""AST-based zero-network-calls guard and generator write-guard tests
(TCK-20260721-ORCHESTRATION-CONTRACT-CORE).

The network-calls scan is modeled directly on
tests/agent_replay/test_runner_no_forbidden_calls.py's `_FORBIDDEN_MODULE_NAMES` /
`_dotted_call_name` pattern, with the forbidden set swapped to network-library names. No existing
"no network calls" precedent exists elsewhere in this repo (see investigation.md) — this is new,
not copied verbatim from a prior test file, only from its AST-walking technique.

The write-guard tests prove the generator's containment check is structurally wired in (a
positive control, not merely present-but-unused), and the scope-creep guard prevents this
ticket's tree from starting the out-of-scope Claude conformance/diff or Codex adapter work.
"""
from __future__ import annotations

import ast
import shutil
from pathlib import Path

import pytest

from agent_orchestration.errors import GeneratorWriteGuardError
from agent_orchestration.generator import generate
from agent_orchestration.loader import load_contract

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOL_DIR = _REPO_ROOT / "tools" / "agent_orchestration"

_FORBIDDEN_MODULE_NAMES = {"socket", "urllib", "requests", "http"}
_FORBIDDEN_DOTTED_PREFIXES = ("socket.", "urllib.", "requests.", "http.client")

# Scope-creep guard: real repo paths/module names that would indicate this ticket started
# building the out-of-scope Claude conformance/diff tooling or a .codex/ provider adapter, rather
# than casual references to existing, already-real paths like .claude/agents/*.md (which
# roles/*.yaml legitimately documents, e.g. finalizer's inline-prompt exception note).
_SCOPE_CREEP_MARKERS = (".codex/", "conformance_diff", "claude_conformance", ".claude/conformance")


def _tool_py_files() -> list[Path]:
    files = sorted(_TOOL_DIR.glob("*.py"))
    assert files, f"no .py files found under {_TOOL_DIR} — scan would be vacuous"
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


def test_no_forbidden_network_import_statements():
    for path in _tool_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top not in _FORBIDDEN_MODULE_NAMES, f"{path}: forbidden `import {alias.name}`"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                top = module.split(".")[0]
                assert top not in _FORBIDDEN_MODULE_NAMES, f"{path}: forbidden `from {module} import ...`"


def test_no_forbidden_network_dotted_calls():
    for path in _tool_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_call_name(node.func)
            if dotted is None:
                continue
            assert not dotted.startswith(_FORBIDDEN_DOTTED_PREFIXES), (
                f"{path}: forbidden network call `{dotted}(...)`"
            )


def _fake_repo_with_real_contract(tmp_path: Path) -> Path:
    """Builds a throwaway repo root under tmp_path with a copy of the real agent-orchestration/
    contract — keeps generator tests from ever writing into the real repo tree."""
    fake_repo = tmp_path / "fake_repo"
    shutil.copytree(_REPO_ROOT / "agent-orchestration", fake_repo / "agent-orchestration")
    return fake_repo


def test_generator_write_guard_refuses_writes_outside_agent_orchestration_without_flag(tmp_path):
    fake_repo = _fake_repo_with_real_contract(tmp_path)
    outside_dir = tmp_path / "outside_contract_dir"
    with pytest.raises(GeneratorWriteGuardError):
        generate(fake_repo, outside_dir)
    assert not outside_dir.exists()


def test_generator_write_guard_allows_writes_outside_with_explicit_flag(tmp_path):
    fake_repo = _fake_repo_with_real_contract(tmp_path)
    outside_dir = tmp_path / "outside_contract_dir"
    written = generate(fake_repo, outside_dir, allow_outside_contract=True)
    assert written
    for path in written:
        assert path.exists()


def test_generator_allows_writes_inside_agent_orchestration_without_flag(tmp_path):
    # Regenerating in-place (or into a subdirectory of agent-orchestration/) is always allowed
    # without the flag — the guard only restricts writes OUTSIDE agent-orchestration/.
    fake_repo = _fake_repo_with_real_contract(tmp_path)
    inside_dir = fake_repo / "agent-orchestration" / "_generated_test_scratch"
    written = generate(fake_repo, inside_dir)
    assert written
    for path in written:
        assert path.exists()


def test_generated_output_round_trips_through_load_contract(tmp_path):
    fake_repo = _fake_repo_with_real_contract(tmp_path)
    outside_dir = tmp_path / "roundtrip_target"
    generate(fake_repo, outside_dir, allow_outside_contract=True)

    # load_contract expects a repo-root-shaped layout with an agent-orchestration/ child —
    # confirm the generated files are themselves valid, loadable contract data.
    wrapper_root = tmp_path / "wrapper_root"
    shutil.copytree(outside_dir, wrapper_root / "agent-orchestration")
    bundle = load_contract(wrapper_root)
    assert bundle.contract["version"] == 1


def test_no_conformance_or_provider_adapter_code_in_this_tickets_tree():
    # Scoped to .py/.yaml (functional contract/tooling content) — README.md prose legitimately
    # names ".codex/" as a concept when describing what this directory does NOT build, which
    # is not the same as this tree actually containing adapter code.
    search_dirs = [_TOOL_DIR, _REPO_ROOT / "agent-orchestration"]
    for directory in search_dirs:
        for pattern in ("**/*.py", "**/*.yaml", "**/*.yml"):
            for path in directory.glob(pattern):
                text = path.read_text(encoding="utf-8")
                for marker in _SCOPE_CREEP_MARKERS:
                    assert marker not in text, f"{path}: scope-creep marker {marker!r} found"
