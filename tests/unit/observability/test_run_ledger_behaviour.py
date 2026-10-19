"""Run ledger behaviour counters (flee, pursuit, perception): typed movement mode as entity-ticks and episodes, perception sampled on a fixed
cadence, keyed by kind group and person flag; a pure observer that leaves the state it reads untouched."""
from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

from src.ai.goals.kind_group import is_person, kind_group
from src.core.movement_modes import MovementMode
from src.observability.run_ledger import PERCEPTION_SAMPLE_EVERY, RunLedger
from tests.unit.observability.test_run_ledger import _update
from tests.unit.observability.test_starvation_death_record import WHO, _at_tick, _world


@pytest.fixture(autouse=True)
def _clean():
    RunLedger.reset_run_state()
    RunLedger.configure(True)
    yield
    RunLedger.reset_run_state()


def _moded(state, mode, tick, alive=True):
    e = state.entities[WHO]
    cur = replace(state, tick=tick)
    object.__setattr__(cur, "entities", {WHO: replace(e, navigation=replace(e.navigation, movement_mode=mode), combat=replace(e.combat, alive=alive))})
    return cur


def _who(state):
    e = state.entities[WHO]
    return f"{kind_group(e)}|{int(is_person(e))}"


def _behaviour():
    return RunLedger.tally_event().payload["behaviour"]


def test_flee_counts_entity_ticks_and_one_episode_per_entry():
    base = _world()
    who = _who(base)
    modes = [MovementMode.WANDER, MovementMode.RETREAT, MovementMode.RETREAT, MovementMode.WANDER, MovementMode.RETREAT]
    prior = _moded(base, MovementMode.WANDER, 1)
    for i, m in enumerate(modes, start=2):
        cur = _moded(base, m, i)
        RunLedger.observe(prior, cur, _update())
        prior = cur
    b = _behaviour()
    assert b[f"flee_ticks|{who}"] == 3
    assert b[f"flee_episodes|{who}"] == 2
    assert not any(k.startswith("pursuit") for k in b)


def test_pursue_and_intercept_are_both_pursuit_and_moving_between_them_is_one_episode():
    base = _world()
    who = _who(base)
    prior = _moded(base, MovementMode.WANDER, 1)
    for i, m in enumerate([MovementMode.PURSUE, MovementMode.INTERCEPT, MovementMode.HOLD], start=2):
        cur = _moded(base, m, i)
        RunLedger.observe(prior, cur, _update())
        prior = cur
    b = _behaviour()
    assert b[f"pursuit_ticks|{who}"] == 2
    assert b[f"pursuit_episodes|{who}"] == 1


def test_a_dead_entity_counts_nothing():
    base = _world()
    RunLedger.observe(_moded(base, MovementMode.WANDER, 1), _moded(base, MovementMode.RETREAT, 2, alive=False), _update())
    assert _behaviour() == {}


def test_perception_is_sampled_only_on_the_cadence_and_the_sample_count_is_reported():
    base = _world()
    who = _who(base)
    seen = [object(), object()]
    with patch("src.observability.run_ledger.perceived_hostiles", return_value=seen) as pf:
        prior = _moded(base, MovementMode.WANDER, 0)
        for t in range(1, 2 * PERCEPTION_SAMPLE_EVERY + 1):
            cur = _moded(base, MovementMode.WANDER, t)
            RunLedger.observe(prior, cur, _update())
            prior = cur
    payload = RunLedger.tally_event().payload
    assert payload["perception_samples"] == 2
    assert pf.call_count == 2
    assert payload["behaviour"][f"perceiving_ticks|{who}"] == 2
    assert payload["behaviour"][f"perceived_hostiles|{who}"] == 4


def test_observing_does_not_change_the_states_it_reads():
    base = _world()
    prior, cur = _moded(base, MovementMode.WANDER, 9), _moded(base, MovementMode.RETREAT, 10)
    before = (prior.entities[WHO].navigation, cur.entities[WHO].navigation, cur.tick)
    RunLedger.observe(prior, cur, _update())
    assert (prior.entities[WHO].navigation, cur.entities[WHO].navigation, cur.tick) == before


def test_the_counters_are_empty_and_the_tally_keys_exist_for_a_run_with_no_flee_pursuit_or_perception():
    base = _world()
    RunLedger.observe(_moded(base, MovementMode.WANDER, 1), _moded(base, MovementMode.WANDER, 2), _update())
    payload = RunLedger.tally_event().payload
    assert payload["behaviour"] == {} and payload["perception_samples"] == 0


def test_a_step_is_counted_once_under_the_terrain_of_the_tile_entered():
    base = _world()
    e = base.entities[WHO]
    x, y = e.navigation.position

    def at(px, py, tick):
        cur = replace(base, tick=tick, terrain={(int(px), int(py)): "FOREST"})
        object.__setattr__(cur, "entities", {WHO: replace(e, navigation=replace(e.navigation, position=(px, py)))})
        return cur

    RunLedger.observe(at(x, y, 1), at(x + 1.0, y, 2), _update())
    RunLedger.observe(at(x + 1.0, y, 3), at(x + 1.2, y, 4), _update())  # still inside the same tile: no step
    assert _behaviour()["steps|FOREST"] == 1
