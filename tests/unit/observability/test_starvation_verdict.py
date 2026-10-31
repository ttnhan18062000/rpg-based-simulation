"""TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY, V3 judge: the record says which opening steps were in reach and whether each was
taken. An untried step (row 27: the pull goes to the step) is a FAIL; no open way and no takeable step is SURV-06's poverty outcome, not a fail."""
from __future__ import annotations

from src.ai.goals.ways import WayKind
from src.observability.starvation_record import OpeningStepTried, StarvationDeathRecord, StarvationVerdict


def _record(union=(), attempted=()):
    return StarvationDeathRecord(entity_id=1, kind="worker", tick=9, cause_tick=9, ways_open_in_reach_union=tuple(union),
                                 ways_in_reach_at_death=tuple(union), ways_attempted=tuple(attempted), last_meal_tick=None)


def test_a_work_step_in_reach_and_never_taken_is_a_fail_even_when_the_meal_was_closed():
    rec = _record(union=(WayKind.WORK_SHIFT,))
    assert rec.opening_steps_in_reach() == (OpeningStepTried(WayKind.WORK_SHIFT, False),)
    assert rec.verdict() is StarvationVerdict.UNTRIED_STEP and rec.verdict().is_fail


def test_no_open_way_and_no_takeable_step_is_poverty_and_not_a_fail():
    rec = _record()
    assert rec.opening_steps_in_reach() == ()
    assert rec.verdict() is StarvationVerdict.POVERTY and not rec.verdict().is_fail


def test_every_step_taken_is_not_a_fail():
    rec = _record(union=(WayKind.FORAGE, WayKind.WORK_SHIFT), attempted=(WayKind.FORAGE, WayKind.WORK_SHIFT))
    assert all(s.tried for s in rec.opening_steps_in_reach())
    assert rec.verdict() is StarvationVerdict.TRIED and not rec.verdict().is_fail


def test_an_untried_non_step_way_is_still_a_fail():
    rec = _record(union=(WayKind.INN_MEAL,))
    assert rec.opening_steps_in_reach() == () and rec.verdict() is StarvationVerdict.UNTRIED_WAY and rec.verdict().is_fail


def test_the_fail_verdicts_coincide_with_the_existing_untried_rule():
    for union, attempted in (((), ()), ((WayKind.BUY,), ()), ((WayKind.BUY,), (WayKind.BUY,)), ((WayKind.INN_MEAL, WayKind.FORAGE), (WayKind.FORAGE,))):
        rec = _record(union, attempted)
        assert rec.verdict().is_fail is bool(rec.untried_in_reach())


def test_the_payload_carries_the_steps_and_the_verdict():
    payload = _record(union=(WayKind.WORK_SHIFT,)).to_payload()
    assert payload["opening_steps_in_reach"] == [{"way": "WORK_SHIFT", "tried": False}] and payload["verdict"] == "UNTRIED_STEP"
