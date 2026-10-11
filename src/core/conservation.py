# Compliance IDs: COMBAT-066, DATA-004, DATA-005, DATA-006, DATA-007, DATA-008, DATA-049, DATA-063, DATA-080, DATA-094, DATA-098, DATA-104, DATA-106, DATA-107, DATA-108, DATA-111, ECON-003, ECON-200, ECON-201, INFRA-052, INFRA-055, INFRA-058, INFRA-072, INFRA-091, INFRA-107, INFRA-114, INFRA-115, INFRA-116, INFRA-120, INFRA-123, PROG-044, PROG-133, RES-001, RES-002, RES-003, RES-004, RES-005, RES-006, RES-008, RES-010, RES-013, RES-019, RES-020, RES-029, RES-036, RES-037, RES-038, RES-039, RES-040, RES-041, RES-042, RES-043, RES-044, RES-047, RES-048, RES-049, RES-050, RES-053, RES-055, RES-056, RES-057, RES-058, RES-059, RES-061, RES-064, RES-068, RES-069, RES-070, RES-071, RES-072, RES-073, RES-074, RES-075, RES-076, RES-077, RES-078, RES-079, RES-080, RES-081, RES-082, RES-083, RES-084, RES-088, RES-089, RES-090, RES-091, RES-092, RES-093, RES-094, RES-095, RES-096, RES-097, RES-098, RES-099, RES-100, RES-101, RES-102, RES-103, RES-104, RES-105, RES-106, RES-107, RES-108, RES-109, RES-110, RES-111, RES-112, RES-113, RES-114, RES-115, RES-116, RES-117, RES-118, RES-119, RES-200, RES-201, SOC-026, STRAT-011, STRAT-104, STRAT-172, STRAT-173, STRAT-174, STRAT-175, WORLD-164
# Compliance IDs: TOWN-011
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.models.world_records import OwedRecord
from src.core.treasury import TreasuryTransfer, can_pay
from src.core.enums import ReasonCode
from src.core.inventory import InventoryService
from src.core.quests import QuestStatus
from src.core.updates import (
    AttributeUpdate,
    BuildingUpdate,
    BiologicalUpdate,
    CombatUpdate,
    EquipmentUpdate,
    IdentityUpdate,
    InteractionUpdate,
    InventoryUpdate,
    QuestUpdate,
    ResourceNodeUpdate,
    RewardUpdate,
    StrategicUpdate,
)

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, InventoryComponent
    from src.core.updates import ResourceTransferIntent

@dataclass(frozen=True, slots=True)
class SourceDebit:
    """What a transfer takes from another entity's own inventory (an inheritance), applied with the receipt or not at all."""
    entity_id: int
    inventory_update: InventoryUpdate


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
    quest_update: Optional[QuestUpdate] = None
    home_storage_update: Optional[InventoryUpdate] = None
    building_update: Optional[BuildingUpdate] = None
    ground_item_remove: Optional[int] = None
    corpse_remove: Optional[int] = None
    source_debit: Optional[SourceDebit] = None
    treasury_update: Optional[TreasuryTransfer] = None
    owed: Optional[Any] = None  # an OwedRecord: the coin a short treasury could not pay now and owes instead
    reason: ReasonCode = ReasonCode.UNKNOWN

def _tax_credit(intent: ResourceTransferIntent) -> Optional[TreasuryTransfer]:
    """The share of a sale's or a wage's proceeds that goes to the treasury of the faction holding the place (the intent names it)."""
    if intent.treasury_faction is None or intent.treasury_gold <= 0:
        return None
    return TreasuryTransfer(faction=intent.treasury_faction, gold_delta=min(intent.treasury_gold, intent.gold_delta))


def _wage_result(state: Any, intent: ResourceTransferIntent, treasury_pending: Optional[Dict[str, float]] = None) -> TransactionResult:
    """EXCH-02: a wage is a transfer from the employer's own purse. A short purse pays nothing (the worker is unpaid, no coin appears), unless the
    intent says the owning treasury funds a shortfall (``treasury_pays``, maintenance work at a treasury building, ruling 61): then the treasury tops
    the purse up by exactly the shortfall first, and the treasury's net change (the top-up less any tax share) is one typed transfer."""
    employer = state.buildings.get(intent.source_id)
    if employer is None or not employer.functional:
        return TransactionResult(accepted=False, reason=ReasonCode.TARGET_INVALID)
    if intent.gold_delta <= 0:
        return TransactionResult(accepted=False, reason=ReasonCode.LIQUIDITY_EXHAUSTED)
    shortfall = max(0, intent.gold_delta - employer.inventory.gold)
    faction = intent.treasury_faction
    if shortfall > 0 and not (intent.treasury_pays and faction is not None and can_pay(state.global_resources, faction, shortfall, treasury_pending)):
        return TransactionResult(accepted=False, reason=ReasonCode.LIQUIDITY_EXHAUSTED)
    tax = _tax_credit(intent)
    net = (tax.gold_delta if tax else 0) - shortfall
    return TransactionResult(
        accepted=True,
        inventory_update=InventoryUpdate(gold_delta=intent.gold_delta - (tax.gold_delta if tax else 0)),
        building_update=BuildingUpdate(building_id=employer.id, inventory=InventoryUpdate(gold_delta=shortfall - intent.gold_delta)),
        treasury_update=TreasuryTransfer(faction=faction, gold_delta=net) if net and faction is not None else None)


def _service_credit(state: Any, intent: ResourceTransferIntent, price: int) -> Optional[Any]:
    """The building's purse receives what a bought service costs (EXCH-02: every coin is some purse's coin). A service whose source is a
    building id (a bed, a meal at an inn or home) pays that building; a fee, a tax or a purchase with a named source is a sink as before."""
    if not isinstance(intent.source_id, int) or price <= 0 or intent.source_id not in state.buildings:
        return None
    return BuildingUpdate(building_id=intent.source_id, inventory=InventoryUpdate(gold_delta=price))


def _inherit_result(state: Any, intent: ResourceTransferIntent, inventory_full: bool) -> TransactionResult:
    """EXCH-02: what the dead entity carried, items and coin, moves to its heir, once. The dead entity is debited with the heir's receipt, so
    a receipt the heir cannot take (a full inventory) leaves the goods where they were and nothing is copied."""
    dead = state.entities.get(intent.source_id) if isinstance(intent.source_id, int) else None
    if dead is None:
        return TransactionResult(accepted=False, reason=ReasonCode.TARGET_INVALID)
    if inventory_full:
        return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
    for item in intent.items_add:
        if sum(s.quantity for s in dead.inventory.items if s.item_id == item.item_id) < item.quantity:
            return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_RESOURCES)
    if intent.gold_delta < 0 or dead.inventory.gold < intent.gold_delta:
        return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_RESOURCES)
    return TransactionResult(
        accepted=True,
        inventory_update=InventoryUpdate(items_add=intent.items_add, gold_delta=intent.gold_delta),
        source_debit=SourceDebit(entity_id=dead.id, inventory_update=InventoryUpdate(items_remove=intent.items_add, gold_delta=-intent.gold_delta)))


def _carried_food_result(intent: ResourceTransferIntent, inventory: InventoryComponent) -> TransactionResult:
    """Eating what the subject carries: the item is consumed together with the meal, or nothing happens."""
    for item in intent.items_remove:
        if sum(s.quantity for s in inventory.items if s.item_id == item.item_id) < item.quantity:
            return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_RESOURCES)
    return TransactionResult(accepted=True, inventory_update=InventoryUpdate(items_remove=intent.items_remove), biological_update=intent.biological_upd)


def _reward_result(intent: ResourceTransferIntent, inventory_full: bool, reservations: Optional[Dict[Any, int]]) -> TransactionResult:
    """A COMBAT or QUEST grant. A quest accounts for in-tick reservations first (P0.2); both grant XP/gold only if the items fit
    (Progression Rule: if it has items, it must fit)."""
    is_quest = intent.source_kind == "QUEST"
    if is_quest and reservations and reservations.get(("QUEST", intent.source_id), 0) > 0:
        return TransactionResult(accepted=False, reason=ReasonCode.TARGET_LOCKED)
    if intent.items_add and inventory_full:
        return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
    return TransactionResult(
        accepted=True,
        inventory_update=InventoryUpdate(items_add=intent.items_add, gold_delta=intent.gold_delta),
        identity_update=IdentityUpdate(evolution_points_delta=intent.xp_reward),
        reward_update=intent.reward_upd,
        quest_update=QuestUpdate(quest_id=str(intent.source_id), status_set=QuestStatus.REWARDED) if is_quest else None,
    )


def _fund_reward(result: TransactionResult, intent: ResourceTransferIntent, state: Any, entity: Any,
                 treasury_pending: Optional[Dict[str, float]]) -> TransactionResult:
    """EXCH-02, decision 38: a reward whose coin is funded by a treasury is paid from it when it holds the coin; a short treasury grants the rest of
    the reward and OWES the coin (an OwedRecord, paid oldest first). A reward with no treasury named is left as it was."""
    gold = intent.gold_delta
    if not (result.accepted and intent.treasury_pays and intent.treasury_faction is not None and gold > 0):
        return result
    if can_pay(state.global_resources, intent.treasury_faction, gold, treasury_pending):
        return replace(result, treasury_update=TreasuryTransfer(faction=intent.treasury_faction, gold_delta=-int(gold)))
    owed = OwedRecord(id=f"owed:{intent.source_id}:{entity.id}", creditor_id=entity.id, debtor_faction=intent.treasury_faction,
                      amount=int(gold), posted_tick=state.tick, reason=f"{intent.source_kind}_REWARD")
    unpaid = InventoryUpdate(items_add=intent.items_add)  # the items and experience are granted; only the coin is owed
    return replace(result, inventory_update=unpaid, owed=owed)


def _shop_sell_result(state: Any, intent: ResourceTransferIntent, target_inventory: InventoryComponent) -> TransactionResult:
    """A sale at a shop (RPG-ECON-201): the shop pays the full price out of its own purse; the seller receives it minus the place holder's share."""
    building = state.buildings.get(intent.source_id)
    if not building or not building.functional:
        return TransactionResult(accepted=False, reason=ReasonCode.TARGET_INVALID)
    if building.inventory.gold < intent.gold_delta:
        return TransactionResult(accepted=False, reason=ReasonCode.LIQUIDITY_EXHAUSTED)
    for item in intent.items_remove:
        if sum(s.quantity for s in target_inventory.items if s.item_id == item.item_id) < item.quantity:
            return TransactionResult(accepted=False, reason=ReasonCode.INSUFFICIENT_RESOURCES)
    tax = _tax_credit(intent)
    return TransactionResult(
        accepted=True,
        inventory_update=InventoryUpdate(items_remove=intent.items_remove, gold_delta=intent.gold_delta - (tax.gold_delta if tax else 0)),
        building_update=BuildingUpdate(building_id=intent.source_id, inventory=InventoryUpdate(items_add=intent.items_remove, gold_delta=-intent.gold_delta)),
        treasury_update=tax)


def _service_result(state: Any, intent: ResourceTransferIntent, target_inventory: InventoryComponent) -> TransactionResult:
    """A paid service or fee. The payee is the service building's purse, else the treasury the intent names, else (an unnamed payee) nobody."""
    if target_inventory.gold < intent.gold_cost:
        return TransactionResult(accepted=False, reason=ReasonCode.ACTION_EXHAUSTION)
    paid = min(target_inventory.gold, max(0, intent.gold_cost - intent.gold_delta))
    credit = _service_credit(state, intent, paid)
    holder = intent.treasury_faction
    to_treasury = credit is None and holder is not None and paid > 0
    return TransactionResult(
        accepted=True,
        building_update=credit,
        treasury_update=TreasuryTransfer(faction=holder, gold_delta=int(paid)) if holder is not None and to_treasury else None,
        inventory_update=InventoryUpdate(items_add=intent.items_add, gold_delta=intent.gold_delta - intent.gold_cost),
        identity_update=intent.identity_upd, biological_update=intent.biological_upd, attributes_update=intent.attributes_upd,
        combat_update=intent.combat_upd, strategic_update=intent.strategic_upd, equipment_update=intent.equipment_upd, reward_update=intent.reward_upd)


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
        reservations: Optional[Dict[tuple[str, str|int], int]] = None,
        treasury_pending: Optional[Dict[str, float]] = None
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
        # Logic ID: TOWN-011 (Loot/harvest abort because of inventory pressure)
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
            if inventory_full and intent.items_add:
                 return TransactionResult(accepted=False, reason=ReasonCode.INVENTORY_FULL)
            ground_item = state.ground_items.get(intent.source_id)
            if not ground_item:
                return TransactionResult(accepted=False, reason=ReasonCode.SOURCE_MISSING)
            
            # P0.2 Refinement: Account for in-tick reservations
            if reservations and reservations.get(("GROUND_ITEM", intent.source_id), 0) > 0:
                return TransactionResult(accepted=False, reason=ReasonCode.TARGET_LOCKED)
            
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add, gold_delta=ground_item.gold),
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
            
            # The body's coin is the body's own (EXCH-02): the looter takes what the corpse holds, whatever the intent says.
            return TransactionResult(
                accepted=True,
                inventory_update=InventoryUpdate(items_add=intent.items_add, gold_delta=corpse.gold),
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
            return _shop_sell_result(state, intent, target_inventory)

        elif intent.source_kind == "WAGE":
            return _wage_result(state, intent, treasury_pending)

        elif intent.source_kind == "INHERIT":
            return _inherit_result(state, intent, inventory_full)

        elif intent.source_kind in ("COMBAT", "QUEST"):
            return _fund_reward(_reward_result(intent, inventory_full, reservations), intent, state, entity, treasury_pending)

        # VERIFIED v2: authoritative_side_effects
        if intent.source_kind in ("TOWN_SERVICE", "TAX", "REPAIR_FEE", "SERVICE_FEE", "INFORMATION_PURCHASE"):
             return _service_result(state, intent, target_inventory)
        
        elif intent.source_kind == "CARRIED_FOOD":
             return _carried_food_result(intent, target_inventory)

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
