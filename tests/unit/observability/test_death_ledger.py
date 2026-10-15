"""Death ledger: every hp loss has a typed source and every death one typed record (cause, last attacker, hazard kind, hp lost by source).

Staged on single states and updates (the ledger is a pure observer). Sources are asserted by kind, never by a number tuned to a world.
"""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.core.death_cause import DeathCause, DeathRecord, HpLossSource, death_cause_of
from src.core.updates import CombatUpdate
from src.engine.starvation import STARVING_LINE
from src.observability.death_ledger import LEDGER_LIVE_EVENT, LEDGER_TALLY_EVENT, DeathLedger
from src.observability.run_ledger import RunLedger
from tests.unit.observability.test_starvation_death_record import WHO, _at_tick, _world


@pytest.fixture(autouse=True)
def _clean():
    DeathLedger.reset_run_state()
    DeathLedger.configure(STARVING_LINE, True)
    yield
    DeathLedger.reset_run_state()


def _states(hp_before=50, hp_after=50, hunger=0.0, alive=True, record=None, prior_record=None):
    """The same body on two ticks: `prior` (tick 10) and `current` (tick 11)."""
    prior = _at_tick(_world(hunger=hunger), 10)
    e = prior.entities[WHO]
    object.__setattr__(prior, "entities", {WHO: replace(e, combat=replace(e.combat, hp=hp_before, alive=True),
                                                       lifecycle=replace(e.lifecycle, death_record=prior_record))})
    cur = _at_tick(_world(hunger=hunger), 11)
    ec = cur.entities[WHO]
    object.__setattr__(cur, "entities", {WHO: replace(ec, combat=replace(ec.combat, hp=hp_after, alive=alive),
                                                      lifecycle=replace(ec.lifecycle, death_record=record))})
    return prior, cur


def _update(**combat):
    return SimpleNamespace(entity_updates={WHO: SimpleNamespace(combat=CombatUpdate(**combat))})


def _tally():
    return DeathLedger.tally_event().payload


def _lost(payload, source):
    return sum(v for k, v in payload["hp_lost"].items() if k.endswith("|" + source.value))


def test_a_hit_is_a_typed_source_and_the_attacker_is_remembered():
    prior, cur = _states(50, 40)
    DeathLedger.observe(prior, cur, _update(hp_delta=-10, damage_taken=10, attacker_id=7))
    assert _lost(_tally(), HpLossSource.HIT) == 10


def test_hazard_drain_is_its_own_source_even_beside_a_hit():
    prior, cur = _states(50, 40)
    DeathLedger.observe(prior, cur, _update(hp_delta=-10, hazard_damage=4, attacker_id=7))
    p = _tally()
    assert _lost(p, HpLossSource.HAZARD) == 4 and _lost(p, HpLossSource.HIT) == 6


def test_a_starving_body_losing_hp_with_no_update_is_the_starvation_drain():
    """The two hp the D75 attribution could not place: no update's hp_delta carries them, the apply path's passive branch takes them."""
    prior, cur = _states(50, 48, hunger=STARVING_LINE + 1.0)
    DeathLedger.observe(prior, cur, SimpleNamespace(entity_updates={}))
    p = _tally()
    assert _lost(p, HpLossSource.STARVATION) == 2 and p["unattributed_hp"] == 0


def test_a_loss_nothing_explains_is_counted_unattributed():
    prior, cur = _states(50, 49, hunger=0.0)
    DeathLedger.observe(prior, cur, SimpleNamespace(entity_updates={}))
    assert _tally()["unattributed_hp"] == 1


def test_healing_is_not_a_loss():
    prior, cur = _states(40, 45)
    DeathLedger.observe(prior, cur, _update(hp_delta=5))
    assert _tally()["hp_lost"] == {}


def test_a_death_is_tallied_once_by_cause_with_the_hp_the_body_lost_by_source():
    DeathLedger.observe(*_states(50, 45), _update(hp_delta=-5, attacker_id=9, damage_taken=5))
    prior, cur = _states(5, 0, alive=False, record=DeathRecord(DeathCause.COMBAT, 11, last_attacker_id=9))
    DeathLedger.observe(prior, cur, _update(hp_delta=-5, damage_taken=5, attacker_id=9))
    p = _tally()
    (row,) = p["records"]
    assert row["cause"] == DeathCause.COMBAT.value and row["tick"] == 11 and row["hp_lost"] == {HpLossSource.HIT.value: 10}
    assert sum(p["deaths"].values()) == 1
    DeathLedger.observe(cur, cur, _update())  # the same record a tick later is not a second death
    assert len(_tally()["records"]) == 1


def test_a_body_that_dies_with_no_death_record_is_unknown_and_counted():
    prior, cur = _states(1, 0, alive=False, record=None)
    DeathLedger.observe(prior, cur, _update(hp_delta=-1, attacker_id=2))
    assert _tally()["unknown_deaths"] == 1
    DeathLedger.observe(cur, replace(cur), _update())
    assert _tally()["unknown_deaths"] == 1


def test_the_typed_cause_reads_every_reason_the_lifecycle_records():
    for cause in DeathCause:
        if cause is not DeathCause.UNKNOWN:
            assert death_cause_of(cause.value) is cause
    assert death_cause_of(None) is DeathCause.UNKNOWN and death_cause_of("nonsense") is DeathCause.UNKNOWN


def test_a_not_live_ledger_is_silent_and_writes_no_tally():
    DeathLedger.reset_run_state()
    DeathLedger.configure(STARVING_LINE, False)
    prior, cur = _states(50, 40)
    assert DeathLedger.observe(prior, cur, _update(hp_delta=-10)) == [] and DeathLedger.closing_event({}) is None


def test_the_live_header_opens_once_and_the_tally_closes_a_live_run():
    prior, cur = _states(50, 40)
    first = DeathLedger.observe(prior, cur, _update(hp_delta=-10))
    assert [e.event_type for e in first] == [LEDGER_LIVE_EVENT]
    assert DeathLedger.observe(prior, cur, _update(hp_delta=-10)) == []
    assert DeathLedger.closing_event({LEDGER_LIVE_EVENT: 1}).event_type == LEDGER_TALLY_EVENT


def test_the_ledger_reads_the_states_and_writes_nothing_back():
    prior, cur = _states(5, 0, alive=False, record=DeathRecord(DeathCause.COMBAT, 11))
    before = (prior.entities[WHO], cur.entities[WHO])
    DeathLedger.observe(prior, cur, _update(hp_delta=-5, attacker_id=9))
    assert (prior.entities[WHO], cur.entities[WHO]) == before
    assert RunLedger._deaths == {}
