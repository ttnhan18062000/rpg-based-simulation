"""Unit tests for ReadModelService — shaped response contract."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import json
import pytest

from src.api.read_model_service import ReadModelService


def _make_manager(**overrides):
    mgr = MagicMock()
    mgr.get_state.return_value = {"tick": 1, "world_time": 0.0, "entities_count": 3, "maturity": 0.0, "seed": 42}
    mgr.get_full_snapshot.return_value = {"tick": 1, "entities": [], "regions": [], "status": "ACTIVE"}
    mgr.get_entity.return_value = {
        "id": 1,
        "kind": "hero",
        "position": [0.0, 0.0],
        "combat": {"hp": 100, "max_hp": 100, "alive": True},
        "inventory": {"gold": 10, "item_count": 0, "items": []},
        "strategic": {},
        "social": {},
        "navigation": {},
        "biological": {},
        "identity": {},
        "intent_results": [],
        "quests": [],
        "readiness": 1.0,
    }
    mgr.get_entity_timeline_events.return_value = []
    mgr.get_entities_paged.return_value = {"entities": [], "total": 0, "offset": 0, "limit": 100}
    for k, v in overrides.items():
        getattr(mgr, k).return_value = v
    return mgr


def test_read_model_shapes_entity_response():
    """entity_status() returns a shaped dict with expected keys, not a raw EntityState."""
    svc = ReadModelService(_make_manager())
    result = svc.entity_status(1)
    assert isinstance(result, dict)
    assert "id" in result
    assert "combat" in result
    assert "inventory" in result


def test_read_model_shapes_world_status():
    """world_status() returns a dict with tick and entities_count keys."""
    svc = ReadModelService(_make_manager())
    result = svc.world_status()
    assert isinstance(result, dict)
    assert "tick" in result
    assert "entities_count" in result


def test_read_model_does_not_expose_raw_state():
    """All ReadModelService responses are JSON-serializable shaped dicts."""
    svc = ReadModelService(_make_manager())
    entity = svc.entity_status(1)
    world = svc.world_status()
    full = svc.world_full()
    timeline = svc.entity_timeline(1)
    paged = svc.entities_paged()
    for obj in [entity, world, full, timeline, paged]:
        assert obj is not None
        # Must be JSON-serializable (no internal state objects)
        json.dumps(obj)


def test_read_model_entity_not_found():
    """entity_status() returns None for an unknown entity_id."""
    mgr = _make_manager()
    mgr.get_entity.return_value = None
    svc = ReadModelService(mgr)
    result = svc.entity_status(9999)
    assert result is None
