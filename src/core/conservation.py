from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from src.core.inventory import InventoryService
from src.core.updates import InventoryUpdate, ResourceNodeUpdate, InteractionUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import ResourceTransferIntent

@dataclass(frozen=True, slots=True)
class TransactionResult:
    """Outcome of a resource transfer resolution."""
    accepted: bool
    inventory_update: Optional[InventoryUpdate] = None
    node_update: Optional[ResourceNodeUpdate] = None
    identity_update: Optional[IdentityUpdate] = None
    ground_item_remove: Optional[int] = None
    corpse_remove: Optional[int] = None
    reason: str = ""

class ResourceTransactionResolver:
    """
    Authoritative layer for resolving resource transfer intents.
    Enforces the "Atomic Conservation Law": Source depletion and destination 
    receipt must happen together or not at all.
    """

    @staticmethod
    def resolve(
        state: AuthoritativeState, 
        entity: EntityState, 
        intent: ResourceTransferIntent,
        inventory_override: Optional[InventoryComponent] = None
    ) -> TransactionResult:
        """
        Validates an intent and produces the necessary updates.
        """
        target_inventory = inventory_override if inventory_override is not None else entity.inventory
        
        # 1. Destination Capacity Check
        if not InventoryService.can_add_items(target_inventory, intent.items_add):
            return TransactionResult(accepted=False, reason="INVENTORY_FULL")

        # 2. Source/Cost Validation & Update Computation
        if intent.source_kind == "NODE":
            node = state.resource_nodes.get(intent.source_id)
            if not node or node.remaining_charges <= 0:
                return TransactionResult(accepted=False, reason="SOURCE_DEPLETED")
            
            delta = -node.remaining_charges if node.kind == "LOOT" else -1
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                node_update=ResourceNodeUpdate(node_id=intent.source_id, charges_delta=delta)
            )

        elif intent.source_kind == "GROUND_ITEM":
            ground_item = state.ground_items.get(intent.source_id)
            if not ground_item:
                return TransactionResult(accepted=False, reason="SOURCE_MISSING")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                ground_item_remove=intent.source_id
            )

        elif intent.source_kind == "CORPSE":
            corpse = state.corpses.get(intent.source_id)
            if not corpse:
                return TransactionResult(accepted=False, reason="SOURCE_MISSING")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                corpse_remove=intent.source_id
            )

        elif intent.source_kind == "CRAFTING":
            if entity.inventory.gold < intent.gold_cost:
                return TransactionResult(accepted=False, reason="INSUFFICIENT_GOLD")
            
            for mat in intent.items_remove:
                have = sum(s.quantity for s in entity.inventory.items if s.item_id == mat.item_id)
                if have < mat.quantity:
                    return TransactionResult(accepted=False, reason="INSUFFICIENT_MATERIALS")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_add=intent.items_add,
                    items_remove=intent.items_remove,
                    gold_delta=-intent.gold_cost
                )
            )

        elif intent.source_kind == "SHOP_BUY":
            if entity.inventory.gold < intent.gold_cost:
                return TransactionResult(accepted=False, reason="INSUFFICIENT_GOLD")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_add=intent.items_add,
                    gold_delta=-intent.gold_cost
                )
            )

        elif intent.source_kind == "SHOP_SELL":
            for item in intent.items_remove:
                have = sum(s.quantity for s in entity.inventory.items if s.item_id == item.item_id)
                if have < item.quantity:
                    return TransactionResult(accepted=False, reason="INSUFFICIENT_ITEMS")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_remove=intent.items_remove,
                    gold_delta=intent.gold_delta
                )
            )

        elif intent.source_kind == "COMBAT":
            # Law of Combat: Gold from kills
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    gold_delta=intent.gold_delta
                )
            )

        elif intent.source_kind == "QUEST":
            # Law of Reward: Quests grant resources without cost
            from src.core.updates import IdentityUpdate
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_add=intent.items_add,
                    gold_delta=intent.gold_delta
                ),
                identity_update=IdentityUpdate(evolution_points_delta=intent.xp_reward)
            )

        return TransactionResult(accepted=False, reason="UNKNOWN_SOURCE_KIND")
