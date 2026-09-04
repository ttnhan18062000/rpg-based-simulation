"""Suite-wide proof that executor fixtures cannot mutate durable pilot surfaces."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_replay_codex.monitoring_shards import read_source_bytes


_REPO = Path(__file__).resolve().parents[2]
_MONITORING = _REPO / "agent-monitoring"
_MONITORING_SOURCES = ("runs.jsonl", "events.jsonl", "tools.jsonl")


def _snapshot_monitoring() -> dict[str, bytes]:
    return {name: read_source_bytes(_MONITORING, name) for name in _MONITORING_SOURCES}


@pytest.fixture(scope="session", autouse=True)
def _real_surfaces_are_unchanged():
    before_monitoring = _snapshot_monitoring()
    before_config = (_REPO / ".codex" / "config.toml").read_bytes()
    before_tickets = {
        path.relative_to(_REPO).as_posix(): path.read_bytes()
        for path in (_REPO / "tickets").rglob("*.md")
    }
    yield
    assert _snapshot_monitoring() == before_monitoring
    assert (_REPO / ".codex" / "config.toml").read_bytes() == before_config
    after_tickets = {
        path.relative_to(_REPO).as_posix(): path.read_bytes()
        for path in (_REPO / "tickets").rglob("*.md")
    }
    assert after_tickets == before_tickets
