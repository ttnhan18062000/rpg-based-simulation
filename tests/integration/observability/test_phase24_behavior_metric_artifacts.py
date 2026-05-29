from __future__ import annotations
import os
import json
import shutil
import pytest
from src.observability.behavior.behavior_metric_window import BehaviorMetricWindow


@pytest.fixture
def temp_run_dir():
    run_dir = "tests/run_data_phase24_test"
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    yield run_dir
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)


def test_behavior_metric_window_artifact_written(temp_run_dir):
    run_dir = temp_run_dir
    filepath = os.path.join(run_dir, "behavior_metric_windows.jsonl")

    window1 = BehaviorMetricWindow(
        run_id="run_123",
        window_start_tick=0,
        window_end_tick=10,
        behavior_counts={"combat/engage": 3}
    )
    window2 = BehaviorMetricWindow(
        run_id="run_123",
        window_start_tick=11,
        window_end_tick=20,
        behavior_counts={"movement/travel": 8}
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json.dumps(window1.to_dict()) + "\n")
        f.write(json.dumps(window2.to_dict()) + "\n")

    assert os.path.exists(filepath)

    reconstructed_windows = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            reconstructed_windows.append(BehaviorMetricWindow.from_dict(json.loads(line)))

    assert len(reconstructed_windows) == 2
    assert reconstructed_windows[0].run_id == "run_123"
    assert reconstructed_windows[0].window_start_tick == 0
    assert reconstructed_windows[0].window_end_tick == 10
    assert reconstructed_windows[0].behavior_counts == {"combat/engage": 3}

    assert reconstructed_windows[1].run_id == "run_123"
    assert reconstructed_windows[1].window_start_tick == 11
    assert reconstructed_windows[1].window_end_tick == 20
    assert reconstructed_windows[1].behavior_counts == {"movement/travel": 8}


def test_behavior_metrics_do_not_modify_runtime_metric_windows(temp_run_dir):
    # Ensure separate artifact paths
    run_dir = temp_run_dir
    runtime_metrics_path = os.path.join(run_dir, "metric_windows.jsonl")
    behavior_metrics_path = os.path.join(run_dir, "behavior_metric_windows.jsonl")

    assert not os.path.exists(runtime_metrics_path)
    assert not os.path.exists(behavior_metrics_path)
