from __future__ import annotations
import pytest
from src.observability.behavior.behavior_scorecard import RunBehaviorScorecard
from src.observability.behavior.run_comparison import RunBehaviorComparison


def test_run_comparison_reports_behavior_delta():
    baseline = RunBehaviorScorecard(
        run_id="run_base", entity_count=10, route_diversity_score=0.5,
        action_entropy=1.0, episode_success_rate=0.6, stagnation_ratio=0.3,
        repeated_failure_loop_count=5, adaptation_proof_count=1,
        hidden_knowledge_suspicion_count=0, cognition_impact_score=0.5,
        observability_overhead_ms_avg=0.5, runtime_cost_delta_percent=0.0,
        verdict="BASELINE"
    )

    # Improved target: higher success rate AND lower loop count
    target = RunBehaviorScorecard(
        run_id="run_target", entity_count=10, route_diversity_score=0.7,
        action_entropy=1.1, episode_success_rate=0.8, stagnation_ratio=0.1,
        repeated_failure_loop_count=2, adaptation_proof_count=3,
        hidden_knowledge_suspicion_count=0, cognition_impact_score=0.9,
        observability_overhead_ms_avg=0.5, runtime_cost_delta_percent=2.0,
        verdict="IMPROVED"
    )

    comparison = RunBehaviorComparison()
    res = comparison.compare(baseline, target)

    assert res["behavior_improved"] is True
    assert res["episode_success_rate_delta"] == pytest.approx(0.2)
    assert res["repeated_failure_loop_delta"] == -3
    assert res["adaptation_proof_delta"] == 2
    assert res["verdict"] == "IMPROVED"


def test_comparison_does_not_claim_improvement_when_only_event_volume_increased():
    baseline = RunBehaviorScorecard(
        run_id="run_base", entity_count=10, route_diversity_score=0.5,
        action_entropy=1.0, episode_success_rate=0.6, stagnation_ratio=0.3,
        repeated_failure_loop_count=5, adaptation_proof_count=1,
        hidden_knowledge_suspicion_count=0, cognition_impact_score=0.5,
        observability_overhead_ms_avg=0.5, runtime_cost_delta_percent=0.0,
        verdict="BASELINE"
    )

    # Target where only event counts or entropy/diversity is higher, but failure loop counts did not drop
    target = RunBehaviorScorecard(
        run_id="run_target", entity_count=10, route_diversity_score=0.8,
        action_entropy=1.5, episode_success_rate=0.6, stagnation_ratio=0.3,
        repeated_failure_loop_count=5, adaptation_proof_count=1,
        hidden_knowledge_suspicion_count=0, cognition_impact_score=0.5,
        observability_overhead_ms_avg=0.5, runtime_cost_delta_percent=0.0,
        verdict="NO_REAL_IMPROVEMENT"
    )

    comparison = RunBehaviorComparison()
    res = comparison.compare(baseline, target)

    assert res["behavior_improved"] is False
    assert res["verdict"] == "NO_IMPROVEMENT"
