from __future__ import annotations
import pytest
from src.observability.behavior.behavior_scorecard import RunBehaviorScorecard


def test_run_scorecard_to_dict_and_from_dict():
    sc = RunBehaviorScorecard(
        run_id="run_1",
        entity_count=10,
        route_diversity_score=0.85,
        action_entropy=1.2,
        episode_success_rate=0.75,
        stagnation_ratio=0.1,
        repeated_failure_loop_count=1,
        adaptation_proof_count=5,
        hidden_knowledge_suspicion_count=0,
        cognition_impact_score=0.9,
        observability_overhead_ms_avg=0.5,
        runtime_cost_delta_percent=2.5,
        verdict="EXCELLENT"
    )
    data = sc.to_dict()
    assert data["run_id"] == "run_1"
    assert data["episode_success_rate"] == 0.75
    assert data["verdict"] == "EXCELLENT"

    reconstructed = RunBehaviorScorecard.from_dict(data)
    assert reconstructed.run_id == "run_1"
    assert reconstructed.episode_success_rate == 0.75
    assert reconstructed.verdict == "EXCELLENT"
