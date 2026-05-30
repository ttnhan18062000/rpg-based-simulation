from __future__ import annotations
import pytest
from src.observability.behavior.behavior_scorecard import EntityBehaviorScorecard
from src.observability.behavior.cohort_analyzer import CohortAnalyzer


def test_cohort_analyzer_groups_by_verdict():
    scorecards = [
        EntityBehaviorScorecard(
            run_id="run_1", entity_id=1, ticks_observed=10,
            route_families_used={}, behavior_categories_used={},
            episodes_started=0, episodes_completed=0, episodes_failed=0,
            repeated_failure_count=0, adaptation_proof_count=0,
            stagnation_score=0.0, progression_score=0.0, cooperation_score=0.0,
            information_usage_score=0.0, behavior_diversity_score=0.0,
            verdict="cautious"
        ),
        EntityBehaviorScorecard(
            run_id="run_1", entity_id=2, ticks_observed=10,
            route_families_used={}, behavior_categories_used={},
            episodes_started=0, episodes_completed=0, episodes_failed=0,
            repeated_failure_count=0, adaptation_proof_count=0,
            stagnation_score=0.0, progression_score=0.0, cooperation_score=0.0,
            information_usage_score=0.0, behavior_diversity_score=0.0,
            verdict="aggressive"
        ),
        EntityBehaviorScorecard(
            run_id="run_1", entity_id=3, ticks_observed=10,
            route_families_used={}, behavior_categories_used={},
            episodes_started=0, episodes_completed=0, episodes_failed=0,
            repeated_failure_count=0, adaptation_proof_count=0,
            stagnation_score=0.0, progression_score=0.0, cooperation_score=0.0,
            information_usage_score=0.0, behavior_diversity_score=0.0,
            verdict="cautious"
        ),
    ]

    analyzer = CohortAnalyzer()
    groups = analyzer.group_by_verdict(scorecards)

    assert len(groups["cautious"]) == 2
    assert len(groups["aggressive"]) == 1
    assert groups["cautious"][0].entity_id == 1
    assert groups["cautious"][1].entity_id == 3
