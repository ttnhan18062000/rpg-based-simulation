"""The brain is woken as a chosen rest ends below the sleep floor, so the fatigue project closes (part of 2.153 / STRAT-293; designer ruling 2026-10-30).

A chosen SLEEP/REST now ends strictly below REST_MIN_SLEEP_DEBT (20), but the rest holds no brain, and the strategic pass that completes the project ran only on its
cadence (every 10 ticks, staggered by entity id). The awake debt climbs 0.05 a tick, so by the next cadence tick it was back at the floor, `rest_in_place_update` fired
again and the hover only moved from 59 to 20. The scheduler now wakes a subject that is idle with an ACTIVE fatigue project as current and debt below the floor, and the
strategic pass evaluates it on that tick. Run through a real Kernel across every brain-cadence offset (entity id 1 to 10). Nothing else is woken; no new constant.
"""
from dataclasses import replace

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState, RegionState, TaskComponent
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.kernel import Kernel
from src.engine.sleep_debt import REST_MIN_SLEEP_DEBT, rest_ended_at_the_floor
from src.platform.rng import DeterministicRNG

INN_ID = 20003


def _profile():
    return RuntimeProfile(name="floor_wake", hardware_class=HardwareClass.CLASS_C, max_ram_mb=512, max_cpu_percent=50, max_worker_count=0,
                          max_queue_depth=100, max_replay_buffer_kb=1024, max_observability_budget_percent=5, max_tick_budget_ms=100.0,
                          sampling_interval_ticks=1)


def _run(eid, action, debt, at_inn=False, ticks=40):
    hero = (V2EntityBuilder(eid).kind("hero").location(5.0, 5.0).identity(faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    payload = {"action": action, "reason": "REST_IN_PLACE" if action == "REST" else "AT_BED"}
    hero = replace(hero, biological=replace(hero.biological, sleep_debt=debt), task=TaskComponent(work_kind="ENTITY_ACT", payload=payload))
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target=str(INN_ID) if at_inn else "", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="p1", kind=GoalKind.FATIGUE, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id="o1")
    hero = replace(hero, strategic=replace(hero.strategic, projects={"p1": project}, current_project_id="p1", current_objective_id="o1"))
    region = RegionState(id="r1", name="R", kind="FOREST", bounds=(0, 0, 100, 100), hazard_level=0.0)
    buildings = {INN_ID: BuildingState(id=INN_ID, kind="inn", position=(6.0, 5.0), functional=True)} if at_inn else {}
    state = AuthoritativeState(tick=1, seed=1, entities={eid: hero}, regions={"r1": region}, buildings=buildings, next_entity_id=eid + 1, next_node_id=1000,
                               terrain={(x, y): "plain" for x in range(10) for y in range(10)})
    kernel = Kernel(_profile(), state, DeterministicRNG(1))
    history = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            e = kernel._state.entities[eid]
            history.append((kernel._state.tick, e.biological.sleep_debt, dict(e.task.payload), e.strategic.projects["p1"].status))
    finally:
        kernel.shutdown()
    return history


def _check(history):
    end = next(i for i, (_, debt, payload, _) in enumerate(history) if not payload)          # the tick the held rest ended (task cleared)
    end_tick, end_debt = history[end][0], history[end][1]
    assert end_debt < REST_MIN_SLEEP_DEBT                                                       # ended strictly below the floor
    done = next(i for i, h in enumerate(history) if h[3] == ProjectStatus.COMPLETED)
    assert history[done][0] - end_tick <= 1, "the project closes on the tick after the rest ends, before the debt accrues back"
    assert history[done][1] < REST_MIN_SLEEP_DEBT
    window = [h for h in history[end:] if h[0] - end_tick <= 10]      # the designer's counter: no rest dispatch within 10 ticks of a floor-end
    assert window and all(not p for _, _, p, _ in window), "no rest dispatched after the floor-end (no rest_in_place hover at the floor)"
    assert all(p.get("reason") != "REST_IN_PLACE" for _, _, p, _ in history[end:])


@pytest.mark.parametrize("eid", range(1, 11))   # brain-cadence offsets 0 to 9 (stagger by entity id)
def test_a_rest_in_place_ending_at_the_floor_closes_the_project_at_every_cadence_offset(eid):
    _check(_run(eid, "REST", REST_MIN_SLEEP_DEBT + 0.5))


@pytest.mark.parametrize("eid", (1, 4, 10))
def test_an_inn_bed_sleep_ending_at_the_floor_closes_the_project_too(eid):
    _check(_run(eid, "SLEEP", REST_MIN_SLEEP_DEBT + 0.5, at_inn=True))


def test_only_the_state_a_chosen_rest_leaves_wakes_the_brain():
    hero = (V2EntityBuilder(1).kind("hero").location(1.0, 1.0).combat(hp=100, max_hp=100, alive=True).lifecycle(active=True).build())
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target="", status=ObjectiveStatus.ACTIVE)
    fatigue = ProjectState(id="p1", kind=GoalKind.FATIGUE, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id="o1")
    base = replace(hero, strategic=replace(hero.strategic, projects={"p1": fatigue}, current_project_id="p1"),
                   biological=replace(hero.biological, sleep_debt=19.9))
    assert rest_ended_at_the_floor(base)
    assert not rest_ended_at_the_floor(replace(base, biological=replace(base.biological, sleep_debt=20.0)))                     # not below the floor
    assert not rest_ended_at_the_floor(replace(base, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "REST"})))   # still holding a rest
    assert not rest_ended_at_the_floor(replace(base, strategic=replace(base.strategic, current_project_id="")))                  # no current project
    other = replace(fatigue, kind=GoalKind.HUNGER)
    assert not rest_ended_at_the_floor(replace(base, strategic=replace(base.strategic, projects={"p1": other})))                 # not a fatigue project
    done = replace(fatigue, status=ProjectStatus.COMPLETED)
    assert not rest_ended_at_the_floor(replace(base, strategic=replace(base.strategic, projects={"p1": done})))                  # already closed
