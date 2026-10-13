"""Owner decision 42 (memo row 65): every living body heals naturally, twice as fast asleep or resting, none at the starving line,
half speed while weakened. Derived from existing fields; no new state."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.engine import natural_healing as nh
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence


def _gain(hp, max_hp, hunger=0.0, sleep_debt=0.0, resting=False, tick=1, eid=0):
    combat = replace(V2EntityBuilder(1).kind("human").build().combat, hp=hp, max_hp=max_hp)
    bio = replace(V2EntityBuilder(1).kind("human").build().biological, hunger=hunger, sleep_debt=sleep_debt)
    return nh.hp_gain(combat, bio, resting, tick, eid)


def _ticks_to_full(max_hp, eid, **kw):
    hp, tick = 1, 0
    while hp < max_hp and tick < 40000:
        tick += 1
        hp += _gain(hp, max_hp, tick=tick, eid=eid, **kw)
    return tick


@pytest.mark.parametrize("max_hp,period", [(35, 274), (100, 96), (800, 12)])
def test_an_awake_body_gains_one_hp_every_period(max_hp, period):
    assert nh.heal_period(max_hp, False, 1.0) == period
    assert sum(_gain(1, max_hp, tick=t) for t in range(1, period * 4 + 1)) == 4


def test_a_resting_body_heals_at_twice_the_rate():
    assert nh.heal_period(100, True, 1.0) * 2 == nh.heal_period(100, False, 1.0)


def test_nothing_heals_at_or_past_the_starving_line():
    assert not any(_gain(1, 100, hunger=95.0, tick=t) for t in range(1, 500))
    assert any(_gain(1, 100, hunger=94.99, tick=t) for t in range(1, 500))


def test_a_weakened_body_heals_at_half_speed_the_worse_stage_deciding():
    assert nh.heal_period(100, False, 0.5) == 2 * nh.heal_period(100, False, 1.0)
    assert nh.heal_period(100, False, 0.5) == 192
    assert sum(_gain(1, 100, sleep_debt=90.0, tick=t) for t in range(1, 193)) == 1  # weakened by sleep debt alone
    assert sum(_gain(1, 100, hunger=90.0, tick=t) for t in range(1, 193)) == 1  # weakened by hunger alone


def test_it_never_passes_max_hp_and_never_raises_the_dead():
    assert all(_gain(100, 100, tick=t) == 0 for t in range(1, 300))
    assert all(_gain(0, 100, tick=t) == 0 for t in range(1, 300))


@pytest.mark.parametrize("eid", [0, 3, 41])
def test_bodies_of_different_size_are_whole_in_about_the_same_time(eid):
    awake = [_ticks_to_full(m, eid) for m in (35, 100, 800)]
    rest = [_ticks_to_full(m, eid, resting=True) for m in (35, 100, 800)]
    assert all(8400 <= t <= 10800 for t in awake) and all(4200 <= t <= 5400 for t in rest)


def test_it_is_deterministic_and_staggered_by_entity_id():
    assert [_gain(1, 100, tick=t, eid=5) for t in range(1, 400)] == [_gain(1, 100, tick=t, eid=5) for t in range(1, 400)]
    assert len({next(t for t in range(1, 200) if _gain(1, 100, tick=t, eid=e)) for e in range(60)}) > 30


def _step(ent, tick):
    state = AuthoritativeState(tick=tick, seed=1, entities={})
    changes = ApplyPath._compute_entity_changes(ent, None, tick, SystemCadence(), True, False, [], state)
    return replace(ent, **{k: v for k, v in changes.items() if k in ("combat", "biological", "lifecycle")})


def _hurt(eid=1):
    ent = V2EntityBuilder(eid).kind("human").combat(hp=50, max_hp=100, alive=True).lifecycle(active=True).build()
    return replace(ent, biological=replace(ent.biological, hunger=0.0, sleep_debt=0.0))


def test_the_apply_path_heals_a_hurt_awake_body_and_a_fed_one_only():
    ent = _hurt()
    for t in range(1, 600):
        ent = _step(ent, t)
    assert ent.combat.hp > 50
    starving = replace(_hurt(), biological=replace(_hurt().biological, hunger=99.0))
    hp0 = starving.combat.hp
    for t in range(1, 60):
        starving = _step(starving, t)
    assert starving.combat.hp <= hp0
