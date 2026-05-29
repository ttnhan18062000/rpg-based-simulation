from __future__ import annotations
import pytest
from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.behavior_timeline_store import BehaviorTimelineStore


def test_behavior_timeline_store_is_bounded():
    store = BehaviorTimelineStore(capacity_per_entity=3)
    for tick in range(5):
        store.record(BehaviorEvent(
            run_id="run_1",
            tick=tick,
            entity_id=12,
            behavior_category="combat",
            behavior_family="engage"
        ))

    timeline = store.get_entity_timeline("run_1", 12)
    assert len(timeline.events) == 3
    assert timeline.events[0].tick == 2
    assert timeline.events[-1].tick == 4


def test_behavior_timeline_tracks_dropped_count():
    store = BehaviorTimelineStore(capacity_per_entity=2)
    for tick in range(5):
        store.record(BehaviorEvent(
            run_id="run_1",
            tick=tick,
            entity_id=12,
            behavior_category="combat",
            behavior_family="engage"
        ))

    timeline = store.get_entity_timeline("run_1", 12)
    assert timeline.dropped_count == 3
