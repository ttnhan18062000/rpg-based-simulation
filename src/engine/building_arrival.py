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
from src.engine.shop_sale import plan_sale


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


def building_arrival_update(state: Any, entity: Any, project: Any, building_id: int) -> EntityUpdate:
    """The survival action by project kind at the building the subject reached: a meal at the inn or a sale at a shop (hunger; the shop visit
    ends once nothing is left to sell), a bed (fatigue); anything else is idle."""
    kind = getattr(project, "kind", "")
    if kind == "hunger":
        building = state.buildings.get(building_id)
        at_shop = getattr(building, "kind", None) == "shop"
        done = finished_visit(state, entity, project, building) if at_shop else None
        if done is not None:
            return done
        if at_shop:
            return _act(entity, "SELL", building_id)
        if entity.biological.hunger < HUNGER_NEED_FLOOR:
            return _end_project(entity, project)  # fed: a meal is bought only for a hunger (no paying to eat when not hungry)
        # At the inn the hunger step is a meal. Free meals stay on (owner decision 44), so a broke subject eats too; the shift of work
        # (work_shift.py) is dispatched here only on the removal stack, where a meal costs coin and a broke subject cannot eat.
        return _act(entity, "EAT", building_id)
    if kind == "fatigue":
        return _act(entity, "REST", building_id)
    return EntityUpdate(entity_id=entity.id)
