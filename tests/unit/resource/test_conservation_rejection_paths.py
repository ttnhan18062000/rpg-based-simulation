"""Resolver-level rejection coverage for ResourceTransactionResolver.resolve().

Production already returns accepted=False with the right ReasonCode on every path below.
These tests close a coverage gap: they pin each rejection (exact ReasonCode, no update
fields) so a regression of any rejection to acceptance fails loudly.

Source kinds in resolve() are string literals, so a coverage guard scans the resolver source
and fails when a handled kind has no rejection case in the table.

Reservation guards for QUEST, RECRUIT and CHEST are only reachable by a direct resolve() call
with a hand-built reservations dict; the apply path populates reservations for NODE,
GROUND_ITEM and CORPSE only. The resolver has no reservation guard for buildings, so no
building lock test exists.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import textwrap

import pytest

from src.core.builder import V2EntityBuilder
from src.core.conservation import ResourceTransactionResolver, TransactionResult
from src.core.enums import ReasonCode
from src.core.state import (
    AuthoritativeState,
    BuildingState,
    CorpseState,
    GroundItemState,
    InventoryComponent,
    ItemStack,
    ResourceNodeState,
)
from src.core.update_models.resources import ResourceTransferIntent

ACTOR_ID = 1
SOURCE_ID = 7
TX_ID = "tx-1"


def _actor(*, gold: int = 0, max_slots: int = 16, items: list[ItemStack] | None = None):
    return (
        V2EntityBuilder(ACTOR_ID)
        .kind("hero")
        .location(1.0, 1.0)
        .combat(alive=True, readiness=100.0)
        .inventory(gold=gold, max_slots=max_slots, items=items or [])
        .build()
    )


def _node(charges: int = 3) -> ResourceNodeState:
    return ResourceNodeState(
        id=SOURCE_ID, kind="WOOD", position=(1.0, 1.0), yields_item="wood",
        remaining_charges=charges, max_charges=5, required_ticks=1,
    )


def _ground_item() -> GroundItemState:
    return GroundItemState(id=SOURCE_ID, item_id="wood", quantity=2, position=(1.0, 1.0))


def _corpse() -> CorpseState:
    return CorpseState(
        id=SOURCE_ID, original_entity_id=50, position=(1.0, 1.0),
        items=[ItemStack("wood", 2)], decay_tick=500,
    )


def _building(*, functional: bool = True, gold: int = 0, items: list[ItemStack] | None = None) -> BuildingState:
    return BuildingState(
        id=SOURCE_ID, kind="shop", position=(1.0, 1.0), functional=functional,
        inventory=InventoryComponent(items=items or [], gold=gold),
    )


WOOD = [ItemStack("wood", 1)]


def _case(case_id, source_kind, reason, *, actor=None, state=None, intent=None, reservations=None):
    return pytest.param(
        source_kind, reason, actor or {}, state or {}, intent or {}, reservations,
        id=case_id,
    )


REJECTION_CASES = [
    _case("idempotency_node", "NODE", ReasonCode.IDEMPOTENCY_VIOLATION,
          state={"resource_nodes": {SOURCE_ID: _node()}, "processed_transaction_ids": [TX_ID]},
          intent={"transaction_id": TX_ID}),
    _case("node_inventory_full", "NODE", ReasonCode.INVENTORY_FULL,
          actor={"max_slots": 0}, state={"resource_nodes": {SOURCE_ID: _node()}},
          intent={"items_add": WOOD}),
    _case("node_missing", "NODE", ReasonCode.TARGET_INVALID),
    _case("node_depleted", "NODE", ReasonCode.SOURCE_DEPLETED,
          state={"resource_nodes": {SOURCE_ID: _node(charges=0)}}),
    _case("ground_item_inventory_full", "GROUND_ITEM", ReasonCode.INVENTORY_FULL,
          actor={"max_slots": 0}, state={"ground_items": {SOURCE_ID: _ground_item()}},
          intent={"items_add": WOOD}),
    _case("ground_item_missing", "GROUND_ITEM", ReasonCode.SOURCE_MISSING),
    _case("ground_item_locked", "GROUND_ITEM", ReasonCode.TARGET_LOCKED,
          state={"ground_items": {SOURCE_ID: _ground_item()}},
          reservations={("GROUND_ITEM", SOURCE_ID): 1}),
    _case("corpse_inventory_full", "CORPSE", ReasonCode.INVENTORY_FULL,
          actor={"max_slots": 0}, state={"corpses": {SOURCE_ID: _corpse()}},
          intent={"items_add": WOOD}),
    _case("corpse_missing", "CORPSE", ReasonCode.SOURCE_MISSING),
    _case("corpse_locked", "CORPSE", ReasonCode.TARGET_LOCKED,
          state={"corpses": {SOURCE_ID: _corpse()}},
          reservations={("CORPSE", SOURCE_ID): 1}),
    _case("crafting_inventory_full", "CRAFTING", ReasonCode.INVENTORY_FULL,
          actor={"max_slots": 0}, intent={"items_add": WOOD}),
    _case("crafting_insufficient_gold", "CRAFTING", ReasonCode.INSUFFICIENT_GOLD,
          intent={"gold_cost": 5}),
    _case("crafting_insufficient_resources", "CRAFTING", ReasonCode.INSUFFICIENT_RESOURCES,
          intent={"items_remove": [ItemStack("wood", 2)], "items_add": [ItemStack("stone", 1)]}),
    _case("shop_buy_inventory_full", "SHOP_BUY", ReasonCode.INVENTORY_FULL,
          actor={"max_slots": 0}, state={"buildings": {SOURCE_ID: _building(items=[ItemStack("wood", 5)])}},
          intent={"items_add": WOOD}),
    _case("shop_buy_building_missing", "SHOP_BUY", ReasonCode.TARGET_INVALID),
    _case("shop_buy_building_not_functional", "SHOP_BUY", ReasonCode.TARGET_INVALID,
          state={"buildings": {SOURCE_ID: _building(functional=False, items=[ItemStack("wood", 5)])}}),
    _case("shop_buy_out_of_stock", "SHOP_BUY", ReasonCode.OUT_OF_STOCK,
          state={"buildings": {SOURCE_ID: _building()}}, intent={"items_add": WOOD}),
    _case("shop_buy_insufficient_gold", "SHOP_BUY", ReasonCode.INSUFFICIENT_GOLD,
          state={"buildings": {SOURCE_ID: _building(items=[ItemStack("wood", 5)])}},
          intent={"items_add": WOOD, "gold_cost": 5}),
    _case("shop_sell_building_missing", "SHOP_SELL", ReasonCode.TARGET_INVALID),
    _case("shop_sell_building_not_functional", "SHOP_SELL", ReasonCode.TARGET_INVALID,
          state={"buildings": {SOURCE_ID: _building(functional=False, gold=100)}}),
    _case("shop_sell_liquidity_exhausted", "SHOP_SELL", ReasonCode.LIQUIDITY_EXHAUSTED,
          state={"buildings": {SOURCE_ID: _building(gold=0)}}, intent={"gold_delta": 5}),
    _case("shop_sell_insufficient_resources", "SHOP_SELL", ReasonCode.INSUFFICIENT_RESOURCES,
          state={"buildings": {SOURCE_ID: _building(gold=100)}}, intent={"items_remove": WOOD}),
    _case("combat_inventory_full", "COMBAT", ReasonCode.INVENTORY_FULL,
          actor={"max_slots": 0}, intent={"items_add": WOOD}),
    _case("quest_locked", "QUEST", ReasonCode.TARGET_LOCKED,
          reservations={("QUEST", SOURCE_ID): 1}),
    _case("quest_inventory_full", "QUEST", ReasonCode.INVENTORY_FULL,
          actor={"max_slots": 0}, intent={"items_add": WOOD}),
    _case("town_service_insufficient_gold", "TOWN_SERVICE", ReasonCode.ACTION_EXHAUSTION,
          intent={"gold_cost": 5}),
    _case("tax_insufficient_gold", "TAX", ReasonCode.ACTION_EXHAUSTION, intent={"gold_cost": 5}),
    _case("repair_fee_insufficient_gold", "REPAIR_FEE", ReasonCode.ACTION_EXHAUSTION,
          intent={"gold_cost": 5}),
    _case("service_fee_insufficient_gold", "SERVICE_FEE", ReasonCode.ACTION_EXHAUSTION,
          intent={"gold_cost": 5}),
    _case("information_purchase_insufficient_gold", "INFORMATION_PURCHASE",
          ReasonCode.ACTION_EXHAUSTION, intent={"gold_cost": 5}),
    _case("recruit_locked", "RECRUIT", ReasonCode.TARGET_LOCKED,
          reservations={("RECRUIT", SOURCE_ID): 1}),
    _case("recruit_insufficient_gold", "RECRUIT", ReasonCode.ACTION_EXHAUSTION,
          intent={"gold_cost": 5}),
    _case("chest_locked", "CHEST", ReasonCode.TARGET_LOCKED,
          reservations={("CHEST", SOURCE_ID): 1}),
    _case("chest_insufficient_gold", "CHEST", ReasonCode.ACTION_EXHAUSTION,
          intent={"gold_cost": 5}),
    _case("home_storage_withdraw_not_stored", "HOME_STORAGE", ReasonCode.ACTION_EXHAUSTION,
          intent={"items_add": WOOD}),
    _case("home_storage_deposit_no_capacity", "HOME_STORAGE", ReasonCode.INSUFFICIENT_CAPACITY,
          actor={"items": [ItemStack("wood", 1)]},
          state={"home_storage": {ACTOR_ID: InventoryComponent(max_slots=0)}},
          intent={"items_remove": WOOD}),
    _case("home_storage_deposit_not_carried", "HOME_STORAGE", ReasonCode.ACTION_EXHAUSTION,
          intent={"items_remove": WOOD}),
    _case("unknown_source_kind", "NO_SUCH_KIND", ReasonCode.UNKNOWN_SOURCE_KIND),
]

UNKNOWN_KIND = "NO_SUCH_KIND"


def _resolve(source_kind, actor_kwargs, state_kwargs, intent_kwargs, reservations):
    actor = _actor(**actor_kwargs)
    state = AuthoritativeState(tick=1, seed=42, entities={ACTOR_ID: actor}, **state_kwargs)
    intent_kwargs = {"transaction_id": TX_ID, **intent_kwargs}
    intent = ResourceTransferIntent(source_id=SOURCE_ID, source_kind=source_kind, **intent_kwargs)
    return ResourceTransactionResolver.resolve(state, actor, intent, reservations=reservations)


@pytest.mark.parametrize("source_kind,reason,actor,state,intent,reservations", REJECTION_CASES)
def test_resolver_rejection_table(source_kind, reason, actor, state, intent, reservations):
    result = _resolve(source_kind, actor, state, intent, reservations)

    assert result.accepted is False
    assert result.reason == reason
    for field in dataclasses.fields(TransactionResult):
        if field.name not in ("accepted", "reason"):
            assert getattr(result, field.name) is None, field.name


def test_idempotency_violation_resolver_level():
    """Reachable only by a direct resolve(): the apply path rejects a replayed id before it gets here."""
    result = _resolve(
        "GROUND_ITEM", {}, {"ground_items": {SOURCE_ID: _ground_item()}, "processed_transaction_ids": [TX_ID]}, {}, None,
    )

    assert result.accepted is False
    assert result.reason == ReasonCode.IDEMPOTENCY_VIOLATION


def test_unprocessed_transaction_id_is_not_an_idempotency_violation():
    state = {"ground_items": {SOURCE_ID: _ground_item()}, "processed_transaction_ids": ["other-tx"]}

    assert _resolve("GROUND_ITEM", {}, state, {}, None).accepted is True
    assert _resolve("GROUND_ITEM", {}, {"ground_items": state["ground_items"]}, {"transaction_id": None}, None).accepted is True


def _handled_source_kinds() -> set[str]:
    source = textwrap.dedent(inspect.getsource(ResourceTransactionResolver.resolve))
    kinds: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if not (isinstance(left, ast.Attribute) and left.attr == "source_kind"):
            continue
        for comparator in node.comparators:
            if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                kinds.add(comparator.value)
            elif isinstance(comparator, ast.Tuple):
                kinds.update(
                    el.value for el in comparator.elts
                    if isinstance(el, ast.Constant) and isinstance(el.value, str)
                )
    return kinds


def test_resolver_source_kind_coverage_guard():
    handled = _handled_source_kinds()
    covered = {case.values[0] for case in REJECTION_CASES}

    assert handled, "source-kind scan found nothing; the guard itself is broken"
    assert handled - covered == set(), "source kinds handled by resolve() without a rejection case"
    assert covered - handled == {UNKNOWN_KIND}


def _lock_scenario(source_kind):
    if source_kind == "GROUND_ITEM":
        return {"ground_items": {SOURCE_ID: _ground_item()}}, {}
    if source_kind == "CORPSE":
        return {"corpses": {SOURCE_ID: _corpse()}}, {}
    return {}, {}


@pytest.mark.parametrize("source_kind", ["GROUND_ITEM", "CORPSE", "QUEST", "RECRUIT", "CHEST"])
def test_target_locked_per_source_kind(source_kind):
    state, intent = _lock_scenario(source_kind)
    key = (source_kind, SOURCE_ID)

    locked = _resolve(source_kind, {}, state, intent, {key: 1})
    assert locked.accepted is False
    assert locked.reason == ReasonCode.TARGET_LOCKED

    larger_count = _resolve(source_kind, {}, state, intent, {key: 3})
    assert larger_count.accepted is False
    assert larger_count.reason == ReasonCode.TARGET_LOCKED

    other_kind = "CHEST" if source_kind != "CHEST" else "RECRUIT"
    for no_lock in (
        None,
        {},
        {key: 0},
        {(other_kind, SOURCE_ID): 1},
        {(source_kind, SOURCE_ID + 1): 1},
    ):
        result = _resolve(source_kind, {}, state, intent, no_lock)
        assert result.accepted is True, no_lock
        assert result.reason == ReasonCode.UNKNOWN
