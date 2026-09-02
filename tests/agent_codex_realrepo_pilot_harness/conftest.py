"""Suite boundary: this harness may inspect, but never alter, the real worktree."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_replay_codex.monitoring_shards import read_tools_source_bytes


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_AGENT_MONITORING_DIR = _PROJECT_ROOT / "agent-monitoring"
_WATCHED = (
    _PROJECT_ROOT / ".codex" / "config.toml",
    _AGENT_MONITORING_DIR / "runs.jsonl",
    _AGENT_MONITORING_DIR / "events.jsonl",
)


def _snapshot() -> dict[str, bytes | None]:
    watched = {str(path): path.read_bytes() if path.is_file() else None for path in _WATCHED}
    watched[str(_AGENT_MONITORING_DIR / "tools.jsonl")] = read_tools_source_bytes(
        _AGENT_MONITORING_DIR
    )
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
