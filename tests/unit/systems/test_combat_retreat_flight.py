"""A brain decision that chooses COMBAT_RETREAT is a decision to leave an engagement (CONFLICT-04, divergence 2.139): it issues a decided flight (FlightReason.COMBAT_RETREAT)
that steps beside an engaged hostile; a target the strategic pass writes again between decisions is still a stored target and takes no step. Pure tests of
`combat_retreat_flight_update` (the rules) and the movement selector's reading of the reason."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import FlightReason
from src.core.state import TaskComponent
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.core.updates import EntityUpdate, NavigationUpdate, StrategicUpdate, TaskUpdate
from src.engine.cadence import SystemCadence, should_run
from src.engine.candidate_selector import ARRIVAL_ENDS_MOVE_REASONS, MovementCandidateSelector
from src.systems.strategic_systems.combat_retreat_flight import combat_retreat_flight_update

TOWN = (25.0, 25.0)
RETREAT = FlightReason.COMBAT_RETREAT.value


def _project(kind=GoalKind.COMBAT_RETREAT, pid="proj_combat_retreat_1"):
    obj = ObjectiveState(id=f"{kind.value}_town_center", kind=ObjectiveKind.REACH_LOCATION, target="town_center", target_position=TOWN, status=ObjectiveStatus.ACTIVE)
    return ProjectState(id=pid, kind=kind, status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id)


def _entity(task=None, projects=()):
    e = V2EntityBuilder(1).kind("HERO").location(28.0, 32.0).combat(hp=10, max_hp=100, atk=5, def_stat=5, alive=True, readiness=100.0).lifecycle(active=True).build()
    e = replace(e, strategic=replace(e.strategic, projects={p.id: p for p in projects}, current_project_id=projects[0].id if projects else None))
    return replace(e, task=task) if task is not None else e


def _held(reason):
    return TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (10.0, 10.0), "reason": reason})


def _issue(entity, ent_upd=None, project_id=None, brain_ran=True):
    return combat_retreat_flight_update(entity, ent_upd or EntityUpdate(entity_id=1), None, project_id or entity.strategic.current_project_id, brain_ran)


def test_a_brain_decision_for_combat_retreat_issues_the_decided_flight_once():
    entity = _entity(projects=[_project()])
    out = _issue(entity)
    assert out.task == TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": TOWN, "reason": RETREAT})
    assert out.navigation.target_set == TOWN


def test_a_tick_the_brain_did_not_evaluate_issues_nothing_even_for_a_current_retreat_project():
    entity = _entity(projects=[_project()])
    assert _issue(entity, brain_ran=False) == EntityUpdate(entity_id=1)


def test_a_live_combat_retreat_move_is_kept_not_restarted():
    entity = _entity(task=_held(RETREAT), projects=[_project()])
    assert _issue(entity) == EntityUpdate(entity_id=1)


def test_the_brains_own_idle_reset_is_replaced_by_the_flight():
    entity = _entity(projects=[_project()])
    reset = EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}))
    assert _issue(entity, reset).task.work_kind_set == "ENTITY_MOVE"


def test_a_same_tick_tactical_attack_beats_the_flight():
    entity = _entity(projects=[_project()])
    attack = EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 16}))
    assert _issue(entity, attack) == attack


def test_a_bare_seed_for_another_project_issues_no_move():
    entity = _entity(projects=[_project(GoalKind.RESOLVE_BLOCKER, "proj_resolve_blocker_1")])
    assert _issue(entity).task is None


def test_a_live_panic_retreat_is_kept_when_the_brain_chooses_combat_retreat():
    entity = _entity(task=_held("PANIC_RETREAT"), projects=[_project()])
    assert _issue(entity) == EntityUpdate(entity_id=1)


def test_a_live_panic_retreat_is_kept_when_the_brain_chooses_something_else():
    entity = _entity(task=_held("PANIC_RETREAT"), projects=[_project(GoalKind.RESOLVE_BLOCKER, "proj_resolve_blocker_1")])
    assert _issue(entity) == EntityUpdate(entity_id=1)


def test_after_the_panic_retreat_ends_the_next_brain_decision_issues_the_flight():
    entity = _entity(projects=[_project()])  # the tactical flight is over: the idle task
    assert _issue(entity).task.payload_set["reason"] == RETREAT


def test_a_held_combat_retreat_move_does_not_suppress_the_brain_another_choice_ends_it_within_one_cadence():
    entity = _entity(task=_held(RETREAT), projects=[_project(GoalKind.RESOLVE_BLOCKER, "proj_resolve_blocker_1")])
    cadence = SystemCadence().strategic_intelligence
    ended = [t for t in range(cadence) if _issue(entity, brain_ran=should_run(t, entity.id, cadence)) != EntityUpdate(entity_id=1)]
    assert ended, "no brain tick inside one strategic cadence ended the held flight"
    out = _issue(entity)
    assert out.task == TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}) and out.navigation.target_clear is True
    assert _issue(entity, brain_ran=False) == EntityUpdate(entity_id=1)  # between decisions the held flight runs on


def test_a_held_combat_retreat_move_ends_only_for_its_own_reason():
    entity = _entity(task=_held("PANIC_RETREAT"), projects=[_project(GoalKind.RESOLVE_BLOCKER, "proj_resolve_blocker_1")])
    assert _issue(entity) == EntityUpdate(entity_id=1)


def test_the_selector_reads_combat_retreat_as_a_decided_flight_that_ends_on_arrival():
    entity = _entity(task=_held(RETREAT))
    assert MovementCandidateSelector.is_decided_flight(entity)
    assert RETREAT in ARRIVAL_ENDS_MOVE_REASONS
    arrived = replace(entity, navigation=replace(entity.navigation, position=(10.0, 11.0)))
    assert MovementCandidateSelector.arrived_in_area(arrived)
