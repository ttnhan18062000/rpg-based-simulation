import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for the /api/v1/stream compute_delta logic."""

import json
import pytest
pytest.importorskip("fastapi")

from src.api.schemas import EntitySlimSchema
from src.api.routes.stream import compute_delta
from src.utils.event_log import SimEvent


def _make_slim(eid: int, x: int = 0, y: int = 0, hp: int = 10, **kw) -> EntitySlimSchema:
    """Helper to build a minimal EntitySlimSchema for testing."""
    defaults = dict(
        id=eid, kind="goblin", x=x, y=y, hp=hp, max_hp=20,
        state="IDLE", level=1, tier=0, faction="monsters",
        weapon_range=1, combat_target_id=None, loot_progress=0, loot_duration=3,
    )
    defaults.update(kw)
    return EntitySlimSchema(**defaults)


class TestComputeDelta:
    """Unit tests for compute_delta — the core diffing engine behind SSE streaming."""

    def test_initial_snapshot_full_dump(self):
        """When old_slim is empty, every entity should appear in 'changed'."""
        new_slim = {1: _make_slim(1), 2: _make_slim(2)}
        result = compute_delta({}, new_slim, tick=0, events=[])

        assert result is not None
        data = json.loads(result)
        assert data["tick"] == 0
        assert len(data["changed"]) == 2
        assert data["removed"] == []
        assert data["events"] == []

    def test_no_changes_skipped(self):
        """Identical snapshots on a non-heartbeat tick should return None."""
        slim = {1: _make_slim(1)}
        result = compute_delta(slim, slim, tick=1, events=[])
        assert result is None  # No diff, no heartbeat tick

    def test_heartbeat_on_tick_20(self):
        """Even without changes, tick % 20 == 0 should emit a heartbeat."""
        slim = {1: _make_slim(1)}
        result = compute_delta(slim, slim, tick=20, events=[])
        assert result is not None
        data = json.loads(result)
        assert data["tick"] == 20
        assert data["changed"] == []
        assert data["removed"] == []

    def test_entity_moved(self):
        """A position change should appear in 'changed'."""
        old = {1: _make_slim(1, x=0, y=0)}
        new = {1: _make_slim(1, x=5, y=3)}
        result = compute_delta(old, new, tick=10, events=[])

        data = json.loads(result)
        assert len(data["changed"]) == 1
        assert data["changed"][0]["x"] == 5
        assert data["changed"][0]["y"] == 3

    def test_entity_died(self):
        """An entity present in old but missing in new should appear in 'removed'."""
        old = {1: _make_slim(1), 2: _make_slim(2)}
        new = {1: _make_slim(1)}
        result = compute_delta(old, new, tick=5, events=[])

        data = json.loads(result)
        assert data["removed"] == [2]

    def test_entity_spawned(self):
        """A new entity not in old should appear in 'changed'."""
        old = {1: _make_slim(1)}
        new = {1: _make_slim(1), 3: _make_slim(3, x=10, y=10)}
        result = compute_delta(old, new, tick=7, events=[])

        data = json.loads(result)
        assert len(data["changed"]) == 1
        assert data["changed"][0]["id"] == 3

    def test_events_serialized(self):
        """SimEvents passed to compute_delta should appear serialized in the output."""
        slim = {1: _make_slim(1)}
        events = [
            SimEvent(tick=5, category="combat", message="Goblin attacks Hero",
                     entity_ids={1, 2}, metadata={"damage": 10}),
        ]
        result = compute_delta({}, slim, tick=5, events=events)

        data = json.loads(result)
        assert len(data["events"]) == 1
        assert data["events"][0]["category"] == "combat"
        assert data["events"][0]["message"] == "Goblin attacks Hero"

    def test_hp_change_detected(self):
        """HP changes count as a diff."""
        old = {1: _make_slim(1, hp=20)}
        new = {1: _make_slim(1, hp=15)}
        result = compute_delta(old, new, tick=3, events=[])

        data = json.loads(result)
        assert len(data["changed"]) == 1
        assert data["changed"][0]["hp"] == 15

    def test_state_change_detected(self):
        """AI state changes count as a diff."""
        old = {1: _make_slim(1, state="IDLE")}
        new = {1: _make_slim(1, state="HUNT")}
        result = compute_delta(old, new, tick=4, events=[])

        data = json.loads(result)
        assert len(data["changed"]) == 1
        assert data["changed"][0]["state"] == "HUNT"
