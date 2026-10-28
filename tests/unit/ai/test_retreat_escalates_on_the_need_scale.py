"""SURV-07 on one scale (owner memo row 88, TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE): the goal-level retreat score escalates with the wound the way a
need escalates with its level (`need_pull`: onset 0.6, full 0.85 of the damage fraction `1 - hp/max_hp`, death the consequence line), and only while a hostile ACTS on the
subject (`acting_threat_to`). A watching, adjacent, non-attacking hostile adds nothing, so row 83's fix (a starving subject eats) is not undone."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.scorers import CombatRetreatScorer
from src.core.movement_modes import MovementMode
from src.core.state import TaskComponent
from src.engine.need_pull import ESCALATION_AMPLITUDE, ESCALATION_FULL, ESCALATION_ONSET, retreat_pull, smoothstep
from tests.helpers.scenario import compile_world

MERCHANT, HUNTER = 37, 45
MAX_HP = 85


def _scene(hp, acting, hunger=100.0, with_hunter=True):
    """Real frontier_living_world seed-42 merchant 37 beside predator_hunter 45 (adjacent); the hunter attacks the merchant when `acting`, else has no task."""
    state = compile_world("frontier_living_world", 42)
    m, h = state.entities[MERCHANT], state.entities[HUNTER]
    m = replace(m, navigation=replace(m.navigation, position=(41.0, 31.0), movement_mode=MovementMode.REGROUP), combat=replace(m.combat, hp=hp, max_hp=MAX_HP),
                biological=replace(m.biological, hunger=hunger, sleep_debt=0.0))
    m = replace(m, identity=replace(m.identity, personality=replace(m.identity.personality, bravery=0.0)))
    h = replace(h, navigation=replace(h.navigation, position=(41.0, 30.0)))
    if acting:
        h = replace(h, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": MERCHANT}))
    object.__setattr__(state, "entities", {MERCHANT: m, HUNTER: h} if with_hunter else {MERCHANT: m})
    return state, m


def _retreat(hp, acting, **kw):
    state, m = _scene(hp, acting, **kw)
    return CombatRetreatScorer().score(m, state).utility


def test_an_acting_hostile_at_the_bottom_of_the_wound_scale_outbids_the_starving_pull():
    from src.engine.need_pull import hunger_pull
    from src.engine.starvation import STARVING_LINE

    starving_pull = hunger_pull(100.0, 100.0, 0.0, 0.0)
    assert STARVING_LINE == 95.0 and starving_pull == 160.0
    assert _retreat(hp=10, acting=True) > starving_pull  # hp 10 of 85 (11.8%): past the full edge, so the whole amplitude is added


def test_the_same_scene_with_a_hostile_that_does_not_act_stays_under_the_old_ceiling():
    assert _retreat(hp=10, acting=False) <= 150.0  # the row 83 pin's scene: an adjacent hunter with no task adds no escalation


def test_the_escalation_is_exactly_the_need_pull_term_of_the_damage_fraction():
    for hp in (10, 20, 30, 40):
        gap = _retreat(hp, acting=True) - _retreat(hp, acting=False)
        assert gap == pytest.approx(ESCALATION_AMPLITUDE * smoothstep(ESCALATION_ONSET, ESCALATION_FULL, 1.0 - hp / MAX_HP))


def test_no_escalation_while_the_wound_is_below_its_onset():
    hp = 60  # damage fraction 0.29 (< 0.6): the subject still flees by the raw score if panicking, but the wound adds nothing
    state, m = _scene(hp, acting=True)
    assert CombatRetreatScorer().score(m, state).utility == _retreat(hp, acting=False)


def test_the_escalation_grows_with_the_wound_between_its_onset_and_its_full_edge():
    onset_hp, full_hp = MAX_HP * (1 - ESCALATION_ONSET), MAX_HP * (1 - ESCALATION_FULL)
    values = [_retreat(hp, acting=True) - _retreat(hp, acting=False) for hp in (onset_hp + 1, 0.5 * (onset_hp + full_hp), full_hp - 1)]
    assert values == sorted(values) and values[0] < values[-1]


def test_with_no_hostile_in_view_nothing_is_added():
    hp = 10
    assert _retreat(hp, acting=True, with_hunter=False) == _retreat(hp, acting=False, with_hunter=False)


def test_retreat_pull_is_the_raw_utility_plus_the_amplitude_at_death():
    assert retreat_pull(120.0, 0.0) == pytest.approx(120.0 + ESCALATION_AMPLITUDE)
    assert retreat_pull(120.0, 1.0) == 120.0
