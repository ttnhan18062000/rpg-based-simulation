"""Suite-wide proof that executor fixtures cannot mutate durable pilot surfaces."""
from __future__ import annotations

from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_MONITORING = _REPO / "agent-monitoring"
_WATCHED = ("runs.jsonl", "events.jsonl", "tools.jsonl")


@pytest.fixture(scope="session", autouse=True)
def _real_surfaces_are_unchanged():
    before_monitoring = {name: (_MONITORING / name).read_bytes() for name in _WATCHED}
    before_config = (_REPO / ".codex" / "config.toml").read_bytes()
    before_tickets = {
        path.relative_to(_REPO).as_posix(): path.read_bytes()
        for path in (_REPO / "tickets").rglob("*.md")
    }
    yield
    assert {name: (_MONITORING / name).read_bytes() for name in _WATCHED} == before_monitoring
    assert (_REPO / ".codex" / "config.toml").read_bytes() == before_config
    after_tickets = {
        path.relative_to(_REPO).as_posix(): path.read_bytes()
        for path in (_REPO / "tickets").rglob("*.md")
    }
    assert after_tickets == before_tickets
