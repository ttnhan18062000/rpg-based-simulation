"""Unit tests for `pending_grief_triggers(state)` (decision 80, grief as state; replaces the EventExtractor.detect_grief_triggers tests of
TCK-20260824-GRIEF-NEMESIS-REACHABILITY, Step 4).

A body that died on the previous tick carries a `death_record` with `tick == state.tick - 1`; every still-active entity whose trust toward it meets
ALLY_TRUST_THRESHOLD (0.30) is owed a trigger `(griever_id, dead_id, urgency)`, unless `grief_drained_tick` already covers that death tick.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.death_cause import DeathCause, DeathRecord
from src.core.grief_triggers import pending_grief_triggers
from src.core.social_constants import ALLY_TRUST_THRESHOLD
from src.core.state import AuthoritativeState


def _body(eid: int, trust: dict | None = None, dead_tick: int | None = None):
    e = V2EntityBuilder(eid).kind("worker").location(float(eid), 0.0).build()
    if trust:
        e = replace(e, social=replace(e.social, trust_history=dict(trust)))
    if dead_tick is not None:
        e = replace(e, lifecycle=replace(e.lifecycle, active=False, death_record=DeathRecord(cause=DeathCause.COMBAT, tick=dead_tick)))
    return e


def _state(*bodies, tick: int = 6, drained: int = -1) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=1, entities={b.id: b for b in bodies}, grief_drained_tick=drained)


def test_finds_the_qualifying_ally():
    assert pending_grief_triggers(_state(_body(1, {2: 0.9}), _body(2, dead_tick=5))) == [(1, 2, round(min(1.0, 0.9 * 0.8), 6))]


def test_below_threshold_is_not_included():
    assert pending_grief_triggers(_state(_body(1, {2: ALLY_TRUST_THRESHOLD - 0.01}), _body(2, dead_tick=5))) == []


def test_no_death_no_triggers():
    assert pending_grief_triggers(_state(_body(1, {2: 0.9}), _body(2))) == []


def test_a_dead_griever_gives_no_trigger():
    assert pending_grief_triggers(_state(_body(1, {2: 0.9}, dead_tick=5), _body(2, dead_tick=5))) == []


def test_multiple_grievers():
    triggers = pending_grief_triggers(_state(_body(1, {3: 0.9}), _body(2, {3: 0.5}), _body(3, dead_tick=5)))
    assert sorted(triggers) == sorted([(1, 3, round(min(1.0, 0.9 * 0.8), 6)), (2, 3, round(min(1.0, 0.5 * 0.8), 6))])


def test_only_the_previous_ticks_deaths_are_owed():
    assert pending_grief_triggers(_state(_body(1, {2: 0.9}), _body(2, dead_tick=3), tick=6)) == []
    assert pending_grief_triggers(_state(_body(1, {2: 0.9}), _body(2, dead_tick=6), tick=6)) == []


def test_a_drained_death_tick_is_owed_once():
    bodies = (_body(1, {2: 0.9}), _body(2, dead_tick=5))
    assert pending_grief_triggers(_state(*bodies, drained=4)) != []
    assert pending_grief_triggers(_state(*bodies, drained=5)) == []


def test_a_body_with_no_death_record_gives_no_trigger():
    assert pending_grief_triggers(_state(_body(1, {2: 0.9}), replace(_body(2), lifecycle=replace(_body(2).lifecycle, active=False)))) == []
