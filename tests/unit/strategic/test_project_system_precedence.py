"""
tests/unit/strategic/test_project_system_precedence.py

Regression guard for StrategicUpdate merge precedence
(TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP, investigation Open Question 1).

StrategicUpdate.merge is last-write-wins for current_project_id_set /
current_objective_id_set (src/core/updates.py:549-550). Historically (before
TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE) this mattered because a separate,
earlier-running "adventure_decision" pipeline phase (System A) could be
overwritten by the later "strategic_intelligence" phase (System B) within the
same tick. As of that ticket, AdventureDecisionPhase no longer exists:
adventure routing is now a tier-5 GoalScorer candidate
(AdventureGoalScorer, src/ai/goals/adventure_scorer.py) evaluated inside
GoalRegistry.get_all_scores() within evaluate_strategic_intent() itself — the
two systems no longer run as separate phases at all. This test still documents
StrategicUpdate.merge's own last-write-wins property as a tested, intentional
fact of the merge mechanism (not phase-ordering-dependent), which remains true
and load-bearing for the current single-phase design.
"""
from src.core.updates import StrategicUpdate


def test_system_b_strategic_update_wins_last_write_precedence():
    system_a_update = StrategicUpdate(
        current_project_id_set="proj_a",
        current_objective_id_set="obj_a",
    )
    system_b_update = StrategicUpdate(
        current_project_id_set="proj_b",
        current_objective_id_set="obj_b",
    )

    merged = system_a_update.merge(system_b_update)

    assert merged.current_project_id_set == "proj_b"
    assert merged.current_objective_id_set == "obj_b"


def test_system_b_noop_update_does_not_clobber_system_a_selection():
    system_a_update = StrategicUpdate(
        current_project_id_set="proj_a",
        current_objective_id_set="obj_a",
    )
    system_b_noop = StrategicUpdate()

    merged = system_a_update.merge(system_b_noop)

    assert merged.current_project_id_set == "proj_a"
    assert merged.current_objective_id_set == "obj_a"
