"""A chosen rest or sleep lasts until the sleep need is met (2.153 / STRAT-293, Unified; designer ruling 2026-10-30, N14).

A REST begun at the wake line (58.8) ended after one tick, so the fatigue project (which completes below REST_MIN_SLEEP_DEBT, 20) never did and squatters
chattered on the inn's door tiles. A chosen SLEEP or REST now ends strictly below the floor; a collapse keeps the wake-line end (decision 41). No new constant.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.engine.pipeline_phases.actions import _survival_action_ends
from src.engine.sleep_debt import COLLAPSE_FLAG, REST_MIN_SLEEP_DEBT, SLEEP_DEBT, chosen_rest_is_met, is_rested_enough
from src.engine.tactical_rest import REST_MIN_SLEEP_DEBT as REEXPORTED


def _at(debt):
    return V2EntityBuilder(1).kind("hero").location(1.0, 1.0).biological(sleep_debt=debt).build()


def _ends(action, debt, collapse=False):
    payload = {"action": action, **({COLLAPSE_FLAG: True} if collapse else {})}
    return _survival_action_ends(action, True, "SUCCESS", None, (payload, _at(debt)))


def test_the_floor_is_the_existing_constant_moved_with_its_old_import_path_kept():
    assert REST_MIN_SLEEP_DEBT == 20.0 and REEXPORTED is REST_MIN_SLEEP_DEBT


def test_a_rest_begun_at_the_wake_line_is_not_ended_by_the_wake_line():
    for action in ("REST", "SLEEP"):
        assert _ends(action, SLEEP_DEBT.wake_line + 0.1) is False   # was True below the line
        assert _ends(action, SLEEP_DEBT.wake_line - 0.1) is False   # the p22 hover: a REST at 59 now runs on
        assert _ends(action, 40.0) is False


def test_a_sleep_from_90_ends_below_the_floor_not_at_the_wake_line():
    for action in ("REST", "SLEEP"):
        assert _ends(action, 90.0) is False and _ends(action, 58.7) is False
        assert _ends(action, REST_MIN_SLEEP_DEBT) is False    # strictly below: the project completes and the goal exits only below 20
        assert _ends(action, REST_MIN_SLEEP_DEBT - 0.1) is True
    assert chosen_rest_is_met(19.9) and not chosen_rest_is_met(20.0)


def test_a_collapse_keeps_the_wake_line_end_and_a_sleep_chosen_after_it_runs_to_the_floor():
    assert _ends("SLEEP", 98.0, collapse=True) is False
    assert _ends("SLEEP", SLEEP_DEBT.wake_line - 0.1, collapse=True) is True and is_rested_enough(SLEEP_DEBT.wake_line - 0.1)
    assert _ends("SLEEP", SLEEP_DEBT.wake_line - 0.1, collapse=False) is False   # the same debt, chosen: it keeps sleeping


def test_only_a_successful_survival_action_ends_and_other_actions_end_as_before():
    assert _survival_action_ends("REST", True, "FAILURE", None, ({"action": "REST"}, _at(10.0))) is False
    assert _survival_action_ends("EAT", True, "SUCCESS", None, ({"action": "EAT"}, _at(99.0))) is True
