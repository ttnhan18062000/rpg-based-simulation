"""How a repair is paid (EXCH-02, owner decision 58): once, into the purse of the smith in reach; away from a smith by a carried repair kit that is
used up and moves no coin; otherwise not at all."""
from __future__ import annotations

from typing import Any, Dict

from src.core.models.inventory import ItemStack
from src.core.updates import (
    EntityUpdate,
    EquipmentUpdate,
    InventoryUpdate,
    ResourceTransferIntent,
)
from src.engine.building_services import service_building

REPAIR_KIT = "repair_kit"


def repair_update(entity: Any, repair_deltas: Dict[Any, float], total_cost: int, context: Any) -> Dict[int, EntityUpdate]:
    """The update that restores the durability in `repair_deltas`, at a smith (charged `total_cost` once) or with a kit, or a no-op when neither is at hand."""
    smith = service_building(context, entity, "REPAIR") if context is not None else None
    if smith is not None:
        charge = ResourceTransferIntent(source_id=smith.id, source_kind="TOWN_SERVICE", gold_cost=total_cost, transfer_kind="REPAIR",
                                        equipment_upd=EquipmentUpdate(durability_set=repair_deltas))
        return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-100.0, resource_transfers=[charge])}
    if any(i.item_id == REPAIR_KIT and i.quantity > 0 for i in entity.inventory.items):
        return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-100.0, equipment=EquipmentUpdate(durability_set=repair_deltas),
                                        inventory=InventoryUpdate(items_remove=[ItemStack(REPAIR_KIT, 1)]))}
    return {entity.id: EntityUpdate(entity_id=entity.id)}
