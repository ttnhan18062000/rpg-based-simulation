"""
tests/unit/strategic/test_project_system_precedence.py

Regression guard for the System A (adventure_decision) vs. System B
(strategic_intelligence) StrategicUpdate merge precedence
(TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP, investigation Open Question 1).

StrategicUpdate.merge is last-write-wins for current_project_id_set /
current_objective_id_set (src/core/updates.py:549-550). Since
"strategic_intelligence" (System B) runs after "adventure_decision" (System A)
in the same tick (src/engine/pipeline.py), System B's selection wins whenever
it actually produces a value this tick. This test documents that behavior as a
tested, intentional property rather than an emergent, unverified side effect
of phase ordering — this ticket does not change merge semantics or unify the
two systems (explicit Out of Scope).
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
