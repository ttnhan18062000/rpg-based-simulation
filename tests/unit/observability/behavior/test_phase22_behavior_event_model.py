"""
Phase 22 — BehaviorEvent model unit tests.

Tests verify:
- BehaviorEvent is immutable (frozen dataclass).
- All required fields are set correctly.
- source_event_ids link raw events.
- to_dict() and from_dict() produce stable JSON-compatible roundtrip.
- BEHAVIOR_CATEGORIES set is correct.
"""
from __future__ import annotations

import pytest

from src.observability.behavior.behavior_event import BehaviorEvent, BEHAVIOR_CATEGORIES


class TestBehaviorEventModel:
    """Unit tests for BehaviorEvent dataclass."""

    def _make_event(self, **kwargs) -> BehaviorEvent:
        defaults = dict(
            run_id="run_001",
            tick=10,
            entity_id=42,
            behavior_category="combat",
            behavior_family="engage",
        )
        defaults.update(kwargs)
        return BehaviorEvent(**defaults)

    def test_behavior_event_is_frozen(self):
        """BehaviorEvent must be immutable."""
        event = self._make_event()
        with pytest.raises((AttributeError, TypeError)):
            event.tick = 999  # type: ignore[misc]

    def test_behavior_event_required_fields(self):
        event = self._make_event()
        assert event.run_id == "run_001"
        assert event.tick == 10
        assert event.entity_id == 42
        assert event.behavior_category == "combat"
        assert event.behavior_family == "engage"

    def test_behavior_event_defaults(self):
        event = self._make_event()
        assert event.subject is None
        assert event.target_id is None
        assert event.source_event_ids == ()
        assert event.route_family is None
        assert event.action_type is None
        assert event.outcome is None
        assert event.reason is None
        assert dict(event.payload) == {}

    def test_behavior_event_with_source_event_ids(self):
        event = self._make_event(source_event_ids=("evt_1", "evt_2"))
        assert event.source_event_ids == ("evt_1", "evt_2")

    def test_behavior_event_links_source_event_id(self):
        """BehaviorEvent must link at least one source event ID (roadmap requirement)."""
        event = self._make_event(source_event_ids=("raw_event_abc",))
        assert len(event.source_event_ids) >= 1
        assert "raw_event_abc" in event.source_event_ids

    def test_behavior_event_to_dict_roundtrip(self):
        """to_dict() produces JSON-compatible dict; from_dict() reconstructs correctly."""
        original = self._make_event(
            behavior_category="quest",
            behavior_family="progress",
            source_event_ids=("evt_abc",),
            outcome="completed",
            payload={"quest_id": "q_001"},
        )
        d = original.to_dict()

        # Must be JSON-serializable (no sets, tuples, etc.)
        import json
        serialized = json.dumps(d)
        loaded = json.loads(serialized)

        restored = BehaviorEvent.from_dict(loaded)
        assert restored.run_id == original.run_id
        assert restored.tick == original.tick
        assert restored.entity_id == original.entity_id
        assert restored.behavior_category == original.behavior_category
        assert restored.behavior_family == original.behavior_family
        assert restored.source_event_ids == original.source_event_ids
        assert restored.outcome == original.outcome
        assert dict(restored.payload) == {"quest_id": "q_001"}

    def test_behavior_event_to_dict_no_tuples(self):
        """to_dict() output must not contain Python tuples (not JSON serializable)."""
        event = self._make_event(source_event_ids=("a", "b"))
        d = event.to_dict()
        assert isinstance(d["source_event_ids"], list)

    def test_behavior_categories_set_complete(self):
        """BEHAVIOR_CATEGORIES must include all 16 roadmap categories."""
        expected = {
            "movement", "combat", "recovery", "preparation", "progression",
            "information_seeking", "resource_gathering", "trade", "crafting",
            "quest", "cooperation", "avoidance", "failure_response",
            "world_response", "idle_or_defer", "unknown_behavior",
        }
        assert expected.issubset(BEHAVIOR_CATEGORIES), (
            f"Missing categories: {expected - BEHAVIOR_CATEGORIES}"
        )

    def test_behavior_event_with_none_entity_id(self):
        """entity_id may be None for global events."""
        event = self._make_event(entity_id=None)
        assert event.entity_id is None

    def test_behavior_event_payload_is_mapping(self):
        """payload must be a Mapping (dict-like), not a mutable side-effect."""
        event = self._make_event(payload={"key": "val"})
        assert event.payload["key"] == "val"

    def test_behavior_event_equality(self):
        """Two BehaviorEvents with same fields must be equal (frozen dataclass semantics)."""
        e1 = self._make_event()
        e2 = self._make_event()
        assert e1 == e2

    def test_behavior_event_from_dict_handles_missing_optional_fields(self):
        """from_dict() must handle missing optional fields gracefully."""
        minimal = {
            "run_id": "run_x",
            "tick": 5,
            "entity_id": None,
            "behavior_category": "movement",
            "behavior_family": "travel",
        }
        event = BehaviorEvent.from_dict(minimal)
        assert event.run_id == "run_x"
        assert event.source_event_ids == ()
        assert event.payload == {}
