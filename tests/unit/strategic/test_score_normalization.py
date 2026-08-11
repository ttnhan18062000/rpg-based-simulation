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


def test_locked_system_a_current_now_reachable_by_system_b_candidate_fix_confirmed():
    """Confirmed-fix regression guard for TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-
    SCALE-BUG.

    Before the fix, retention_margin(9.0) / current_max(_ADVENTURE_ROUTE_SCORE_MAX=2.9) ~ 3.10
    alone exceeded any realistic System-B candidate_pct, so a locked System-A current could
    never be interrupted by a System-B candidate, regardless of urgency
    (TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION's post-batch re-investigation
    confirmed this via a live 1365-call trace: 0 of 24 locked-branch calls ever switched).

    The fix normalizes the margin term against the fixed _GOAL_UTILITY_SCORE_MAX(100.0)
    instead of the variable current_max. For this test's exact scenario:
    current_pct = 0.1/2.9 ~ 0.0345.
    OLD: normalized_effective_current_pct = 0.0345 + 9.0/2.9 = 0.0345 + 3.10345 ~ 3.1379 --
    no realistic candidate_pct clears this, so the bug blocked the switch.
    NEW: normalized_effective_current_pct = 0.0345 + 9.0/100 = 0.0345 + 0.09 = 0.1245 --
    candidate_pct = 100.0/100 = 1.0 clears both 0.1245 and the 0.8 urgency floor, so the
    switch now succeeds. This test pins the FIXED behavior so a future regression back to
    dividing the margin term by current_max is caught immediately.
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
    assert result is not None
    assert result.current_project_id_set == "candidate"


def test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate():
    """AC1: a locked System-A current CAN be interrupted by a genuinely high-urgency System-B
    candidate under the fixed formula, using real (not synthetic) score values.

    Values are pulled directly from the live 1365-call monkeypatched trace captured in
    TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION's post-batch re-investigation
    (tick=2, hero=8 row) -- not hand-picked to pass.

    current_pct = 0.8207/2.9 ~ 0.28300.
    OLD: normalized_effective_current_pct = 0.28300 + 9.0/2.9 ~ 3.38645 -- candidate_pct
    (1.3258) cannot clear this, matching the trace's observed switched=False.
    NEW: normalized_effective_current_pct = 0.28300 + 9.0/100 = 0.37300 -- candidate_pct
    (1.3258) clears both 0.37300 and the 0.8 urgency floor, so the switch now succeeds.
    """
    current = ProjectState(
        id="current", kind=ProjectKind.SOCIAL, status=ProjectStatus.ACTIVE,
        score=0.8207, lock_until_tick=100
    )
    entity = _make_entity(
        profile=CognitionProfile(interruption_resistance=0.3, resistance_multiplier=30.0),
        current_project=current
    )
    candidate = ProjectState(
        id="candidate", kind=GoalKind.COMBAT_ENGAGE, status=ProjectStatus.ACTIVE, score=132.58
    )
    result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
    assert result is not None
    assert result.current_project_id_set == "candidate"


def test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate():
    """AC2: a locked System-A current is still NOT interrupted by a low-urgency System-B
    candidate under the fixed formula -- the fix must not overcorrect into "any candidate
    can always interrupt."

    Same current as test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate
    (current_pct ~ 0.28300, normalized_effective_current_pct ~ 0.37300 under the fixed formula).

    Sub-case 1: candidate.score=30.0 -> candidate_pct=0.30, fails the margin term itself
    (0.30 > 0.373 is False) -- blocked before even reaching the floor check.
    Sub-case 2: candidate.score=75.0 -> candidate_pct=0.75, clears the margin term
    (0.75 > 0.373) but fails the 0.8 urgency floor -- still blocked. This pins that the
    floor still binds even once the margin term is fixed, matching STRAT-186's "or explicit
    emergency" framing (only a genuinely urgent candidate, not merely a stronger one,
    bypasses).
    """
    current = ProjectState(
        id="current", kind=ProjectKind.SOCIAL, status=ProjectStatus.ACTIVE,
        score=0.8207, lock_until_tick=100
    )
    entity = _make_entity(
        profile=CognitionProfile(interruption_resistance=0.3, resistance_multiplier=30.0),
        current_project=current
    )

    low_urgency_candidate = ProjectState(
        id="candidate", kind=GoalKind.SOCIAL, status=ProjectStatus.ACTIVE, score=30.0
    )
    result = StrategicIntelligenceSystem.evaluate_project_switch(
        entity, low_urgency_candidate, current_tick=50
    )
    assert result is None

    below_floor_candidate = ProjectState(
        id="candidate", kind=GoalKind.SOCIAL, status=ProjectStatus.ACTIVE, score=75.0
    )
    result = StrategicIntelligenceSystem.evaluate_project_switch(
        entity, below_floor_candidate, current_tick=50
    )
    assert result is None
