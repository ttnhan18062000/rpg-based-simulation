"""A chosen sale at a shop (EXCH-02, owner decision 34; EXCH-01 price through MarketSystem, Bible 03 section 4).

Selling is a decision (AGENCY-01), not something that happens to whoever stands beside a shop: a subject whose task is the SELL step
(``ai/goals/opening_steps.py``) arrives at a shop and its SELL action turns the goods it can spare into one conserving ``SHOP_SELL`` transfer.
The shop pays out of its own purse (the resolver debits the building), so a sale never exceeds the purse: units are sold only while the
purse covers their price. One price law: ``MarketSystem.calculate_price(is_buy=False)`` per UNIT, times the quantity.

What a subject can spare: the listed gathered materials; the last unit of a weapon or armor stack and any item an equipment slot names
stay with its owner (equipment is proposed from the inventory, so the stack IS the equipped item); food only as SURPLUS: at least one meal's
worth stays (``FOOD_KEPT_HUNGER_RECOVERY``) and the rest may be sold.
"""
from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

from src.core.items import ItemRegistry, food_hunger_recovery
from src.core.models.inventory import ItemKind, ItemStack
from src.core.updates import ResourceTransferIntent
from src.engine.serves import serves
from src.engine.shop import shop_price

# The gathered materials a shop buys (the old auto-sell list).
SELLABLE_MATERIALS = ("wood", "ore", "iron_ore", "fish", "leather", "fiber", "herb", "iron_sword")
# Food a subject keeps for itself: enough to clear a hungry stomach once (2 berries of 30 hunger each).
FOOD_KEPT_HUNGER_RECOVERY = 60.0


def spare_quantity(entity: Any, item: Any) -> int:
    """How many units of one inventory stack the subject can spare for sale."""
    item_id = item.item_id if hasattr(item, "item_id") else item
    held = item.quantity if hasattr(item, "quantity") else 1
    recovery = food_hunger_recovery(item_id)
    if recovery > 0.0:
        return max(0, held - math.ceil(FOOD_KEPT_HUNGER_RECOVERY / recovery))
    if item_id.lower() not in SELLABLE_MATERIALS:
        return 0
    definition = ItemRegistry.get(item_id)
    keeps_one = (definition is not None and definition.kind in (ItemKind.WEAPON, ItemKind.ARMOR)) or item_id in entity.equipment.slots.values()
    return held - 1 if keeps_one else held


def unit_price(state: Any, shop: Any, item_id: str) -> int:
    """What the shop pays for one unit: MarketSystem's price law (base x region x building x the sell factor)."""
    return shop_price(state, shop, item_id, is_buy=False)


def plan_sale(state: Any, entity: Any, shop: Any) -> Optional[ResourceTransferIntent]:
    """The one conserving sale intent for what `entity` can spare at `shop`, or None when nothing sells (nothing spare, or the purse is
    below every unit's price). Units are taken stack by stack while the shop's purse covers their price."""
    purse = int(shop.inventory.gold)
    stacks: List[ItemStack] = []
    total = 0
    for item in entity.inventory.items:
        spare = spare_quantity(entity, item)
        price = unit_price(state, shop, item.item_id) if spare > 0 else 0
        units = min(spare, purse // price) if price > 0 else 0
        if units > 0:
            stacks.append(ItemStack(item.item_id, units))
            total += units * price
            purse -= units * price
    if not stacks:
        return None
    return ResourceTransferIntent(source_id=shop.id, source_kind="SHOP_SELL", items_remove=stacks, gold_delta=total,
                                  price_multiplier=1.0, transfer_kind="SELL")


def nearest_sale(state: Any, entity: Any) -> Optional[Tuple[Any, ResourceTransferIntent]]:
    """(shop, sale) for the nearest functional shop that would buy something from `entity`, or None."""
    px, py = entity.navigation.position
    best: Optional[Tuple[float, int, Any, ResourceTransferIntent]] = None
    for shop in state.buildings.values():
        if shop.kind != "shop" or not shop.functional or not serves(state, entity, shop):
            continue
        sale = plan_sale(state, entity, shop)
        if sale is None:
            continue
        key = (abs(shop.position[0] - px) + abs(shop.position[1] - py), shop.id)
        if best is None or key < best[:2]:
            best = (key[0], key[1], shop, sale)
    return None if best is None else (best[2], best[3])
