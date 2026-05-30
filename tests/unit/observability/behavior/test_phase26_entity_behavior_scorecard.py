from __future__ import annotations
import pytest
from src.observability.behavior.behavior_scorecard import EntityBehaviorScorecard


def test_entity_scorecard_frozen():
    sc = EntityBehaviorScorecard(
        run_id="run_1",
        entity_id=12,
        ticks_observed=100,
        route_families_used={"safe": 5},
        behavior_categories_used={"combat": 10},
        episodes_started=3,
        episodes_completed=2,
        episodes_failed=1,
        repeated_failure_count=0,
        adaptation_proof_count=1,
        stagnation_score=0.1,
        progression_score=0.8,
        cooperation_score=0.5,
        information_usage_score=0.6,
        behavior_diversity_score=0.7,
        verdict="stable"
    )
    with pytest.raises(AttributeError):
        sc.entity_id = 15  # type: ignore


def test_entity_scorecard_to_dict_and_from_dict():
    sc = EntityBehaviorScorecard(
        run_id="run_1",
        entity_id=12,
        ticks_observed=100,
        route_families_used={"safe": 5},
        behavior_categories_used={"combat": 10},
        episodes_started=3,
        episodes_completed=2,
        episodes_failed=1,
        repeated_failure_count=0,
        adaptation_proof_count=1,
        stagnation_score=0.1,
        progression_score=0.8,
        cooperation_score=0.5,
        information_usage_score=0.6,
        behavior_diversity_score=0.7,
        verdict="stable"
    )
    data = sc.to_dict()
    assert data["entity_id"] == 12
    assert data["route_families_used"] == {"safe": 5}
    assert data["verdict"] == "stable"

    reconstructed = EntityBehaviorScorecard.from_dict(data)
    assert reconstructed.entity_id == 12
    assert reconstructed.route_families_used == {"safe": 5}
    assert reconstructed.verdict == "stable"
