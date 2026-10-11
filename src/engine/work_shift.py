"""A shift of work at an inn for a wage (EXCH-02, owner decision 34: a wage for work at a shop, inn or smithy, paid from the payer's own purse).

A subject that cannot afford a meal and has nothing a shop would buy can work a shift at the inn: the WORK action, held tick after tick beside a
functional inn, counts up the interaction progress the node harvest already uses (``kind="work"``, no new state). Walking away, taking damage or
changing task resets it (``interaction.py``). After SHIFT_TICKS consecutive ticks the inn pays WAGE_GOLD out of its OWN purse as one typed ``WAGE``
transfer; a short purse pays nothing (the resolver rejects it) and the worker has worked unpaid. The inn's coin is credited by the meals and
beds it sells, so the loop closes through the inn's purse. The town (treasury) wage for public work is a separate path, not built here.

Values follow the fiction (owner decision 33): 200 ticks at 36 seconds a tick (Bible 05) is a two-hour kitchen and yard shift; its 6 gold is a
meal (5) and a coin.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.core.updates import EntityUpdate, InteractionUpdate, ResourceTransferIntent
from src.engine.building_services import service_building
from src.engine.serves import nearest_serving, serves

SHIFT_TICKS = 200
WAGE_GOLD = 6
SHIFT_START = "shift_start"  # the tick the shift began, carried by the held WORK task's payload


def nearest_work(state: Any, entity: Any) -> Optional[Any]:
    """The nearest functional inn that hires `entity` (it serves it, owner decision 43) and whose purse covers one wage, or None."""
    return nearest_serving(state, entity, state.buildings.values(), "inn", accept=lambda inn: inn.inventory.gold >= WAGE_GOLD)


def shift_done(update: Optional[EntityUpdate]) -> bool:
    """True when `update` ends a shift (completed, or no inn in reach): the held WORK task then ends."""
    return update is not None and update.interaction is not None and update.interaction.reset


def work_update(entity: Any, payload: Dict[str, Any], tick: int, context: Any) -> Dict[int, EntityUpdate]:
    """One tick of the shift: nothing until the SHIFT_TICKS-th tick since it began, then the inn's wage and the end of the shift."""
    inn = service_building(context, entity, "WORK") if context is not None else None
    if inn is None or not serves(context, entity, inn):
        return {entity.id: EntityUpdate(entity_id=entity.id, interaction=InteractionUpdate(reset=True))}
    if tick - int(payload.get(SHIFT_START, tick)) + 1 < SHIFT_TICKS:
        return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}
    # A held action runs twice a tick (the worker, then the routing phase); one shift is paid once, by its transaction id.
    shift = f"wage:{entity.id}:{inn.id}:{payload.get(SHIFT_START, tick)}"
    wage = ResourceTransferIntent(source_id=inn.id, source_kind="WAGE", gold_delta=WAGE_GOLD, transfer_kind="WAGE", transaction_id=shift)
    return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0, resource_transfers=[wage], interaction=InteractionUpdate(reset=True))}
