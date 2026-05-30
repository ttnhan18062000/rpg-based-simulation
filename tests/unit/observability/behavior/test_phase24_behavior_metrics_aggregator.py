from __future__ import annotations
import pytest
from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.metrics_aggregator import BehaviorMetricsAggregator


class MockEpisode:
    def __init__(self, start_tick: int, episode_type: str, outcome: str):
        self.start_tick = start_tick
        self.episode_type = episode_type
        self.outcome = outcome


def test_behavior_counts_aggregate_by_category_and_family():
    events = [
        BehaviorEvent(
            run_id="run_123",
            tick=5,
            entity_id=1,
            behavior_category="combat",
            behavior_family="engage"
        ),
        BehaviorEvent(
            run_id="run_123",
            tick=8,
            entity_id=1,
            behavior_category="combat",
            behavior_family="engage"
        ),
        BehaviorEvent(
            run_id="run_123",
            tick=12,
            entity_id=1,
            behavior_category="movement",
            behavior_family="travel"
        ),
    ]

    aggregator = BehaviorMetricsAggregator()
    window = aggregator.aggregate(
        run_id="run_123",
        window_start=0,
        window_end=10,
        behavior_events=events
    )

    assert window.window_start_tick == 0
    assert window.window_end_tick == 10
    # Should count events within tick range [0, 10]
    assert window.behavior_counts == {"combat/engage": 2}


def test_route_family_counts_aggregate():
    events = [
        BehaviorEvent(
            run_id="run_123",
            tick=2,
            entity_id=1,
            behavior_category="movement",
            behavior_family="travel",
            route_family="safe_route"
        ),
        BehaviorEvent(
            run_id="run_123",
            tick=4,
            entity_id=1,
            behavior_category="movement",
            behavior_family="travel",
            route_family="safe_route"
        ),
        BehaviorEvent(
            run_id="run_123",
            tick=6,
            entity_id=2,
            behavior_category="combat",
            behavior_family="engage",
            route_family="aggressive"
        ),
    ]

    aggregator = BehaviorMetricsAggregator()
    window = aggregator.aggregate(
        run_id="run_123",
        window_start=0,
        window_end=10,
        behavior_events=events
    )

    assert window.route_family_counts == {"safe_route": 2, "aggressive": 1}


def test_episode_outcomes_aggregate():
    episodes = [
        MockEpisode(start_tick=3, episode_type="combat_episode", outcome="success"),
        MockEpisode(start_tick=6, episode_type="combat_episode", outcome="failure"),
        MockEpisode(start_tick=15, episode_type="quest_episode", outcome="success"),
    ]

    aggregator = BehaviorMetricsAggregator()
    window = aggregator.aggregate(
        run_id="run_123",
        window_start=0,
        window_end=10,
        behavior_events=[],
        episodes=episodes
    )

    assert window.episode_counts == {"combat_episode": 2}
    assert window.episode_outcomes == {
        "combat_episode/success": 1,
        "combat_episode/failure": 1
    }


def test_failures_and_adaptations_aggregate():
    events = [
        BehaviorEvent(
            run_id="run_123",
            tick=3,
            entity_id=1,
            behavior_category="failure_response",
            behavior_family="blocked_route",
            outcome="adapted",
            reason="route adaptation triggered"
        ),
        BehaviorEvent(
            run_id="run_123",
            tick=7,
            entity_id=2,
            behavior_category="failure_response",
            behavior_family="low_health",
            outcome="escaped"
        ),
    ]

    aggregator = BehaviorMetricsAggregator()
    window = aggregator.aggregate(
        run_id="run_123",
        window_start=0,
        window_end=10,
        behavior_events=events
    )

    assert window.failure_counts == {"blocked_route": 1, "low_health": 1}
    assert window.adaptation_counts == {"successful_adaptation": 1}
