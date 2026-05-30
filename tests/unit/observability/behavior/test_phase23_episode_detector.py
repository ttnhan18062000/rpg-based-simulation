from __future__ import annotations
import pytest
from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.behavior_timeline_store import EntityBehaviorTimeline
from src.observability.behavior.episode_detector import EpisodeDetector


def test_combat_events_form_combat_episode():
    timeline = EntityBehaviorTimeline(
        run_id="run_1",
        entity_id=12,
        events=(
            BehaviorEvent(
                run_id="run_1",
                tick=5,
                entity_id=12,
                behavior_category="combat",
                behavior_family="engage",
                source_event_ids=("raw_1",)
            ),
            BehaviorEvent(
                run_id="run_1",
                tick=8,
                entity_id=12,
                behavior_category="combat",
                behavior_family="kill_or_defeat",
                source_event_ids=("raw_2",)
            ),
        )
    )

    detector = EpisodeDetector()
    episodes = detector.detect(timeline)

    assert len(episodes) == 1
    ep = episodes[0]
    assert ep.episode_type == "combat_episode"
    assert ep.start_tick == 5
    assert ep.end_tick == 8
    assert ep.outcome == "success"
    assert ep.source_behavior_event_ids == ("raw_1", "raw_2")


def test_information_events_form_information_episode():
    timeline = EntityBehaviorTimeline(
        run_id="run_1",
        entity_id=12,
        events=(
            BehaviorEvent(
                run_id="run_1",
                tick=3,
                entity_id=12,
                behavior_category="information_seeking",
                behavior_family="query",
                source_event_ids=("raw_10",)
            ),
            BehaviorEvent(
                run_id="run_1",
                tick=6,
                entity_id=12,
                behavior_category="information_seeking",
                behavior_family="learned",
                source_event_ids=("raw_11",)
            ),
        )
    )

    detector = EpisodeDetector()
    episodes = detector.detect(timeline)

    assert len(episodes) == 1
    ep = episodes[0]
    assert ep.episode_type == "information_episode"
    assert ep.start_tick == 3
    assert ep.end_tick == 6
    assert ep.outcome == "success"


def test_failure_then_route_change_forms_failure_response_episode():
    timeline = EntityBehaviorTimeline(
        run_id="run_1",
        entity_id=12,
        events=(
            BehaviorEvent(
                run_id="run_1",
                tick=4,
                entity_id=12,
                behavior_category="failure_response",
                behavior_family="blocked_route",
                source_event_ids=("raw_20",)
            ),
            BehaviorEvent(
                run_id="run_1",
                tick=9,
                entity_id=12,
                behavior_category="movement",
                behavior_family="travel",
                outcome="success",
                source_event_ids=("raw_21",)
            ),
        )
    )

    detector = EpisodeDetector()
    episodes = detector.detect(timeline)

    assert len(episodes) == 1
    ep = episodes[0]
    assert ep.episode_type == "failure_response_episode"
    assert ep.start_tick == 4
    assert ep.end_tick == 9
    assert ep.outcome == "resolved"
