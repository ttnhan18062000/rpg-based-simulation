from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from src.core.inventory import InventoryService
from src.core.updates import InventoryUpdate, ResourceNodeUpdate, InteractionUpdate, IdentityUpdate, BiologicalUpdate, AttributeUpdate, CombatUpdate, StrategicUpdate, RewardUpdate, EquipmentUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, InventoryComponent
    from src.core.updates import ResourceTransferIntent

@dataclass(frozen=True, slots=True)
class TransactionResult:
    """Outcome of a resource transfer resolution."""
    accepted: bool
    inventory_update: Optional[InventoryUpdate] = None
    node_update: Optional[ResourceNodeUpdate] = None
    identity_update: Optional[IdentityUpdate] = None
    biological_update: Optional[BiologicalUpdate] = None
    attributes_update: Optional[AttributeUpdate] = None
    combat_update: Optional[CombatUpdate] = None
    strategic_update: Optional[StrategicUpdate] = None
    equipment_update: Optional[EquipmentUpdate] = None
    reward_update: Optional[RewardUpdate] = None
    home_storage_update: Optional[InventoryUpdate] = None
    ground_item_remove: Optional[int] = None
    corpse_remove: Optional[int] = None
    reason: str = ""

class ResourceTransactionResolver:
    """
    Authoritative layer for resolving resource transfer intents.
    Enforces the "Atomic Conservation Law": Source depletion and destination 
    receipt must happen together or not at all.
    VERIFIED v2: atomic_conservation_law
    """

    @staticmethod
    def resolve(
        state: AuthoritativeState, 
        entity: EntityState, 
        intent: ResourceTransferIntent,
        inventory_override: Optional[InventoryComponent] = None,
        node_overrides: Optional[Dict[int, ResourceNodeUpdate]] = None,
        reservations: Optional[Dict[tuple[str, str|int], int]] = None
    ) -> TransactionResult:
        """
        Validates an intent and produces the necessary updates.
        """
        # Phase E5.3: Exactly-Once Idempotency check
        # Law: A transaction with a specific ID must only succeed once across simulation time.
        if intent.transaction_id and intent.transaction_id in state.processed_transaction_ids:
            return TransactionResult(accepted=False, reason="ALREADY_PROCESSED")

        target_inventory = inventory_override if inventory_override is not None else entity.inventory
        
        # 1. Destination Capacity Check (Phase 8: Account for removals)
        # VERIFIED v2: inventory_slots_and_weight
        # VERIFIED v2: loot_abort_slot_pressure
        # VERIFIED v2: loot_abort_weight_pressure
        inventory_full = not InventoryService.can_add_items_with_removals(target_inventory, intent.items_add, intent.items_remove)
        
        # 2. Source/Cost Validation & Update Computation
        if intent.source_kind == "NODE":
            if inventory_full:
                 return TransactionResult(accepted=False, reason="INVENTORY_FULL")
            node = state.resource_nodes.get(intent.source_id)
            if not node:
                return TransactionResult(accepted=False, reason="SOURCE_MISSING")
            
            # Milestone 13 Fix: Account for sliding updates in the same tick
            remaining = node.remaining_charges
            if node_overrides and intent.source_id in node_overrides:
                remaining += node_overrides[intent.source_id].charges_delta
            
            # P0.2 Refinement: Account for in-tick reservations
            if reservations:
                remaining -= reservations.get(("NODE", intent.source_id), 0)
                
            if remaining <= 0:
                return TransactionResult(accepted=False, reason="SOURCE_DEPLETED")
            
            delta = -node.remaining_charges if node.kind == "LOOT" else -1
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                node_update=ResourceNodeUpdate(node_id=intent.source_id, charges_delta=delta)
            )
            # VERIFIED v2: loot_harvest_side_effects

        elif intent.source_kind == "GROUND_ITEM":
            if inventory_full:
                 return TransactionResult(accepted=False, reason="INVENTORY_FULL")
            ground_item = state.ground_items.get(intent.source_id)
            if not ground_item:
                return TransactionResult(accepted=False, reason="SOURCE_MISSING")
            
            # P0.2 Refinement: Account for in-tick reservations
            if reservations and reservations.get(("GROUND_ITEM", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason="SOURCE_LOCKED")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                ground_item_remove=intent.source_id
            )

        elif intent.source_kind == "CORPSE":
            if inventory_full:
                 return TransactionResult(accepted=False, reason="INVENTORY_FULL")
            corpse = state.corpses.get(intent.source_id)
            if not corpse:
                return TransactionResult(accepted=False, reason="SOURCE_MISSING")
            
            # P0.2 Refinement: Account for in-tick reservations
            if reservations and reservations.get(("CORPSE", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason="SOURCE_LOCKED")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                corpse_remove=intent.source_id
            )

        elif intent.source_kind == "CRAFTING":
            if inventory_full:
                 return TransactionResult(accepted=False, reason="INVENTORY_FULL")
            if target_inventory.gold < intent.gold_cost:
                return TransactionResult(accepted=False, reason="INSUFFICIENT_GOLD")
            
            for mat in intent.items_remove:
                have = sum(s.quantity for s in target_inventory.items if s.item_id == mat.item_id)
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
            if inventory_full:
                 return TransactionResult(accepted=False, reason="INVENTORY_FULL")
            if target_inventory.gold < intent.gold_cost:
                return TransactionResult(accepted=False, reason="INSUFFICIENT_GOLD")
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_add=intent.items_add,
                    gold_delta=-intent.gold_cost
                )
            )

        elif intent.source_kind == "SHOP_SELL":
            # Selling doesn't need capacity check (it removes items)
            for item in intent.items_remove:
                have = sum(s.quantity for s in target_inventory.items if s.item_id == item.item_id)
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
            # P0.2 Refinement: Account for in-tick reservations (Protect killed target)
            if reservations and reservations.get(("COMBAT", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason="SOURCE_LOCKED")

            # Progression Rule: XP is always granted, items/gold only if capacity allows
            reason = ""
            inv_up = None
            if not inventory_full:
                inv_up = InventoryUpdate(items_add=intent.items_add, gold_delta=intent.gold_delta)
            else:
                reason = "INVENTORY_FULL_GOLD_ITEMS_DROPPED"

            return TransactionResult(
                accepted=True,
                inventory_update=inv_up,
                reward_update=intent.reward_upd or RewardUpdate(xp_gain=intent.xp_reward),
                reason=reason
            )

        elif intent.source_kind == "QUEST":
            # P0.2 Refinement: Account for in-tick reservations
            if reservations and reservations.get(("QUEST", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason="SOURCE_LOCKED")

            # Progression Rule: XP is always granted, items/gold only if capacity allows
            reason = ""
            inv_up = None
            if not inventory_full:
                inv_up = InventoryUpdate(items_add=intent.items_add, gold_delta=intent.gold_delta)
            else:
                reason = "INVENTORY_FULL_GOLD_ITEMS_DROPPED"

            return TransactionResult(
                accepted=True,
                inventory_update=inv_up,
                reward_update=intent.reward_upd or RewardUpdate(xp_gain=intent.xp_reward),
                reason=reason
            )

        # VERIFIED v2: authoritative_side_effects
        if intent.source_kind in ("TOWN_SERVICE", "TAX"):
             if target_inventory.gold < intent.gold_cost:
                 return TransactionResult(accepted=False, reason="INSUFFICIENT_GOLD")
                 
             return TransactionResult(
                 accepted=True,
                 inventory_update=InventoryUpdate(
                      items_add=intent.items_add,
                      gold_delta=intent.gold_delta - intent.gold_cost
                 ),
                 identity_update=intent.identity_upd,
                 biological_update=intent.biological_upd,
                 attributes_update=intent.attributes_upd,
                 combat_update=intent.combat_upd,
                 strategic_update=intent.strategic_upd,
                 equipment_update=intent.equipment_upd,
                 reward_update=intent.reward_upd
             )
        
        elif intent.source_kind in ("RECRUIT", "CHEST"):
             # P0.1 Refinement: Source-level locks for world sources
             if reservations and reservations.get((intent.source_kind, intent.source_id), 0) > 0:
                 return TransactionResult(accepted=False, reason="SOURCE_LOCKED")

             if target_inventory.gold < intent.gold_cost:
                 return TransactionResult(accepted=False, reason="INSUFFICIENT_GOLD")
                 
             return TransactionResult(
                 accepted=True,
                 inventory_update=InventoryUpdate(
                      items_add=intent.items_add,
                      gold_delta=intent.gold_delta - intent.gold_cost
                 ),
                 identity_update=intent.identity_upd,
                 biological_update=intent.biological_upd,
                 attributes_update=intent.attributes_upd,
                 combat_update=intent.combat_upd,
                 strategic_update=intent.strategic_upd,
                 equipment_update=intent.equipment_upd,
                 reward_update=intent.reward_upd
             )
        
        elif intent.source_kind == "HOME_STORAGE":
             # Transfer between Entity and their private storage
             storage_id = entity.id
             storage = state.home_storage.get(storage_id)
             if not storage:
                  from src.core.state import InventoryComponent
                  storage = InventoryComponent(max_slots=32, max_weight=200.0)
             
             # Validation: If Entity is Gaining (Withdraw), Storage must have items
             for item in intent.items_add:
                  have = sum(s.quantity for s in storage.items if s.item_id == item.item_id)
                  if have < item.quantity:
                       return TransactionResult(accepted=False, reason="INSUFFICIENT_STORAGE_ITEMS")
             
             # Validation: If Entity is Giving (Deposit), Storage must have capacity
             if intent.items_remove:
                  if not InventoryService.can_add_items(storage, intent.items_remove):
                       return TransactionResult(accepted=False, reason="STORAGE_FULL")
             
             # Validation: If Entity is Giving (Deposit), Entity must have items
             for item in intent.items_remove:
                  have = sum(s.quantity for s in target_inventory.items if s.item_id == item.item_id)
                  if have < item.quantity:
                       return TransactionResult(accepted=False, reason="INSUFFICIENT_ITEMS")

             return TransactionResult(
                 accepted=True,
                 inventory_update=InventoryUpdate(
                      items_add=intent.items_add,
                      items_remove=intent.items_remove
                 ),
                 home_storage_update=InventoryUpdate(
                      items_add=intent.items_remove,
                      items_remove=intent.items_add
                 )
             )
             
        return TransactionResult(accepted=False, reason="UNKNOWN_SOURCE_KIND")
