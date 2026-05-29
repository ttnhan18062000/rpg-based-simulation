from __future__ import annotations
import pytest
from src.observability.behavior.behavior_episode import BehaviorEpisode


def test_behavior_episode_frozen():
    episode = BehaviorEpisode(
        episode_id="ep_1",
        run_id="run_1",
        entity_id=12,
        episode_type="combat_episode",
        start_tick=5,
        end_tick=10,
        trigger="engagement",
        steps=("engage", "defeat"),
        outcome="success",
        source_behavior_event_ids=("ev_1",),
        summary="Success combat"
    )
    with pytest.raises(AttributeError):
        episode.start_tick = 6  # type: ignore


def test_behavior_episode_to_dict_and_from_dict():
    episode = BehaviorEpisode(
        episode_id="ep_1",
        run_id="run_1",
        entity_id=12,
        episode_type="combat_episode",
        start_tick=5,
        end_tick=10,
        trigger="engagement",
        steps=("engage", "defeat"),
        outcome="success",
        source_behavior_event_ids=("ev_1",),
        summary="Success combat"
    )
    data = episode.to_dict()
    assert data["episode_id"] == "ep_1"
    assert data["steps"] == ["engage", "defeat"]
    assert data["outcome"] == "success"

    reconstructed = BehaviorEpisode.from_dict(data)
    assert reconstructed.episode_id == "ep_1"
    assert reconstructed.steps == ("engage", "defeat")
    assert reconstructed.outcome == "success"
