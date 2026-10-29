"""TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO (designer ruling 2026-10-29): the earn step is taken only if its shift can
finish before the starvation line, the pull escalates over the whole step, the arrival action is derived from what the building can do for the subject, and
a held shift is woken by a present threat to life only (the wage is forfeited), never by hunger."""
from __future__ import annotations

from dataclasses import replace

import pytest

import src.core.registries  # noqa: F401
from src.ai.goals.base import OpeningStepKind
from src.ai.goals.opening_steps import opening_steps, work_in_reach
from src.ai.goals.scorers import EatScorer
from src.ai.goals.ways import WayKind, ways_in_reach
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent
from src.core.strategic import ObjectiveState, ProjectState
from src.engine import service_admission
from src.engine.biological_needs import need_rates
from src.engine.building_arrival import building_arrival_update
from src.engine.need_pull import hunger_pull
from src.engine.scheduler import DeterministicScheduler
from src.engine.service_admission import PaymentLaw
from src.engine.starvation import STARVING_LINE
from src.engine.work_shift import SHIFT_START, SHIFT_TICKS, shift_takeable


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _worker(hunger=40.0, gold=0, pos=(10.0, 10.0)):
    e = V2EntityBuilder(1).kind("worker").properties({"species_id": "human", "faction_id": "town_council"}).location(*pos).inventory(gold=gold).build()
    return replace(e, biological=replace(e.biological, hunger=hunger))


def _hall(pos=(20.0, 10.0), bid=10):
    """A workplace that serves no meal and pays a shift from its own purse (a smithy that hires)."""
    return BuildingState(id=bid, kind="blacksmith", position=pos, functional=True, hires_for_pay=True, inventory=InventoryComponent(gold=100))


def _inn(pos=(30.0, 10.0), bid=11, hires=False, gold=100):
    return BuildingState(id=bid, kind="inn", position=pos, functional=True, hires_for_pay=hires, inventory=InventoryComponent(gold=gold))


def _state(entity, *buildings, tick=500):
    return AuthoritativeState(tick=tick, seed=1, world_time=1000, entities={entity.id: entity}, buildings={b.id: b for b in buildings})


def test_a_shift_is_takeable_only_when_the_meal_is_reached_before_the_starvation_line():
    """Strictly under the line at arrival at the meal: need + rate x (walk to the work + SHIFT_TICKS + walk on to the meal)."""
    walk, onward = 10.0, 20.0
    ent = _worker()
    work_pos = (ent.navigation.position[0] + walk, ent.navigation.position[1])
    state = _state(ent, _inn((work_pos[0] + onward, work_pos[1])))
    limit = STARVING_LINE - need_rates(ent)[0] * (walk + SHIFT_TICKS + onward)
    below = replace(ent, biological=replace(ent.biological, hunger=limit - 0.5))
    at = replace(ent, biological=replace(ent.biological, hunger=limit))
    assert shift_takeable(below, state, work_pos)
    assert not shift_takeable(at, state, work_pos)


def test_hunger_that_clears_the_line_at_the_end_of_the_shift_but_crosses_it_on_the_walk_to_the_meal_is_not_takeable():
    walk, onward = 10.0, 40.0
    ent = _worker()
    rate = need_rates(ent)[0]
    work_pos = (ent.navigation.position[0] + walk, ent.navigation.position[1])
    hunger = STARVING_LINE - rate * (walk + SHIFT_TICKS) - 0.5  # under the line when the shift ends
    ent = replace(ent, biological=replace(ent.biological, hunger=hunger))
    assert hunger + rate * (walk + SHIFT_TICKS) < STARVING_LINE <= hunger + rate * (walk + SHIFT_TICKS + onward)
    far_meal = _state(ent, _inn((work_pos[0] + onward, work_pos[1])))
    near_meal = _state(ent, _inn((work_pos[0] + 1.0, work_pos[1])))
    assert not shift_takeable(ent, far_meal, work_pos)
    assert shift_takeable(ent, near_meal, work_pos)


def test_a_far_building_is_takeable_later_than_a_near_one_in_the_same_hunger():
    ent = _worker(hunger=80.0)
    near, far = (11.0, 10.0), (200.0, 10.0)
    assert shift_takeable(ent, _state(ent, _inn((12.0, 10.0))), near) and not shift_takeable(ent, _state(ent, _inn((201.0, 10.0))), far)


def test_a_shift_that_cannot_finish_is_not_an_open_step_not_a_way_and_not_in_reach():
    late = _worker(hunger=94.0)  # 94 + 0.05 x 200 is past the line
    state = _state(late, _hall())
    assert work_in_reach(late, state) is None
    assert WayKind.WORK_SHIFT not in ways_in_reach(late, state)
    step = next(s for s in opening_steps(late, state) if s.kind is OpeningStepKind.EARN_THEN_BUY)
    assert not step.available
    early = _worker(hunger=40.0)
    assert work_in_reach(early, _state(early, _hall())) is not None
    assert WayKind.WORK_SHIFT in ways_in_reach(early, _state(early, _hall()))


def test_the_pull_of_the_earn_step_escalates_over_the_whole_step(monkeypatch):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", PaymentLaw.ATOMIC)
    ent = _worker(hunger=60.0, pos=(10.0, 10.0))
    state = _state(ent, _hall((20.0, 10.0)), _inn((30.0, 10.0)))
    score = EatScorer().score(ent, state)
    assert score.opening_step is OpeningStepKind.EARN_THEN_BUY and score.target_id == "10"
    rate = need_rates(ent)[0]
    walk_only = hunger_pull(60.0, 60.0, rate, 10.0)
    whole_step = hunger_pull(60.0, 60.0, rate, 10.0 + SHIFT_TICKS + 10.0)  # to the hall, the shift, on to the inn
    assert score.utility == pytest.approx(whole_step) and whole_step > walk_only


def _project(kind="hunger"):
    return ProjectState(id="p1", kind=kind, objectives=[ObjectiveState(id="o1", kind="reach")], active_objective_id="o1")


def _arrive(entity, building, state, kind="hunger"):
    return building_arrival_update(state, entity, _project(kind), building.id)


def _action(update):
    return update.task.payload_set.get("action") if update.task is not None and update.task.payload_set else None


@pytest.mark.parametrize("law,gold,expected", [
    (PaymentLaw.CLAMP, 0, "EAT"),       # main: a broke subject at an inn that also hires is fed
    (PaymentLaw.ATOMIC, 0, "WORK"),     # the removal: it cannot pay, so it works
    (PaymentLaw.ATOMIC, 5, "EAT"),      # having earned, it eats
])
def test_an_inn_that_also_hires_gives_the_meal_or_the_shift_by_what_the_law_admits(monkeypatch, law, gold, expected):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", law)
    inn = _inn((10.0, 11.0), hires=True)
    ent = _worker(hunger=50.0, gold=gold)
    update = _arrive(ent, inn, _state(ent, inn))
    assert _action(update) == expected
    if expected == "WORK":
        assert update.task.payload_set[SHIFT_START] == 500 and update.task.payload_set["target_id"] == inn.id


def test_a_town_hall_with_work_and_no_meal_gives_the_shift_on_either_law(monkeypatch):
    for law in PaymentLaw:
        monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", law)
        hall = _hall((10.0, 11.0))
        ent = _worker(hunger=50.0)
        assert _action(_arrive(ent, hall, _state(ent, hall))) == "WORK"


def test_a_building_with_no_meal_and_no_takeable_shift_ends_the_project_by_the_existing_path(monkeypatch):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", PaymentLaw.ATOMIC)
    hall = _hall((10.0, 11.0))
    ent = _worker(hunger=94.0)
    update = _arrive(ent, hall, _state(ent, hall))
    assert _action(update) is None and update.strategic is not None and update.strategic.current_project_id_set == ""


def test_other_arrival_purposes_are_unchanged(monkeypatch):
    inn = _inn((10.0, 11.0))
    ent = _worker(hunger=50.0, gold=20)
    state = _state(ent, inn)
    assert _action(_arrive(ent, inn, state, kind="fatigue")) == "REST"
    assert _action(_arrive(ent, inn, state)) == "EAT"
    shop = BuildingState(id=12, kind="shop", position=(10.0, 11.0), functional=True)
    carrying = replace(ent, inventory=replace(ent.inventory, items=list(ent.inventory.items)))
    assert _action(_arrive(carrying, shop, _state(carrying, shop))) in (None, "SELL")  # a shop visit is the SELL step or its end, never a meal or a shift


def _holder(action, hunger=96.0):
    ent = _worker(hunger=hunger)
    return replace(ent, task=replace(ent.task, work_kind="ENTITY_ACT", payload={"action": action, "target_id": 10, SHIFT_START: 1}))


def _wolf_beside(ent, eid=2):
    pos = (ent.navigation.position[0] + 1.0, ent.navigation.position[1])
    return (V2EntityBuilder(eid).kind("monster").location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, properties={"species_id": "goblin"})
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build())


def test_hunger_does_not_wake_a_held_shift():
    ent = _holder("WORK", hunger=94.0)
    state = _state(ent, _hall())
    assert DeterministicScheduler._is_need_woken(ent, state, "ENTITY_ACT") is False


def test_a_present_threat_wakes_a_held_shift_and_only_a_held_shift():
    work = _holder("WORK", hunger=50.0)
    wolf = _wolf_beside(work)
    state = replace(_state(work, _hall()), entities={work.id: work, wolf.id: wolf})
    assert DeterministicScheduler._is_need_woken(work, state, "ENTITY_ACT") is True  # the brain re-decides; the shift ends and its wage is forfeited
    rest = _holder("EAT", hunger=50.0)
    state2 = replace(state, entities={rest.id: rest, wolf.id: wolf})
    assert DeterministicScheduler._is_need_woken(rest, state2, "ENTITY_ACT") is False  # any other held action is not interrupted


def _with_wolf(state, ent):
    foe = _wolf_beside(ent)
    return replace(state, entities={**state.entities, foe.id: foe})


def test_a_shift_is_not_takeable_while_a_present_threat_holds_and_is_once_it_is_gone():
    """One definition for the start and the wake: a shift is never started that the next tick would interrupt (the frontier s46 guard-9 loop)."""
    inn = _inn((10.0, 11.0), hires=True)
    ent = _worker(hunger=80.0)
    calm = _state(ent, inn)
    assert shift_takeable(ent, calm, inn.position)
    threatened = _with_wolf(calm, ent)
    assert not shift_takeable(ent, threatened, inn.position)
    assert DeterministicScheduler._is_need_woken(replace(ent, task=replace(ent.task, work_kind="ENTITY_ACT", payload={"action": "WORK", SHIFT_START: 1})),
                                                 threatened, "ENTITY_ACT") is True  # the wake and the start read the same test


def test_a_threat_at_the_hiring_inn_gives_no_work_and_does_not_end_the_hunger_project(monkeypatch):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", PaymentLaw.ATOMIC)
    inn = _inn((10.0, 11.0), hires=True)
    ent = _worker(hunger=80.0)
    threatened = _with_wolf(_state(ent, inn), ent)
    update = _arrive(ent, inn, threatened)
    assert _action(update) is None and update.task is None, "no WORK start under a present threat"
    assert update.strategic is None, "the hunger project is not ended, completed or abandoned: it stays current for the next decision"
    calm = _state(ent, inn)
    again = _arrive(ent, inn, calm)
    assert _action(again) == "WORK" and again.strategic is None, "threat gone: the shift starts on the same project (no new project is made)"


def test_a_shift_that_cannot_finish_before_the_line_still_ends_the_project_by_the_existing_path(monkeypatch):
    """The line case keeps what it does today: the project is completed (its objective resolved) and the current project is cleared."""
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", PaymentLaw.ATOMIC)
    inn = _inn((10.0, 11.0), hires=True)
    ent = _worker(hunger=94.0)
    update = _arrive(ent, inn, _state(ent, inn))
    assert _action(update) is None and update.strategic is not None and update.strategic.current_project_id_set == ""
