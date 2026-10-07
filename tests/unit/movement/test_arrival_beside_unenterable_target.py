"""TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED.

A walk to a building targets the building's own tile, which cannot be entered. Beside it the step onto the tile is rejected
(PATH_NOT_FOUND for a blocked tile, BUILDING_OBSTRUCTION for a building tile), the sidestep ladder moved the entity
perpendicular, and the planner moved it back: it jittered between distance 1 and 2 and never stayed where the tactical pass
dispatches the building's service (`dist <= 1.0`). An orthogonally adjacent entity whose step onto the unenterable DESTINATION
tile is rejected has now arrived.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.movement import MovementSystem
from src.engine.tactical import TacticalDecisionSystem

INN = (40, 31)


def _walker(pos, entity_id=1):
    return (V2EntityBuilder(entity_id).kind("HERO").location(float(pos[0]), float(pos[1]))
            .identity(faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, atk=10, def_stat=5, alive=True, readiness=100.0)
            .navigation(movement_mode=MovementMode.WANDER, target=(float(INN[0]), float(INN[1])))
            .lifecycle(active=True).build())


def _state(entities, blocked=(INN,), building_tiles=None):
    inn = BuildingState(id=20003, kind="inn", position=(float(INN[0]), float(INN[1])), functional=True)
    return AuthoritativeState(
        tick=1, seed=1, entities={e.id: e for e in entities}, buildings={20003: inn},
        blocked_tiles=set(blocked), building_tiles=dict(building_tiles or {}), terrain={},
    )


def _move(state, entity):
    return MovementSystem.resolve_move(state, entity, (float(INN[0]), float(INN[1])), MovementMode.WANDER)[entity.id]


def test_an_entity_orthogonally_beside_a_blocked_destination_tile_has_arrived():
    walker = _walker((39, 31))
    update = _move(_state([walker]), walker)
    assert update.navigation is not None and update.navigation.target_clear
    assert update.new_position is None


def test_an_entity_beside_a_building_footprint_tile_has_arrived_too():
    walker = _walker((39, 31))
    update = _move(_state([walker], blocked=(), building_tiles={INN: "inn"}), walker)
    assert update.navigation is not None and update.navigation.target_clear
    assert update.new_position is None


def test_arrival_does_not_touch_the_wait_and_failure_counters():
    walker = _walker((39, 31))
    update = _move(_state([walker]), walker)
    assert update.navigation.failure_reason is None
    assert update.navigation.wait_count_delta == 0


def test_a_diagonal_neighbour_has_not_arrived_it_keeps_walking():
    walker = _walker((39, 32))
    update = _move(_state([walker]), walker)
    assert not (update.navigation and update.navigation.target_clear)
    assert update.new_position is not None


def test_an_obstacle_on_the_way_is_not_an_arrival():
    walker = _walker((36, 31))
    state = _state([walker], blocked=(INN, (37, 31)))
    update = _move(state, walker)
    assert not (update.navigation and update.navigation.target_clear)


def test_another_entity_standing_on_the_destination_is_not_an_arrival():
    walker = _walker((39, 31))
    blocker = _walker(INN, entity_id=2)
    update = _move(_state([walker, blocker], blocked=()), walker)
    assert not (update.navigation and update.navigation.target_clear)


def _fatigue_walker(pos):
    walker = _walker(pos)
    objective = ObjectiveState(id="fatigue_20003", kind=ObjectiveKind.REACH_LOCATION, target="20003", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="proj_fatigue_1", kind="fatigue", status=ProjectStatus.ACTIVE, objectives=[objective],
                           active_objective_id=objective.id)
    strategic = replace(walker.strategic, projects={project.id: project}, current_project_id=project.id,
                        current_objective_id=objective.id)
    return replace(walker, strategic=strategic)


def test_a_walker_to_an_inn_settles_beside_it_and_rest_is_dispatched():
    """Walk the real movement ladder tick by tick: it must stop beside the inn and stay there, and the tactical pass then
    dispatches REST (the old ladder alternated between distance 1 and 2 forever)."""
    walker = _fatigue_walker((39, 28))
    positions = []
    for _ in range(30):
        state = _state([walker])
        update = _move(state, walker)
        if update.new_position is not None:
            walker = replace(walker, navigation=replace(walker.navigation, position=update.new_position,
                                                        last_position=walker.navigation.position))
        if update.navigation is not None and update.navigation.target_clear:
            walker = replace(walker, navigation=replace(walker.navigation, target=None))
        positions.append(tuple(int(v) for v in walker.navigation.position))

    assert positions[-10:] == [positions[-1]] * 10, f"still moving at the end: {positions[-10:]}"
    assert abs(positions[-1][0] - INN[0]) + abs(positions[-1][1] - INN[1]) == 1
    decision = TacticalDecisionSystem.evaluate_entity_intent(_state([walker]), walker)
    assert decision.task is not None and (decision.task.payload_set or {}).get("action") == "REST"
