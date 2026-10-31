"""What a subject does on arriving at a building its project walked to (SURV-06, EXCH-02), and the end of a shop visit made to sell.

A hunger project whose objective is a shop is the SELL opening step. The sale lands with its action (`building_services.py`); once the subject
stands in the shop's reach with nothing left the shop would buy, the visit is done, and the project ends so that the next hunger goal points at
the inn. Without this a sold worker stayed on the shop project, whose score the fresh inn goal did not clear the retention margin to replace.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from src.core.strategic import ObjectiveStatus, ProjectStatus
from src.core.updates import EntityUpdate, StrategicUpdate, TaskUpdate
from src.engine.building_services import SERVICE_KINDS, offers_work
from src.engine.service_admission import admits
from src.engine.shop_sale import plan_sale
from src.engine.work_shift import SHIFT_START, shift_takeable
from src.engine.work_wake import held_work_is_threatened


def _end_project(entity: Any, project: Any) -> EntityUpdate:
    """The update that completes `project` (its active objective resolved) and clears the subject's current project."""
    objectives = [replace(o, status=ObjectiveStatus.RESOLVED) if o.id == project.active_objective_id else o for o in project.objectives]
    return EntityUpdate(entity_id=entity.id, strategic=StrategicUpdate(
        projects_add_or_update=[replace(project, objectives=objectives, status=ProjectStatus.COMPLETED)],
        current_project_id_set="", current_objective_id_set=""))


def finished_visit(state: Any, entity: Any, project: Any, shop: Any) -> Optional[EntityUpdate]:
    """The update that ends `project` when `entity`, in `shop`'s reach, has nothing left to sell it; None while a sale remains."""
    return None if plan_sale(state, entity, shop) is not None else _end_project(entity, project)


HUNGER_NEED_FLOOR = 20.0  # the hunger scorer's own floor (EatScorer): below it there is no hunger need to meet


def _act(entity: Any, action: str, building_id: int, **extra: Any) -> EntityUpdate:
    return EntityUpdate(entity_id=entity.id, task=TaskUpdate(work_kind_set="ENTITY_ACT",
                                                             payload_set={"action": action, "target_id": building_id, **extra}))


def _hunger_arrival(state: Any, entity: Any, project: Any, building_id: int) -> EntityUpdate:
    """The hunger project's action at the building it reached: a sale at a shop (the visit ends once nothing is left to sell), else a meal, a shift or the end."""
    building = state.buildings.get(building_id)
    at_shop = getattr(building, "kind", None) == "shop"
    done = finished_visit(state, entity, project, building) if at_shop else None
    if done is not None:
        return done
    if at_shop:
        return _act(entity, "SELL", building_id)
    if entity.biological.hunger < HUNGER_NEED_FLOOR:
        return _end_project(entity, project)  # fed: a meal is bought only for a hunger (no paying to eat when not hungry)
    # The action is derived from what this building can do for the subject, never stored on the project: a building that serves a meal and would
    # deliver it to this subject (the one admission rule) is a meal; otherwise a building that offers a shift the subject can finish before the
    # starvation line is work (the EARN_THEN_BUY step, held for SHIFT_TICKS, paid on the last tick); otherwise there is nothing to do here.
    if getattr(building, "kind", None) in SERVICE_KINDS["EAT"] and admits(entity, "EAT"):
        return _act(entity, "EAT", building_id)
    if building is not None and offers_work(building):
        if shift_takeable(entity, state, building.position):
            return _act(entity, "WORK", building_id, **{SHIFT_START: state.tick})
        if held_work_is_threatened(entity, state):
            # Not takeable NOW because of a present threat (designer ruling 2026-10-30): the hunger project stays current, nothing is dispatched, and the
            # tactical answer to the threat takes over through the normal switch; the next decision judges again. The project is not ended or abandoned.
            return EntityUpdate(entity_id=entity.id)
    return _end_project(entity, project)  # no meal here and no shift it could finish before the starvation line: the project ends (the existing path)


def building_arrival_update(state: Any, entity: Any, project: Any, building_id: int) -> EntityUpdate:
    """The survival action by project kind at the building the subject reached: a meal, a shift or a sale (hunger), a bed (fatigue); anything else is idle."""
    kind = getattr(project, "kind", "")
    if kind == "hunger":
        return _hunger_arrival(state, entity, project, building_id)
    if kind == "fatigue":
        return _act(entity, "REST", building_id)
    return EntityUpdate(entity_id=entity.id)
