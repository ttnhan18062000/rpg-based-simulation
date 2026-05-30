from __future__ import annotations
import pytest
from src.observability.behavior.behavior_metric_window import BehaviorMetricWindow


def test_behavior_metric_window_frozen():
    window = BehaviorMetricWindow(
        run_id="run_123",
        window_start_tick=0,
        window_end_tick=10,
        behavior_counts={"combat/engage": 5}
    )
    with pytest.raises(AttributeError):
        window.window_start_tick = 5  # type: ignore


def test_behavior_metric_window_to_dict_and_from_dict():
    window = BehaviorMetricWindow(
        run_id="run_123",
        window_start_tick=0,
        window_end_tick=10,
        behavior_counts={"combat/engage": 5},
        route_family_counts={"safe": 2},
        episode_counts={"combat": 1},
        episode_outcomes={"combat/success": 1},
        failure_counts={"blocked": 1},
        adaptation_counts={"switch": 1},
        entity_activity_counts={"entity_1": 5}
    )
    data = window.to_dict()
    assert data["run_id"] == "run_123"
    assert data["window_start_tick"] == 0
    assert data["window_end_tick"] == 10
    assert data["behavior_counts"] == {"combat/engage": 5}
    assert data["route_family_counts"] == {"safe": 2}
    assert data["episode_counts"] == {"combat": 1}
    assert data["episode_outcomes"] == {"combat/success": 1}
    assert data["failure_counts"] == {"blocked": 1}
    assert data["adaptation_counts"] == {"switch": 1}
    assert data["entity_activity_counts"] == {"entity_1": 5}

    reconstructed = BehaviorMetricWindow.from_dict(data)
    assert reconstructed.run_id == "run_123"
    assert reconstructed.window_start_tick == 0
    assert reconstructed.window_end_tick == 10
    assert reconstructed.behavior_counts == {"combat/engage": 5}
    assert reconstructed.route_family_counts == {"safe": 2}
    assert reconstructed.episode_counts == {"combat": 1}
    assert reconstructed.episode_outcomes == {"combat/success": 1}
    assert reconstructed.failure_counts == {"blocked": 1}
    assert reconstructed.adaptation_counts == {"switch": 1}
    assert reconstructed.entity_activity_counts == {"entity_1": 5}
