"""
Cross-system score normalization tests for StrategicIntelligenceSystem.evaluate_project_switch().

STRAT-186 (generalized): candidates/currents from System A (AdventureRouteScorer,
ProjectKind-typed, declared max ~2.9) and System B (GoalRegistry, GoalKind-typed, declared
max 100.0) are normalized to a percentage of their own system's declared max before the
lock-bypass comparison, so the raw ~2.9-vs-100 scale gap does not itself determine the outcome.

Covers:
- Part 1 §Strategic: Project switching uses interruption resistance / margin logic
"""
import pytest
from src.core.strategic import (
    CognitionProfile, ProjectState, ProjectStatus, ProjectKind, GoalKind
)
from src.systems.strategic import StrategicIntelligenceSystem
from tests.unit.strategic.test_interruption_resistance import _make_entity


def test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current():
    """A maximal System A candidate (100% of its own ~2.9 declared max) is not structurally
    incapable of exceeding a low-urgency System B current project, once both are expressed as
    a percentage of their own system's max. This is the direct proof the mapper score-fidelity
    fix (Step 2) landed: under the old hardcoded score=1.0, a real System-A candidate could
    never reach this test's score=2.9 at all.

    Note: current's raw score/resistance are kept low (deviating from plan.md's suggested
    score=5.0) because the function's final `candidate.score > effective_current_score` check
    (STRAT-005/006) is unchanged, raw (unnormalized), and unconditional -- it applies after
    the lock-bypass gate on every path. A candidate_project.score of 2.9 (System A's own
    declared ceiling) cannot clear that raw check against a current whose raw
    score+retention_margin exceeds 2.9, regardless of how favorably the lock-bypass gate's
    normalized comparison resolves. Keeping current's raw score low isolates the assertion to
    what this test actually targets: that the normalized lock-bypass gate does not itself
    block a maximal System A candidate against a low-urgency System B current.
    """
    current = ProjectState(
        id="current", kind=GoalKind.SOCIAL, status=ProjectStatus.ACTIVE,
        score=1.0, lock_until_tick=100
    )
    entity = _make_entity(
        profile=CognitionProfile(interruption_resistance=0.01),
        current_project=current
    )
    # Lock-bypass gate (normalized): candidate_pct = 2.9/2.9 = 1.0
    # current_pct = 1.0/100 + (0.01*30)/100 = 0.01 + 0.003 = 0.013 -- 1.0 clears both the
    # floor and current's normalized effective pct, so the lock does not block.
    # Final raw check (unchanged): effective_current_score = 1.0 + 0.3 = 1.3; 2.9 > 1.3 clears.
    candidate = ProjectState(
        id="route_candidate", kind=ProjectKind.QUEST, status=ProjectStatus.ACTIVE, score=2.9
    )
    result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
    assert result is not None
    assert result.current_project_id_set == "route_candidate"


def test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current():
    """A low-urgency System A candidate cannot spuriously bypass a high-urgency System B
    current project purely because of the raw ~2.9-vs-100 scale gap."""
    current = ProjectState(
        id="current", kind=GoalKind.COMBAT_ENGAGE, status=ProjectStatus.ACTIVE,
        score=90.0, lock_until_tick=100
    )
    entity = _make_entity(
        profile=CognitionProfile(interruption_resistance=0.3),
        current_project=current
    )
    # candidate_pct = 0.5 / 2.9 ≈ 0.17
    # current_pct = 90/100 + (0.3*30)/100 = 0.9 + 0.09 = 0.99
    candidate = ProjectState(
        id="route_candidate", kind=ProjectKind.QUEST, status=ProjectStatus.ACTIVE, score=0.5
    )
    result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
    assert result is None


def test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation():
    """Documented-limitation regression guard, not a desired-behavior test.

    TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION's post-batch re-investigation
    confirmed, via a live 1365-call trace, that 0 of 24 real evaluate_project_switch() calls
    made while current.lock_until_tick > current_tick ever passed -- retention_margin(9.0) /
    _ADVENTURE_ROUTE_SCORE_MAX(2.9) ~ 3.10 alone exceeds any realistic System-B candidate_pct,
    so a locked System-A current can never be interrupted by a System-B candidate today,
    regardless of urgency. This is a real, confirmed, independently-ticketed defect
    (TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG), not fixed by this ticket.
    This test pins the CURRENT (buggy) behavior so a future change to either direction --
    the bug getting silently fixed, or a regression making it worse -- is caught and requires
    an explicit decision, not missed by accident.
    """
    current = ProjectState(
        id="current", kind=ProjectKind.SOCIAL, status=ProjectStatus.ACTIVE,
        score=0.1, lock_until_tick=100  # minimal-score, freshly-locked System-A current
    )
    entity = _make_entity(
        profile=CognitionProfile(interruption_resistance=0.3, resistance_multiplier=30.0),
        current_project=current
    )
    # Maximal-urgency System-B candidate: CombatEngageScorer's own real ceiling is
    # 40 + bravery(1.0)*40 + stamina_ratio(1.0)*20 = 100 -- the highest realistic value.
    candidate = ProjectState(
        id="candidate", kind=GoalKind.COMBAT_ENGAGE, status=ProjectStatus.ACTIVE, score=100.0
    )
    result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
    assert result is None, (
        "If this now returns a StrategicUpdate, TCK-20260811-INTERRUPTION-BYPASS-RETENTION-"
        "MARGIN-SCALE-BUG's normalization defect has been fixed (or the formula changed) -- "
        "update this test to assert the new, intended behavior instead of the documented "
        "limitation, and close/update that ticket accordingly. Do not just delete this test."
    )
