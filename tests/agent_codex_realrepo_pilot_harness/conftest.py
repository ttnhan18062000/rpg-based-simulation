"""Suite boundary: this harness may inspect, but never alter, the real worktree."""
from __future__ import annotations

from pathlib import Path

import pytest


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_WATCHED = (
    _PROJECT_ROOT / ".codex" / "config.toml",
    _PROJECT_ROOT / "agent-monitoring" / "runs.jsonl",
    _PROJECT_ROOT / "agent-monitoring" / "events.jsonl",
    _PROJECT_ROOT / "agent-monitoring" / "tools.jsonl",
)


def _snapshot() -> dict[str, bytes | None]:
    watched = {str(path): path.read_bytes() if path.is_file() else None for path in _WATCHED}
    watched.update(
        {
            str(path): path.read_bytes()
            for directory in (_PROJECT_ROOT / "pilot_requests", _PROJECT_ROOT / "tickets")
            if directory.is_dir()
            for path in directory.rglob("*")
            if path.is_file()
        }
    )
    return watched


@pytest.fixture(autouse=True, scope="session")
def real_worktree_is_preserved():
    before = _snapshot()
    yield
    assert _snapshot() == before
