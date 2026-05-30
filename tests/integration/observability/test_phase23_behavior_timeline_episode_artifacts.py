from __future__ import annotations
import os
import json
import shutil
import pytest
from src.observability.behavior.behavior_episode import BehaviorEpisode


@pytest.fixture
def temp_run_dir():
    run_dir = "tests/run_data_phase23_test"
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    yield run_dir
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)


def test_episode_artifacts_are_written_post_run(temp_run_dir):
    run_dir = temp_run_dir
    filepath = os.path.join(run_dir, "behavior_episodes.jsonl")

    ep1 = BehaviorEpisode(
        episode_id="ep_10",
        run_id="run_123",
        entity_id=1,
        episode_type="combat_episode",
        start_tick=5,
        end_tick=10,
        trigger="engagement",
        steps=("engage", "defeat"),
        outcome="success",
        source_behavior_event_ids=("bev_1",),
        summary="Success combat"
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json.dumps(ep1.to_dict()) + "\n")

    assert os.path.exists(filepath)

    reconstructed_episodes = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            reconstructed_episodes.append(BehaviorEpisode.from_dict(json.loads(line)))

    assert len(reconstructed_episodes) == 1
    assert reconstructed_episodes[0].episode_id == "ep_10"
    assert reconstructed_episodes[0].outcome == "success"
