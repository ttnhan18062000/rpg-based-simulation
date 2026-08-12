"""
Unit tests for RegionStabilizationGoalScorer (TCK-20260811-REGION-STABILIZATION-GOAL-SCORER).

Covers AC1 (registration), AC3 (GoalScore protocol, metadata carries raw score, never utility),
New Finding #7 (raw score calibrated to the 2.9 ceiling, not the pre-migration urgency*100), and
New Finding #8 (target_pos resolves to the region's centroid, not a bare region id) per plan.md
Step 7.
"""
from __future__ import annotations

import pytest

from src.ai.goals import GoalRegistry
from src.ai.goals.base import GoalScore
from src.ai.goals.region_stabilization_scorer import RegionStabilizationGoalScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import GoalKind, ProjectKind, ObjectiveKind


def _entity(eid: int = 1, pos: tuple = (5.0, 5.0)):
    return V2EntityBuilder(eid).kind("hero").location(*pos).build()


def _state(entities=None, regions=None, tick=0):
    return AuthoritativeState(tick=tick, seed=42, entities=entities or {}, regions=regions or {})


# --- AC1 ---------------------------------------------------------------------------------


def test_goal_kind_region_stabilization_is_registered_member():
    assert GoalKind("region_stabilization") == GoalKind.REGION_STABILIZATION
    assert isinstance(
        GoalRegistry._scorers[GoalKind.REGION_STABILIZATION], RegionStabilizationGoalScorer
    )


def test_region_stabilization_goal_scorer_implements_goal_scorer_protocol():
    entity = _entity()
    region = RegionState(id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=0.95)
    state = _state(entities={1: entity}, regions={"swamp": region})
    score = RegionStabilizationGoalScorer().score(entity, state)
    assert isinstance(score, GoalScore)


# --- AC3 -----------------------------------------------------------------------------------


def test_region_stabilization_goal_scorer_metadata_carries_raw_score():
    """
    Worked arithmetic: hazard_level=0.95 -> urgency=min(1.0,(0.95-0.7)/0.3)=0.833333...
    raw_score = urgency * 2.9 = 2.4166666666666665.
    """
    entity = _entity()
    region = RegionState(id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=0.95)
    state = _state(entities={1: entity}, regions={"swamp": region})
    score = RegionStabilizationGoalScorer().score(entity, state)

    assert set(score.metadata.keys()) == {"region_id", "raw_score", "proj_kind", "obj_kind"}
    assert score.metadata["region_id"] == "swamp"
    assert score.metadata["raw_score"] == pytest.approx(2.4166666666666665)
    assert score.metadata["proj_kind"] == ProjectKind.STABILIZE
    assert score.metadata["obj_kind"] == ObjectiveKind.INVESTIGATE
    assert score.metadata["raw_score"] != score.utility


def test_region_stabilization_goal_scorer_low_hazard_returns_zero_utility_no_target():
    entity = _entity()
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), hazard_level=0.5)
    state = _state(entities={1: entity}, regions={"forest": region})
    score = RegionStabilizationGoalScorer().score(entity, state)
    assert score.kind == GoalKind.REGION_STABILIZATION
    assert score.utility == 0.0
    assert score.target_id is None


def test_region_stabilization_goal_scorer_no_region_at_position_returns_zero_utility():
    entity = _entity(pos=(1000.0, 1000.0))
    region = RegionState(id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=0.95)
    state = _state(entities={1: entity}, regions={"swamp": region})
    score = RegionStabilizationGoalScorer().score(entity, state)
    assert score.kind == GoalKind.REGION_STABILIZATION
    assert score.utility == 0.0
    assert score.target_id is None


# --- New Finding #8 ------------------------------------------------------------------------


def test_region_stabilization_target_pos_resolves_to_region_centroid():
    entity = _entity(pos=(5.0, 5.0))
    region = RegionState(id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=0.95)
    state = _state(entities={1: entity}, regions={"swamp": region})
    score = RegionStabilizationGoalScorer().score(entity, state)
    assert score.target_pos == (
        (region.bounds[0] + region.bounds[2]) / 2.0,
        (region.bounds[1] + region.bounds[3]) / 2.0,
    )


# --- New Finding #7 --------------------------------------------------------------------------


def test_region_stabilization_goal_scorer_raw_score_calibrated_to_2_9_not_100():
    """The single highest-value regression guard in this file: at hazard_level=1.0, urgency=1.0
    and raw_score must be 2.9 (the _ADVENTURE_ROUTE_SCORE_MAX ceiling), NOT 100.0 (the
    pre-migration urgency*100 formula, only valid while kind="stabilize" was a bare string)."""
    entity = _entity()
    region = RegionState(id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=1.0)
    state = _state(entities={1: entity}, regions={"swamp": region})
    score = RegionStabilizationGoalScorer().score(entity, state)
    assert score.metadata["raw_score"] == pytest.approx(2.9)
    assert score.metadata["raw_score"] != 100.0
