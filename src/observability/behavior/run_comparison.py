"""
run_comparison — Phase 26 run comparison analyzer.
Compares baseline vs target run scorecards to evaluate feature improvements.
"""
from __future__ import annotations
from typing import Any
from src.observability.behavior.behavior_scorecard import RunBehaviorScorecard


class RunBehaviorComparison:
    """
    Compares baseline and target run behavior scorecards to verify feature improvements.
    Enforces that higher event volume alone does not equal behavioral improvement.
    """
    def compare(
        self,
        baseline: RunBehaviorScorecard,
        target: RunBehaviorScorecard
    ) -> dict[str, Any]:
        """
        Evaluates run performance and behavior changes.
        """
        # Improvement rule: success rate goes up AND failure loop count goes down
        improved = False
        if (
            target.episode_success_rate > baseline.episode_success_rate and
            target.repeated_failure_loop_count < baseline.repeated_failure_loop_count and
            target.adaptation_proof_count >= baseline.adaptation_proof_count
        ):
            improved = True

        return {
            "baseline_run_id": baseline.run_id,
            "target_run_id": target.run_id,
            "episode_success_rate_delta": target.episode_success_rate - baseline.episode_success_rate,
            "repeated_failure_loop_delta": target.repeated_failure_loop_count - baseline.repeated_failure_loop_count,
            "adaptation_proof_delta": target.adaptation_proof_count - baseline.adaptation_proof_count,
            "runtime_cost_delta_percent": target.runtime_cost_delta_percent,
            "behavior_improved": improved,
            "verdict": "IMPROVED" if improved else "NO_IMPROVEMENT"
        }
