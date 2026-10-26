"""
src/systems/strategic_systems/combat_retreat_flight.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A), divergence 2.139, CONFLICT-04 (rpg-designer ruling, 2026-10-26).

A brain decision that chooses COMBAT_RETREAT is a decision to leave an engagement, so it executes as a decided flight: an `ENTITY_MOVE` task update with
`FlightReason.COMBAT_RETREAT`, which `MovementCandidateSelector` lets step beside an engaged hostile (it pays the opportunity attack). The target the strategic pass writes
again BETWEEN decisions is still a stored target and takes no step.

Rules (all read from this tick's update and the entity's own state; no new field):
- It is issued only on a tick the brain evaluated (`brain_ran`), and only when the current project is COMBAT_RETREAT with a positioned objective.
- A subject already holding a COMBAT_RETREAT move keeps it: the move is not restarted. A subject holding a decided flight of another reason (PANIC_RETREAT, ...) keeps
  that one (provisional, rpg-designer pending): the strategic flight is issued by the next brain decision if retreat still wins.
- A task decision an earlier phase issued this tick wins (a tactical ATTACK, a PANIC_RETREAT, anything with a payload); the brain's own reset to an idle `ENTITY_ACT`
  with no payload is not a decision and is replaced.
- A held COMBAT_RETREAT move does not suppress the brain: on a tick the brain evaluated, if the current project is no longer COMBAT_RETREAT the move ends
  (back to the idle task, no stored target) before the brain's new choice is carried out. It also ends on arrival (`ARRIVAL_ENDS_MOVE_REASONS`).
There is no timeout and no "hostile gone" end (a known gap, divergence 2.139).
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional, Tuple

from src.core.enums import DECIDED_FLIGHT_REASONS, FlightReason
from src.core.state import EntityState
from src.core.strategic import GoalKind, ObjectiveStatus, ProjectState, ProjectStatus
from src.core.updates import EntityUpdate, NavigationUpdate, StrategicUpdate, TaskUpdate


def _holds_combat_retreat(entity: EntityState) -> bool:
    """True when the subject's held task is a COMBAT_RETREAT flight."""
    return entity.task.work_kind == "ENTITY_MOVE" and entity.task.payload.get("reason") == FlightReason.COMBAT_RETREAT.value


def _holds_another_flight(entity: EntityState) -> bool:
    """True when the subject holds a decided flight of another reason (PANIC_RETREAT, SAFETY_PRESSURE_RETREAT, ...). PROVISIONAL (rpg-designer, pending): the strategic flight
    does not replace a tactical one; it finishes, and the next brain decision issues the strategic flight if retreat still wins. One isolated condition, easy to flip."""
    return entity.task.work_kind == "ENTITY_MOVE" and entity.task.payload.get("reason") in DECIDED_FLIGHT_REASONS and not _holds_combat_retreat(entity)


def _no_task_decision(ent_upd: EntityUpdate) -> bool:
    """True when no earlier phase issued a task decision this tick: no task update, or the brain's own idle reset (an `ENTITY_ACT` with no payload)."""
    task = ent_upd.task
    return task is None or task.is_noop() or (task.work_kind_set == "ENTITY_ACT" and not task.payload_set)


def _current_project(entity: EntityState, strat_up: Optional[StrategicUpdate], project_id: Optional[str]) -> Optional[ProjectState]:
    if not project_id:
        return None
    project = next((p for p in (strat_up.projects_add_or_update if strat_up else []) if p.id == project_id), None) or entity.strategic.projects.get(project_id)
    return project if project is not None and project.status == ProjectStatus.ACTIVE else None


def _target_position(project: ProjectState, strat_up: Optional[StrategicUpdate]) -> Optional[Tuple[float, float]]:
    obj_id = strat_up.current_objective_id_set if strat_up is not None and strat_up.current_objective_id_set is not None else project.active_objective_id
    obj = next((o for o in project.objectives if o.id == obj_id), None)
    if obj is None or obj.status != ObjectiveStatus.ACTIVE or getattr(obj, "target_entity_id", None) is not None:
        return None
    return getattr(obj, "target_position", None)


def combat_retreat_flight_update(
    entity: EntityState, ent_upd: Optional[EntityUpdate], strat_up: Optional[StrategicUpdate], current_project_id: Optional[str], brain_ran: bool
) -> Optional[EntityUpdate]:
    """`ent_upd` with the COMBAT_RETREAT flight issued, kept or ended as the module docstring says; unchanged on a tick the brain did not evaluate."""
    if ent_upd is None or not brain_ran or not _no_task_decision(ent_upd):
        return ent_upd
    project = _current_project(entity, strat_up, current_project_id)
    holds = _holds_combat_retreat(entity)
    if project is not None and project.kind == GoalKind.COMBAT_RETREAT:
        target = _target_position(project, strat_up)
        if holds or not target or _holds_another_flight(entity):
            return ent_upd
        return replace(
            ent_upd,
            navigation=replace(ent_upd.navigation or NavigationUpdate(), target_set=target),
            task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": target, "reason": FlightReason.COMBAT_RETREAT.value}),
        )
    if holds:  # the brain chose something else: its decision ends the flight before it is carried out
        return replace(ent_upd, navigation=replace(ent_upd.navigation or NavigationUpdate(), target_clear=True), task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}))
    return ent_upd
