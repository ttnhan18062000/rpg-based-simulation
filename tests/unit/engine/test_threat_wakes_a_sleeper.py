"""A present threat wakes a sleeper (2.154 / STRAT-294, Enforced; designer ruling 2026-10-30, N14).

A held SLEEP or REST ran no brain, and only hunger woke it (2.115). F1 (2.153) makes a chosen rest last to the sleep floor, so a sleeper now stays down for
hundreds of ticks and must wake to a threat. Decision 32's condition (an unengaged hostile orthogonally adjacent) or a perceived hostile ACTING on it
(`acting_threat_to`: an attack or pursuit aimed at it, or a hit on it within the need-wake cadence, so a shooter at range counts) wakes it, collapse
included, on decision 32's cadence. The wake is a re-decision only. No new constant.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.policy import GovernorPolicy
from src.engine.scheduler import ADJACENCY_WAKE_COOLDOWN, NEED_WAKE_CADENCE, DeterministicScheduler
from src.engine.sleep_debt import COLLAPSE_FLAG, COLLAPSE_LINE
from src.engine.tactical import TacticalDecisionSystem

SLEEPER_ID = 2   # even id: (tick + 2) % 2 == 0 on even ticks


def _sleeper(action="REST", debt=70.0, collapse=False):
    e = (V2EntityBuilder(SLEEPER_ID).kind("hero").location(10.0, 10.0).identity(faction=Faction.HERO_GUILD)
         .combat(hp=100, max_hp=100, readiness=100.0, alive=True).lifecycle(active=True).biological(hunger=0.0, sleep_debt=debt).build())
    payload = {"action": action, **({COLLAPSE_FLAG: True} if collapse else {})}
    return replace(e, task=TaskComponent(work_kind="ENTITY_ACT", payload=payload))


def _monster(pos, attacking=None, eid=7):
    m = (V2EntityBuilder(eid).kind("monster").location(float(pos[0]), float(pos[1])).identity(faction=Faction.MONSTER_HORDE)
         .combat(hp=100, max_hp=100, readiness=100.0, alive=True).lifecycle(active=True).build())
    if attacking is not None:
        m = replace(m, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": attacking}))
    return m


def _woken(entities, tick):
    state = AuthoritativeState(tick=tick, seed=1, entities={e.id: e for e in entities})
    items, _ = DeterministicScheduler().select_work(state, GovernorPolicy())
    return any(i.owner_id == SLEEPER_ID and i.work_kind == "ENTITY_BRAIN" for i in items)


def _wake_ticks(entities, ticks):
    return [t for t in ticks if _woken(entities, t)]


def test_the_cadence_never_lets_a_hit_fall_between_two_wake_checks():
    assert NEED_WAKE_CADENCE >= ADJACENCY_WAKE_COOLDOWN   # acting_threat_to's hit window covers at least one decision-32 check


def test_a_hostile_stepping_adjacent_wakes_a_chosen_sleeper_on_the_decision_32_cadence():
    for action in ("SLEEP", "REST"):
        beside = [_sleeper(action), _monster((11, 10))]
        ticks = _wake_ticks(beside, range(1, 11))
        assert ticks and all((t + SLEEPER_ID) % ADJACENCY_WAKE_COOLDOWN == 0 for t in ticks)
        assert len(ticks) == 5   # every second tick while the threat stands


def test_a_perceived_hostile_acting_on_it_from_range_wakes_it_too():
    shooter = [_sleeper(), _monster((13, 10), attacking=SLEEPER_ID)]   # 3 tiles away, the longest reach in the content
    assert _wake_ticks(shooter, range(1, 11))


def test_a_collapse_is_woken_and_its_decision_is_the_collapse_again_at_the_line():
    held = _sleeper("SLEEP", debt=COLLAPSE_LINE + 1.0, collapse=True)
    assert _wake_ticks([held, _monster((11, 10))], range(1, 5))
    state = AuthoritativeState(tick=2, seed=1, entities={held.id: held, 7: _monster((11, 10))})
    again = TacticalDecisionSystem.evaluate_entity_intent(state, held)
    assert again.task.payload_set["action"] == "SLEEP" and again.task.payload_set[COLLAPSE_FLAG]


def test_below_the_collapse_line_a_woken_sleeper_answers_the_threat_and_no_rest_is_reissued():
    held = _sleeper("REST", debt=70.0)
    state = AuthoritativeState(tick=2, seed=1, entities={held.id: held, 7: _monster((11, 10), attacking=SLEEPER_ID)})
    decision = TacticalDecisionSystem.evaluate_entity_intent(state, held)
    action = (decision.task.payload_set or {}).get("action") if decision is not None and decision.task is not None else None
    assert action is not None and action not in ("REST", "SLEEP")   # flee or fight; a REST here would put the sleeper straight back down


def test_with_no_threat_there_is_no_wake_a_far_or_passive_hostile_included():
    assert _wake_ticks([_sleeper()], range(1, 11)) == []
    assert _wake_ticks([_sleeper(), _monster((16, 10))], range(1, 11)) == []              # in view, not adjacent, not acting
    assert _wake_ticks([_sleeper(), _monster((13, 10))], range(1, 11)) == []              # 3 tiles, no act aimed at it


def test_a_hostile_acting_on_someone_else_does_not_wake_it():
    assert _wake_ticks([_sleeper(), _monster((13, 10), attacking=99)], range(1, 11)) == []


def test_a_non_sleeping_idle_holder_is_not_affected():
    awake = replace(_sleeper(), task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "HOLD"}))
    assert _wake_ticks([awake, _monster((13, 10), attacking=SLEEPER_ID)], range(1, 11)) == []   # only is_asleep holders gain the wake
