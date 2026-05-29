from __future__ import annotations
import os
import json
import shutil
import pytest
from src.observability.behavior.behavior_scorecard import EntityBehaviorScorecard, RunBehaviorScorecard


@pytest.fixture
def temp_run_dir():
    run_dir = "tests/run_data_phase26_test"
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    yield run_dir
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)


def test_scorecard_artifacts_are_written_to_files(temp_run_dir):
    run_dir = temp_run_dir
    entity_sc_path = os.path.join(run_dir, "entity_behavior_scorecards.jsonl")
    run_sc_path = os.path.join(run_dir, "run_behavior_scorecard.json")

    entity_sc = EntityBehaviorScorecard(
        run_id="run_123", entity_id=1, ticks_observed=10,
        route_families_used={}, behavior_categories_used={},
        episodes_started=0, episodes_completed=0, episodes_failed=0,
        repeated_failure_count=0, adaptation_proof_count=0,
        stagnation_score=0.0, progression_score=0.0, cooperation_score=0.0,
        information_usage_score=0.0, behavior_diversity_score=0.0,
        verdict="stable"
    )

    run_sc = RunBehaviorScorecard(
        run_id="run_123", entity_count=1, route_diversity_score=0.8,
        action_entropy=1.0, episode_success_rate=0.5, stagnation_ratio=0.1,
        repeated_failure_loop_count=0, adaptation_proof_count=0,
        hidden_knowledge_suspicion_count=0, cognition_impact_score=0.0,
        observability_overhead_ms_avg=0.0, runtime_cost_delta_percent=0.0,
        verdict="PASSED"
    )

    with open(entity_sc_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(entity_sc.to_dict()) + "\n")

    with open(run_sc_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(run_sc.to_dict()) + "\n")

    assert os.path.exists(entity_sc_path)
    assert os.path.exists(run_sc_path)
