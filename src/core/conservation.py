from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from src.core.inventory import InventoryService
from src.core.enums import ReasonCode
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
    building_update: Optional[BuildingUpdate] = None
    ground_item_remove: Optional[int] = None
    corpse_remove: Optional[int] = None
    reason: ReasonCode = ReasonCode.UNKNOWN

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
            return TransactionResult(accepted=False, reason=ReasonCode.IDEMPOTENCY_VIOLATION)

        target_inventory = inventory_override if inventory_override is not None else entity.inventory
        
        # 1. Destination Capacity Check (Phase 8: Account for removals)
        # VERIFIED v2: inventory_slots_and_weight
        # VERIFIED v2: loot_abort_slot_pressure
        # VERIFIED v2: loot_abort_weight_pressure
        # RPG-RES-003, RPG-RES-004, RPG-RES-005, RPG-RES-201
        inventory_full = not InventoryService.can_add_items_with_removals(target_inventory, intent.items_add, intent.items_remove)
        
        # 2. Source/Cost Validation & Update Computation
        if intent.source_kind == "NODE":
            if inventory_full:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
            node = state.resource_nodes.get(intent.source_id)
            if not node:
                return TransactionResult(accepted=False, reason=ReasonCode.TARGET_INVALID)
            
            # Milestone 13 Fix: Account for sliding updates in the same tick
            remaining = node.remaining_charges
            if node_overrides and intent.source_id in node_overrides:
                remaining += node_overrides[intent.source_id].charges_delta
            
            # P0.2 Refinement: Account for in-tick reservations
            if reservations:
                remaining -= reservations.get(("NODE", intent.source_id), 0)
                
            if remaining <= 0:
                return TransactionResult(accepted=False, reason=ReasonCode.SOURCE_DEPLETED)
            
            delta = -node.remaining_charges if node.kind == "LOOT" else -1
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                node_update=ResourceNodeUpdate(node_id=intent.source_id, charges_delta=delta)
            )
            # VERIFIED v2: loot_harvest_side_effects

        elif intent.source_kind == "GROUND_ITEM":
            if inventory_full:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
            ground_item = state.ground_items.get(intent.source_id)
            if not ground_item:
                return TransactionResult(accepted=False, reason=ReasonCode.SOURCE_MISSING)
            
            # P0.2 Refinement: Account for in-tick reservations
            if reservations and reservations.get(("GROUND_ITEM", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason=ReasonCode.TARGET_LOCKED)
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                ground_item_remove=intent.source_id
            )

        elif intent.source_kind == "CORPSE":
            if inventory_full:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
            corpse = state.corpses.get(intent.source_id)
            if not corpse:
                return TransactionResult(accepted=False, reason=ReasonCode.SOURCE_MISSING)
            
            # P0.2 Refinement: Account for in-tick reservations
            if reservations and reservations.get(("CORPSE", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason=ReasonCode.TARGET_LOCKED)
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add),
                corpse_remove=intent.source_id
            )

        elif intent.source_kind == "CRAFTING":
            # RPG-RES-200: Conversion must account for removals
            if inventory_full:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
            # RPG-ECON-008
            if target_inventory.gold < intent.gold_cost:
                return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_GOLD)
            
            for mat in intent.items_remove:
                have = sum(s.quantity for s in target_inventory.items if s.item_id == mat.item_id)
                if have < mat.quantity:
                    return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_RESOURCES)
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_add=intent.items_add,
                    items_remove=intent.items_remove,
                    gold_delta=-intent.gold_cost
                )
            )

        elif intent.source_kind == "SHOP_BUY":
            # RPG-RES-119, RPG-ECON-200
            if inventory_full:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
            
            building = state.buildings.get(intent.source_id)
            if not building or not building.functional:
                return TransactionResult(accepted=False, reason=ReasonCode.TARGET_INVALID)

            # 1. Capacity/Stock Check
            # RPG-ECON-200
            for item in intent.items_add:
                have = sum(s.quantity for s in building.inventory.items if s.item_id == item.item_id)
                if have < item.quantity:
                    return TransactionResult(accepted=False, reason=ReasonCode.OUT_OF_STOCK)
            
            # 2. Gold Check
            # RPG-ECON-004, RPG-ECON-200
            if target_inventory.gold < intent.gold_cost:
                return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_GOLD)
            
            from src.core.updates import BuildingUpdate
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_add=intent.items_add,
                    gold_delta=-intent.gold_cost
                ),
                building_update=BuildingUpdate(
                    building_id=intent.source_id,
                    inventory=InventoryUpdate(
                        items_remove=intent.items_add,
                        gold_delta=intent.gold_cost
                    )
                )
            )

        elif intent.source_kind == "SHOP_SELL":
            # RPG-ECON-201: Shop liquidity check
            # Selling doesn't need capacity check for entity (it removes items)
            # But shop needs enough gold
            building = state.buildings.get(intent.source_id)
            if not building or not building.functional:
                return TransactionResult(accepted=False, reason=ReasonCode.TARGET_INVALID)

            if building.inventory.gold < intent.gold_delta:
                return TransactionResult(accepted=False, reason=ReasonCode.LIQUIDITY_EXHAUSTED)

            for item in intent.items_remove:
                have = sum(s.quantity for s in target_inventory.items if s.item_id == item.item_id)
                if have < item.quantity:
                    return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_RESOURCES)
            
            from src.core.updates import BuildingUpdate
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(
                    items_remove=intent.items_remove,
                    gold_delta=intent.gold_delta
                ),
                building_update=BuildingUpdate(
                    building_id=intent.source_id,
                    inventory=InventoryUpdate(
                        items_add=intent.items_remove,
                        gold_delta=-intent.gold_delta
                    )
                )
            )

        elif intent.source_kind == "COMBAT":
            # Progression Rule: XP/Gold is granted only if items (if any) fit.
            # Law: If it has items, it must fit.
            if intent.items_add and inventory_full:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)

            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add, gold_delta=intent.gold_delta),
                identity_update=IdentityUpdate(evolution_points_delta=intent.xp_reward),
                reward_update=intent.reward_upd
            )

        elif intent.source_kind == "QUEST":
            # P0.2 Refinement: Account for in-tick reservations
            if reservations and reservations.get(("QUEST", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason=ReasonCode.TARGET_LOCKED)

            # Law: If it has items, it must fit.
            if intent.items_add and inventory_full:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)

            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add, gold_delta=intent.gold_delta),
                identity_update=IdentityUpdate(evolution_points_delta=intent.xp_reward),
                reward_update=intent.reward_upd
            )

        # VERIFIED v2: authoritative_side_effects
        if intent.source_kind in ("TOWN_SERVICE", "TAX"):
             if target_inventory.gold < intent.gold_cost:
                 return TransactionResult(accepted=False, reason=ReasonCode.ACTION_EXHAUSTION)
                 
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
                 return TransactionResult(accepted=False, reason=ReasonCode.TARGET_LOCKED)

             if target_inventory.gold < intent.gold_cost:
                 return TransactionResult(accepted=False, reason=ReasonCode.ACTION_EXHAUSTION)
                 
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
                       return TransactionResult(accepted=False, reason=ReasonCode.ACTION_EXHAUSTION)
             
             # Validation: If Entity is Giving (Deposit), Storage must have capacity
             if intent.items_remove:
                  if not InventoryService.can_add_items(storage, intent.items_remove):
                       return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_CAPACITY)
             
             # Validation: If Entity is Giving (Deposit), Entity must have items
             for item in intent.items_remove:
                  have = sum(s.quantity for s in target_inventory.items if s.item_id == item.item_id)
                  if have < item.quantity:
                       return TransactionResult(accepted=False, reason=ReasonCode.ACTION_EXHAUSTION)

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
             
        return TransactionResult(accepted=False, reason=ReasonCode.UNKNOWN_SOURCE_KIND)
