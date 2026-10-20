"""
src/ai/goals/safe_route.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED (SURV-07 amendment, owner decision memo row 84)

The hunger pull aims at the nearest open way whose route is not threatened, and holds its choice until reached or threatened.

A hunger project's active objective is threatened when a hostile the subject would flee from (the tactical pass's own perceived-hostile
predicate: `perceived_hostiles`, which is `are_entities_hostile` over what the subject perceives within the target-perception radius, never
the true map) lies within its own attack reach plus one step of the straight line to it. Then the project is RETARGETED, not replaced: its single objective becomes the nearest open
way (the kind's diet and the service rules, the same ways the pull already uses) whose route is not threatened.

The commitment needs no stored state. Only the CURRENT objective is ever tested, so a re-chosen objective stays until it is reached or is
itself threatened, and an old way that stops looking threatened (because its threat left view) is never tried again. When every open way is
threatened the objective is left as it is (today's behaviour: the nearest). No counter, no timer.

Pure reads of the state; the caller applies the returned project through the ordinary `StrategicUpdate`.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple

from src.ai.goals.opening_steps import opening_steps
from src.ai.goals.scorers_support import perceived_hostiles
from src.ai.goals.ways import inn_in_reach
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState
from src.engine.appraisal import can_use_inn_meal

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

Position = Tuple[float, float]

#: One step of the walk, in tiles: a subject moves one whole tile per tick (MOV-07), and no named per-tick move constant exists to read.
MOVE_STEP_TILES = 1


@dataclass(frozen=True)
class OpenWay:
    """One open way to a meal and where it points (what a hunger objective needs)."""
    target_id: str
    target_pos: Position
    target_entity_id: Optional[int] = None


def _route_points(start: Position, end: Position) -> List[Position]:
    """The tiles of the straight walk from `start` to `end`, both ends included (one point per tile of the longer axis)."""
    steps = int(max(abs(end[0] - start[0]), abs(end[1] - start[1])))
    if steps == 0:
        return [start]
    return [(start[0] + (end[0] - start[0]) * i / steps, start[1] + (end[1] - start[1]) * i / steps) for i in range(steps + 1)]


def route_is_threatened(start: Position, end: Position, hostiles: Sequence["EntityState"]) -> bool:
    """True when a hostile could strike the subject on the way: it stands within its OWN attack reach (`combat.range`) plus one step of the straight
    line from `start` to `end`. A melee hostile (reach 1) therefore counts at 2 tiles, a ranged one wider. A route bent around an obstacle is judged by
    its chord, and only hostiles the subject perceives are passed in."""
    if not hostiles:
        return False
    points = _route_points(start, end)
    for hostile in hostiles:
        hx, hy = hostile.navigation.position
        reach = hostile.combat.range + MOVE_STEP_TILES
        if any(max(abs(px - hx), abs(py - hy)) <= reach for px, py in points):
            return True
    return False


def open_ways(entity: "EntityState", state: "AuthoritativeState") -> List[OpenWay]:
    """Every open way the hunger pull can aim at: the inn in reach (when the diet has an inn meal) and each opening step that is open now."""
    ways: List[OpenWay] = []
    inn = inn_in_reach(entity, state)
    if inn is not None and can_use_inn_meal(entity):
        ways.append(OpenWay(str(inn.id), (inn.position[0], inn.position[1])))
    for step in opening_steps(entity, state):
        if step.available and step.target_pos is not None and step.target_id is not None:
            ways.append(OpenWay(step.target_id, (step.target_pos[0], step.target_pos[1]), step.target_entity_id))
    return ways


def _walk(entity: "EntityState", pos: Position) -> float:
    return abs(entity.navigation.position[0] - pos[0]) + abs(entity.navigation.position[1] - pos[1])


def retarget_if_threatened(entity: "EntityState", state: "AuthoritativeState", project: ProjectState) -> Optional[ProjectState]:
    """The hunger project retargeted at the nearest open way whose route is not threatened, or None to leave it as it is.

    None when the objective's route is not threatened (never re-chosen), when no hostile is perceived, or when every open way is threatened
    (the objective stays: today's behaviour)."""
    objective = next((o for o in project.objectives if o.id == project.active_objective_id), None)
    if objective is None or objective.status != ObjectiveStatus.ACTIVE or objective.target_position is None:
        return None
    hostiles = perceived_hostiles(entity, state)
    here = entity.navigation.position
    if not hostiles or not route_is_threatened(here, objective.target_position, hostiles):
        return None
    for way in sorted(open_ways(entity, state), key=lambda w: _walk(entity, w.target_pos)):  # sorted() is stable: ties keep the pull's own order
        if not route_is_threatened(here, way.target_pos, hostiles):
            new_objective = ObjectiveState(
                id=f"hunger_{way.target_id}", kind=ObjectiveKind.REACH_LOCATION, target=way.target_id, target_position=way.target_pos,
                target_entity_id=way.target_entity_id, status=ObjectiveStatus.ACTIVE,
            )
            return replace(project, objectives=[new_objective], active_objective_id=new_objective.id)
    return None
