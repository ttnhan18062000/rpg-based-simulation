"""Building services land when their action executes (EXCH-02; bug fix of the cadence-gated town phase).

A bed (inn, home), a meal (inn) and a chosen sale (shop) used to be attached in ``TownResolutionSystem.resolve``, a phase that runs only on
ticks divisible by the profile's ``town_resolution`` cadence and that read the request from the entity's NEW task in that tick's update. A
subject's brain decides on its own offset, so for most subjects the request was never present when the phase ran. The service now lands in the
action itself: ``ActionRouter`` asks :func:`service_delta` when a REST, EAT or SELL action executes, and merges the result into the action's
update. The action runs wherever the subject is processed (the main thread or a worker); the lookup uses only what a ``WorkerPacket`` carries
(``SpatialQueryService.get_building_at``), and the building's purse and stock change only through the typed transfer the apply path resolves.
"""
from __future__ import annotations

from typing import Any, Optional

from src.core.updates import (
    BiologicalUpdate,
    CombatUpdate,
    EntityUpdate,
    ResourceTransferIntent,
)
from src.engine.serves import serves
from src.engine.service_prices import EAT_PRICE_GOLD, INN_MEAL_HUNGER, REST_PRICE_GOLD
from src.engine.service_reach import service_tile
from src.engine.shop_sale import plan_sale
from src.engine.spatial_query import SpatialQueryService

# The building kinds that serve an action.
SERVICE_KINDS = {"REST": frozenset({"inn", "home"}), "EAT": frozenset({"inn"}), "SELL": frozenset({"shop"}), "WORK": frozenset({"inn"}), "REPAIR": frozenset({"blacksmith"})}


def service_building(context: Any, entity: Any, action: str) -> Optional[Any]:
    """The functional building (of the kinds that serve `action`) the subject stands on or orthogonally beside, or None."""
    kinds = SERVICE_KINDS.get(action)
    if kinds is None:
        return None
    tile = service_tile(context, (int(entity.navigation.position[0]), int(entity.navigation.position[1])), kinds)
    building = SpatialQueryService.get_building_at(context, tile) if tile is not None else None
    return building if building is not None and building.functional else None


def repair_source(context: Any, entity: Any) -> Any:
    """The payee of a repair: the blacksmith in reach, so the resolver credits its purse with what was actually paid (EXCH-02: no coin
    vanishes); with none in reach the repair keeps its old unnamed payee, as on main (repair needs no building today)."""
    smith = service_building(context, entity, "REPAIR") if context is not None else None
    return "BLACKSMITH" if smith is None else smith.id


def service_delta(context: Any, entity: Any, action: str, tick: int) -> Optional[EntityUpdate]:
    """What the building service for `action` adds to the subject's update, or None (no such building in reach, or nothing to deliver).

    A bed and an inn meal are as they were on main (free meals stay on, owner decision 44): the effects are on the update, the price is a
    charge the resolver clamps at what the subject holds, and the building's purse is credited with what was actually paid."""
    building = service_building(context, entity, action)
    if building is None or (action == "SELL" and not serves(context, entity, building)):
        return None
    if action == "REST":
        charge = ResourceTransferIntent(source_id=building.id, source_kind="TOWN_SERVICE", gold_delta=-REST_PRICE_GOLD, transfer_kind="REST",
                                        is_group_required=True)
        return EntityUpdate(entity_id=entity.id, readiness_delta=10.0, combat=CombatUpdate(hp_delta=5),
                            resource_transfers=[charge])
    if action == "EAT":
        charge = ResourceTransferIntent(source_id=building.id, source_kind="TOWN_SERVICE", gold_delta=-EAT_PRICE_GOLD, transfer_kind="EAT",
                                        is_group_required=True)
        return EntityUpdate(entity_id=entity.id, biological=BiologicalUpdate(hunger_delta=-INN_MEAL_HUNGER), resource_transfers=[charge])
    sale = plan_sale(context, entity, building)
    return None if sale is None else EntityUpdate(entity_id=entity.id, resource_transfers=[sale])


def with_service(updates: dict, entity: Any, action: str, tick: int, context: Any) -> dict:
    """The action's updates with the building service for `action` merged into the subject's own update."""
    if context is None or entity.id not in updates or (action == "REST" and "outcome" in entity.task.payload):
        return updates  # (a held sleep repeats its action every tick; the bed is paid for, and heals, once)
    delta = service_delta(context, entity, action, tick)
    if delta is None:
        return updates
    return {**updates, entity.id: updates[entity.id].merge(delta)}
