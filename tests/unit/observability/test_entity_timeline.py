from __future__ import annotations
import pytest
from src.observability.events import SimulationEvent
from src.observability.config import ObservabilityMode
from src.observability.entity_timeline import EntityTimelineStore

def test_entity_timeline_modes():
    # Test OFF mode
    store_off = EntityTimelineStore(mode=ObservabilityMode.OFF)
    ev = SimulationEvent(
        event_type="test_event", event_category="combat", tick=1, severity="INFO",
        source_system="test", message="msg", entity_id=1
    )
    store_off.record(ev)
    assert len(store_off.get_entity_timeline(1)) == 0

    # Test LIGHT mode (limit 20)
    store_light = EntityTimelineStore(mode=ObservabilityMode.LIGHT)
    for i in range(25):
        ev = SimulationEvent(
            event_type="test_event", event_category="combat", tick=i, severity="INFO",
            source_system="test", message=f"msg {i}", entity_id=1
        )
        store_light.record(ev)

    timeline = store_light.get_entity_timeline(1)
    assert len(timeline) == 20
    assert timeline[0].tick == 5  # Rolled over oldest 5
    assert timeline[-1].tick == 24
    assert store_light.dropped_event_count == 5

def test_entity_timeline_related_entities():
    store = EntityTimelineStore(mode=ObservabilityMode.DEBUG)
    
    # Event with related entity ids
    ev = SimulationEvent(
        event_type="test_event", event_category="combat", tick=1, severity="INFO",
        source_system="test", message="combat link", entity_id=1, related_entity_ids=[1, 2, 3]
    )
    store.record(ev)

    # Assert that event was indexed under all three entity timelines
    t1 = store.get_entity_timeline(1)
    t2 = store.get_entity_timeline(2)
    t3 = store.get_entity_timeline(3)

    assert len(t1) == 1
    assert len(t2) == 1
    assert len(t3) == 1

    assert t1[0].event_id == ev.event_id
    assert t2[0].event_id == ev.event_id
    assert t3[0].event_id == ev.event_id

    # Test get_flagged_timelines
    flagged = store.get_flagged_timelines([2, 3, 4])
    assert 2 in flagged
    assert 3 in flagged
    assert 4 not in flagged
    assert len(flagged[2]) == 1
