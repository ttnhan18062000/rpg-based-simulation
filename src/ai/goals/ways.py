"""
src/ai/goals/ways.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6

The food ways (SURV-06) a subject can take now, as one pure read of the state. The hunger scorer and the starvation-death record both ask
this module, so what the pull judged open and what the record says were open cannot diverge. Nothing here changes state or behaviour.

`ways_in_reach` is the TRUE-MAP set. Until M1's honest-perception child lands, what the subject's pull judged open (H6 column a) equals it;
the record keeps both columns and a test pins that they are equal until then.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Tuple

from src.ai.goals.opening_steps import _forage_step, _hunt_step, _scavenge_step, shop_sale_in_reach, work_in_reach
from src.core.items import food_hunger_recovery
from src.core.state import AuthoritativeState, BuildingState, EntityState
from src.engine.appraisal import can_eat_item, can_use_inn_meal
from src.engine.spatial_query import SpatialQueryService
from src.engine.way_in_range import way_in_range


class WayKind(str, Enum):
    """The ways a hungry subject can come by a meal (SURV-06). A kind lists only the ways its diet allows."""
    CARRIED_FOOD = "CARRIED_FOOD"
    INN_MEAL = "INN_MEAL"
    FORAGE = "FORAGE"
    BUY = "BUY"                  # sell spare goods to a shop, then buy a meal
    WORK_SHIFT = "WORK_SHIFT"    # a paid shift at a building that can pay a wage
    SCAVENGE = "SCAVENGE"        # a carcass within reach holding food the diet can eat
    HUNT_EAT_RAW = "HUNT_EAT_RAW"  # a living creature the subject appraises as prey
    RECEIVE = "RECEIVE"            # declared; never returned until a social path exists


def inn_in_reach(entity: EntityState, state: AuthoritativeState) -> Optional[BuildingState]:
    """The nearest inn inside the subject's range, or None (a range-bound subject's ways are inside its range, owner decision D57)."""
    inn = SpatialQueryService.nearest_building(state, entity.navigation.position, "inn")
    if inn is not None and not way_in_range(entity, inn.position):
        return None
    return inn


def ways_in_reach(entity: EntityState, state: AuthoritativeState) -> Tuple[WayKind, ...]:
    """Every food way open to the subject now, in the fixed WayKind order. Pure: reads the state, writes nothing."""
    ways = []
    if any(food_hunger_recovery(stack.item_id) > 0.0 and can_eat_item(entity, stack.item_id) for stack in entity.inventory.items):
        ways.append(WayKind.CARRIED_FOOD)
    if inn_in_reach(entity, state) is not None and can_use_inn_meal(entity):  # decision 44: a diet without prepared food has no inn meal
        ways.append(WayKind.INN_MEAL)
    if _forage_step(entity, state).available:
        ways.append(WayKind.FORAGE)
    if _scavenge_step(entity, state).available:
        ways.append(WayKind.SCAVENGE)
    if _hunt_step(entity, state).available:
        ways.append(WayKind.HUNT_EAT_RAW)
    if shop_sale_in_reach(entity, state) is not None:
        ways.append(WayKind.BUY)
    if work_in_reach(entity, state) is not None:
        ways.append(WayKind.WORK_SHIFT)
    return tuple(ways)
