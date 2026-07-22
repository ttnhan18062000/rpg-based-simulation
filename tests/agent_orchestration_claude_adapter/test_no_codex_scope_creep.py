"""Codex-side scope-creep guard (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, Out of Scope guard).

Mirrors tests/agent_orchestration/test_validator_no_network_calls.py's
`test_no_conformance_or_provider_adapter_code_in_this_tickets_tree`'s `_SCOPE_CREEP_MARKERS`
substring scan, applied to this ticket's own new tree. Asserts no `.codex/` path reference and no
`conformance_diff`/`claude_conformance` module-name string appears anywhere in this ticket's own
shipped `.py`/`.yaml`/`.md` files — catches this ticket's tooling accidentally starting the
out-of-scope Codex-side adapter work (owned by a different ticket).

Scoped to the shipped code/contract tree only, mirroring the predecessor guard's own scope
exactly (`_TOOL_DIR` + `agent-orchestration/`, never its own tests/ directory) — this ticket's own
test modules (this file included) legitimately discuss ".codex/" as a concept when describing what
is explicitly NOT being built here, which is not the same as the shipped tree actually containing
adapter code; the tests/ directory is not scanned.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent

_SCANNED_DIRS = [
    _REPO_ROOT / "tools" / "agent_orchestration_claude_adapter",
]
_SCANNED_FILES = [
    _REPO_ROOT / "agent-orchestration" / "terminal-statuses.yaml",
    _REPO_ROOT / "agent-orchestration" / "rendered" / "claude-adapter.yaml",
    _REPO_ROOT / "agent-orchestration" / "intentional-divergences.md",
]

_SCOPE_CREEP_MARKERS = (".codex/", "conformance_diff", "claude_conformance", ".claude/conformance")


def _all_scanned_paths() -> list[Path]:
    paths: list[Path] = list(_SCANNED_FILES)
    for directory in _SCANNED_DIRS:
        for pattern in ("**/*.py", "**/*.yaml", "**/*.yml", "**/*.md"):
            paths.extend(directory.glob(pattern))
    return paths


def test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree():
    paths = _all_scanned_paths()
    assert paths, "no files found to scan — guard would be vacuous"

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for marker in _SCOPE_CREEP_MARKERS:
            assert marker not in text, f"{path}: scope-creep marker {marker!r} found"


def test_no_dot_codex_directory_exists_in_repo():
    assert not (_REPO_ROOT / ".codex").exists(), (
        ".codex/ must not be created by this ticket — Codex-side adapter implementation is "
        "owned by a different ticket"
    )
