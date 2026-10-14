"""Owner decision 36 (SURV-02 amendment): staged starvation. weak first, then slow health loss, death over days.

Stages derive from hunger alone (no new state field): weakened at 85 (recovery and attack scaled), starving at 95 (1 HP every
round(6000 / max_hp) life-due ticks, staggered by entity id), so a full-health body dies about 6000 ticks (2.5 days) after the line.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.engine import starvation as sv
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.core.state import AuthoritativeState


def test_the_table_is_the_one_place_the_stages_are_tuned():
    assert (sv.STARVATION.weakened_line, sv.STARVATION.starving_line, sv.STARVATION.death_ticks) == (85.0, 95.0, 6000)
    assert sv.WEAKENED_LINE < sv.STARVING_LINE


@pytest.mark.parametrize("hunger,weakened,scale,attack", [(0.0, False, 1.0, 1.0), (84.99, False, 1.0, 1.0), (85.0, True, 0.5, 0.8), (100.0, True, 0.5, 0.8)])
def test_the_weakened_stage_scales_recovery_and_attack_from_its_line(hunger, weakened, scale, attack):
    assert sv.is_weakened(hunger) is weakened
    assert sv.recovery_scale(hunger) == scale
    assert sv.attack_scale(hunger) == attack


def test_no_health_is_lost_below_the_starving_line():
    assert all(sv.hp_loss(94.99, 100, t, e) == 0 for t in range(0, 500) for e in (0, 1, 7))
    assert any(sv.hp_loss(95.0, 100, t, 0) for t in range(0, 60))


@pytest.mark.parametrize("max_hp,period", [(35, 171), (100, 60), (800, 8), (8000, 1)])
def test_the_loss_period_follows_max_hp(max_hp, period):
    assert sv.hp_loss_period(max_hp) == period


@pytest.mark.parametrize("max_hp", [35, 100, 800])
@pytest.mark.parametrize("entity_id", [0, 1, 17, 59, 123])
def test_a_full_health_body_dies_about_six_thousand_ticks_after_the_line(max_hp, entity_id):
    hp, tick = max_hp, 0
    while hp > 0 and tick < 20000:
        tick += 1
        hp -= sv.hp_loss(100.0, max_hp, tick, entity_id)
    assert 4800 <= tick <= 7200, f"max_hp {max_hp} id {entity_id} died {tick} ticks after the line"


def test_a_hurt_body_dies_sooner_and_the_staggering_spreads_the_first_loss():
    def death(hp, eid, max_hp=100):
        tick = 0
        while hp > 0:
            tick += 1
            hp -= sv.hp_loss(100.0, max_hp, tick, eid)
        return tick
    assert death(50, 3) < death(100, 3)
    first = {next(t for t in range(1, 200) if sv.hp_loss(100.0, 100, t, e)) for e in range(60)}
    assert len(first) == 60  # one entity per residue: a hungry population does not lose health on the same tick


def test_the_loss_is_indexed_by_the_life_due_ordinal_under_a_raised_cadence():
    assert sv.hp_loss(100.0, 100, 600, 0, lifecycle_cadence=5) == sv.hp_loss(100.0, 100, 120, 0, lifecycle_cadence=1)


def test_the_weakened_attack_multiplier_compounds_with_exhaustion():
    from src.engine.combat import CombatResolutionSystem
    from src.core.enums import Faction
    a = V2EntityBuilder(1).kind("hero").identity(faction=Faction.HERO_GUILD).combat(hp=100, max_hp=100, readiness=100.0, alive=True).lifecycle(active=True).build()
    d = V2EntityBuilder(2).kind("monster").identity(faction=Faction.MONSTER_HORDE).location(11.0, 10.0).combat(hp=100, max_hp=100, alive=True).lifecycle(active=True).build()
    state = AuthoritativeState(tick=1, seed=1, entities={1: a, 2: d})
    def mult(bio):
        atk, _dfn, trace = CombatResolutionSystem._get_tactical_multipliers(replace(a, biological=bio), d, state)
        return atk, trace

    base = a.biological
    fed, _ = mult(replace(base, hunger=0.0, sleep_debt=0.0))
    weak, t1 = mult(replace(base, hunger=90.0, sleep_debt=0.0))
    both, t2 = mult(replace(base, hunger=90.0, sleep_debt=90.0))
    assert weak == pytest.approx(fed * 0.8) and t1["STARVATION_WEAKENED"] == 0.8
    assert both == pytest.approx(fed * 0.8 * 0.8) and "EXHAUSTION" in t2 and "STARVATION_WEAKENED" in t2
