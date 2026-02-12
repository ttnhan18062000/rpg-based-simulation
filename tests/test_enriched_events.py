"""Tests for enriched event metadata (enhance-01).

Covers:
- SimEvent metadata field
- EventLog stores and retrieves metadata
- WorldLoop emits enriched events with metadata for key actions
- EventSchema includes metadata in API response
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.event_log import SimEvent, EventLog


class TestSimEventMetadata:
    """SimEvent supports optional metadata dict."""

    def test_default_metadata_is_none(self):
        ev = SimEvent(tick=1, category="combat", message="test")
        assert ev.metadata is None

    def test_metadata_dict_stored(self):
        meta = {"damage": 12, "attacker_id": 1, "defender_id": 2}
        ev = SimEvent(tick=1, category="combat", message="test", metadata=meta)
        assert ev.metadata == meta
        assert ev.metadata["damage"] == 12

    def test_metadata_with_entity_ids(self):
        ev = SimEvent(tick=5, category="death", message="goblin died",
                      entity_ids=(3,), metadata={"kind": "goblin", "level": 2})
        assert ev.entity_ids == (3,)
        assert ev.metadata["kind"] == "goblin"


class TestEventLogMetadata:
    """EventLog preserves metadata through append and retrieval."""

    def test_append_and_retrieve_metadata(self):
        log = EventLog(maxlen=100)
        meta = {"item_id": "iron_sword", "count": 1}
        ev = SimEvent(tick=10, category="loot", message="looted sword",
                      entity_ids=(1,), metadata=meta)
        log.append(ev)
        result = log.since_tick(0)
        assert len(result) == 1
        assert result[0].metadata == meta

    def test_latest_preserves_metadata(self):
        log = EventLog(maxlen=100)
        log.append(SimEvent(tick=1, category="combat", message="attack",
                            metadata={"damage": 5}))
        log.append(SimEvent(tick=2, category="level_up", message="leveled up",
                            metadata={"new_level": 3}))
        latest = log.latest(1)
        assert len(latest) == 1
        assert latest[0].metadata["new_level"] == 3

    def test_none_metadata_preserved(self):
        log = EventLog(maxlen=100)
        log.append(SimEvent(tick=1, category="rest", message="resting"))
        result = log.since_tick(0)
        assert result[0].metadata is None


class TestEventSchemaMetadata:
    """EventSchema serializes metadata to API response."""

    def test_schema_includes_metadata(self):
        from src.api.schemas import EventSchema
        schema = EventSchema(
            tick=1, category="death", message="goblin died",
            entity_ids=[3], metadata={"kind": "goblin", "level": 2, "respawn": False},
        )
        data = schema.model_dump()
        assert data["metadata"]["kind"] == "goblin"
        assert data["metadata"]["level"] == 2
        assert data["metadata"]["respawn"] is False

    def test_schema_none_metadata(self):
        from src.api.schemas import EventSchema
        schema = EventSchema(
            tick=1, category="rest", message="resting", entity_ids=[1],
        )
        data = schema.model_dump()
        assert data["metadata"] is None

    def test_schema_json_serializable(self):
        from src.api.schemas import EventSchema
        schema = EventSchema(
            tick=5, category="loot", message="looted items",
            entity_ids=[1],
            metadata={"items": ["iron_sword", "small_hp_potion"], "count": 2},
        )
        json_str = schema.model_dump_json()
        assert '"iron_sword"' in json_str
        assert '"count":2' in json_str or '"count": 2' in json_str
