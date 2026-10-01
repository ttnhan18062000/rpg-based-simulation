"""Apply-path coverage for rejected resource transfers.

Production already leaves a rejected transfer's transaction id out of the durable processed list
and changes no durable state. These tests close a coverage gap: a regression that reported a
rejected transfer as accepted would burn the id permanently (the id would land in
AuthoritativeState.processed_transaction_ids and every retry would be an idempotency violation)
while the entity received nothing.

Everything runs through AuthoritativeApplyPipeline.refine then ApplyPath.apply_generation; the
tests only read the outputs.
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
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
from src.core.updates import EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline

WOOD3 = [ItemStack("wood", 3)]


def _actor(eid: int, *, gold: int = 0, max_slots: int = 16, items: list[ItemStack] | None = None):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(5.0, 5.0)
        .combat(alive=True, readiness=100.0)
        .inventory(gold=gold, max_slots=max_slots, items=items or [])
        .build()
    )


def _ground_item(item_id: int) -> GroundItemState:
    return GroundItemState(id=item_id, item_id="wood", quantity=3, position=(5.0, 5.0))


def _corpse(corpse_id: int) -> CorpseState:
    return CorpseState(
        id=corpse_id, original_entity_id=50, position=(5.0, 5.0),
        items=[ItemStack("wood", 3)], decay_tick=500,
    )


def _intent(source_kind: str, source_id: int, transaction_id: str, **kwargs) -> ResourceTransferIntent:
    return ResourceTransferIntent(
        source_id=source_id, source_kind=source_kind, transaction_id=transaction_id,
        transfer_kind="LOOT", **kwargs,
    )


def _update(transfers_by_entity: dict[int, list[ResourceTransferIntent]]) -> StateUpdate:
    return StateUpdate(entity_updates={
        eid: EntityUpdate(entity_id=eid, resource_transfers=transfers)
        for eid, transfers in transfers_by_entity.items()
    })


def _run(state: AuthoritativeState, transfers_by_entity):
    refined = AuthoritativeApplyPipeline.refine(state, _update(transfers_by_entity))
    return refined, ApplyPath.apply_generation(state, refined)


def _durable_snapshot(state: AuthoritativeState) -> dict:
    return {
        "inventories": {
            eid: (tuple((s.item_id, s.quantity) for s in e.inventory.items), e.inventory.gold)
            for eid, e in state.entities.items()
        },
        "node_charges": {nid: n.remaining_charges for nid, n in state.resource_nodes.items()},
        "ground_items": {gid: (g.item_id, g.quantity) for gid, g in state.ground_items.items()},
        "corpses": {cid: tuple((s.item_id, s.quantity) for s in c.items) for cid, c in state.corpses.items()},
        "buildings": {
            bid: (tuple((s.item_id, s.quantity) for s in b.inventory.items), b.inventory.gold)
            for bid, b in state.buildings.items()
        },
        "home_storage": {
            eid: (tuple((s.item_id, s.quantity) for s in inv.items), inv.gold)
            for eid, inv in state.home_storage.items()
        },
        "processed_transaction_ids": list(state.processed_transaction_ids),
    }


def _result_for(refined: StateUpdate, entity_id: int, transaction_id: str):
    return next(r for r in refined.entity_updates[entity_id].intent_results if r.transaction_id == transaction_id)


def _contested_state() -> AuthoritativeState:
    return AuthoritativeState(
        tick=10, seed=42,
        entities={1: _actor(1), 2: _actor(2)},
        ground_items={10: _ground_item(10), 11: _ground_item(11)},
        corpses={20: _corpse(20), 21: _corpse(21)},
    )


LOCK_CASES = [
    pytest.param("GROUND_ITEM", 10, 11, id="ground_item"),
    pytest.param("CORPSE", 20, 21, id="corpse"),
]


@pytest.mark.parametrize("source_kind,contested_id,spare_id", LOCK_CASES)
def test_rejected_transfer_does_not_burn_transaction_id(source_kind, contested_id, spare_id):
    state = _contested_state()
    refined, new_state = _run(state, {
        1: [_intent(source_kind, contested_id, "winner-tx", items_add=WOOD3)],
        2: [_intent(source_kind, contested_id, "loser-tx", items_add=WOOD3)],
    })

    assert _result_for(refined, 1, "winner-tx").accepted is True
    loser = _result_for(refined, 2, "loser-tx")
    assert loser.accepted is False
    assert loser.reason == ReasonCode.TARGET_LOCKED

    assert "loser-tx" not in refined.processed_transaction_ids
    assert "loser-tx" not in new_state.processed_transaction_ids
    assert "winner-tx" in refined.processed_transaction_ids
    assert "winner-tx" in new_state.processed_transaction_ids

    retry_refined, _ = _run(new_state, {2: [_intent(source_kind, spare_id, "loser-tx", items_add=WOOD3)]})
    retry = _result_for(retry_refined, 2, "loser-tx")
    assert retry.accepted is True
    assert retry.reason != ReasonCode.IDEMPOTENCY_VIOLATION


def test_rejected_inventory_full_transfer_does_not_burn_transaction_id():
    state = AuthoritativeState(
        tick=10, seed=42,
        entities={1: _actor(1, max_slots=0), 2: _actor(2)},
        ground_items={10: _ground_item(10)},
    )
    refined, new_state = _run(state, {1: [_intent("GROUND_ITEM", 10, "full-tx", items_add=WOOD3)]})

    rejected = _result_for(refined, 1, "full-tx")
    assert rejected.accepted is False
    assert rejected.reason == ReasonCode.INVENTORY_FULL
    assert "full-tx" not in refined.processed_transaction_ids
    assert "full-tx" not in new_state.processed_transaction_ids

    retry_refined, _ = _run(new_state, {2: [_intent("GROUND_ITEM", 10, "full-tx", items_add=WOOD3)]})
    retry = _result_for(retry_refined, 2, "full-tx")
    assert retry.accepted is True
    assert retry.reason != ReasonCode.IDEMPOTENCY_VIOLATION


def _node(charges: int) -> ResourceNodeState:
    return ResourceNodeState(
        id=30, kind="WOOD", position=(5.0, 5.0), yields_item="wood",
        remaining_charges=charges, max_charges=5, required_ticks=1,
    )


def _shop(*, gold: int = 0, items: list[ItemStack] | None = None) -> BuildingState:
    return BuildingState(
        id=40, kind="shop", position=(5.0, 5.0),
        inventory=InventoryComponent(items=items or [], gold=gold),
    )


SOLE_REJECTION_CASES = [
    pytest.param(
        {"ground_items": {10: _ground_item(10)}}, {"max_slots": 0},
        _intent("GROUND_ITEM", 10, "tx", items_add=WOOD3), ReasonCode.INVENTORY_FULL,
        id="ground_item_inventory_full",
    ),
    pytest.param(
        {"corpses": {20: _corpse(20)}}, {"max_slots": 0},
        _intent("CORPSE", 20, "tx", items_add=WOOD3), ReasonCode.INVENTORY_FULL,
        id="corpse_inventory_full",
    ),
    pytest.param(
        {"resource_nodes": {30: _node(5)}}, {"max_slots": 0},
        _intent("NODE", 30, "tx", items_add=[ItemStack("wood", 1)]), ReasonCode.INVENTORY_FULL,
        id="node_inventory_full",
    ),
    pytest.param(
        {"resource_nodes": {30: _node(0)}}, {},
        _intent("NODE", 30, "tx", items_add=[ItemStack("wood", 1)]), ReasonCode.SOURCE_DEPLETED,
        id="node_depleted",
    ),
    pytest.param(
        {}, {},
        _intent("GROUND_ITEM", 10, "tx", items_add=WOOD3), ReasonCode.SOURCE_MISSING,
        id="ground_item_missing",
    ),
    pytest.param(
        {}, {"gold": 1},
        _intent("CRAFTING", 0, "tx", items_add=[ItemStack("stone", 1)], gold_cost=5), ReasonCode.INSUFFICIENT_GOLD,
        id="crafting_insufficient_gold",
    ),
    pytest.param(
        {"buildings": {40: _shop()}}, {"gold": 100},
        _intent("SHOP_BUY", 40, "tx", items_add=WOOD3, gold_cost=5), ReasonCode.OUT_OF_STOCK,
        id="shop_buy_out_of_stock",
    ),
    pytest.param(
        {"buildings": {40: _shop(gold=0)}}, {"items": [ItemStack("wood", 3)]},
        _intent("SHOP_SELL", 40, "tx", items_remove=WOOD3, gold_delta=5), ReasonCode.LIQUIDITY_EXHAUSTED,
        id="shop_sell_liquidity_exhausted",
    ),
    pytest.param(
        {"home_storage": {1: InventoryComponent(max_slots=0)}}, {"items": [ItemStack("wood", 3)]},
        _intent("HOME_STORAGE", 1, "tx", items_remove=WOOD3), ReasonCode.INSUFFICIENT_CAPACITY,
        id="home_storage_deposit_no_capacity",
    ),
]


@pytest.mark.parametrize("world,actor_kwargs,intent,reason", SOLE_REJECTION_CASES)
def test_rejected_transfer_zero_durable_change(world, actor_kwargs, intent, reason):
    state = AuthoritativeState(
        tick=10, seed=42,
        entities={1: _actor(1, **actor_kwargs)},
        **world,
    )
    before = _durable_snapshot(state)

    refined, new_state = _run(state, {1: [intent]})

    result = _result_for(refined, 1, "tx")
    assert result.accepted is False
    assert result.reason == reason

    assert refined.ground_items_remove == []
    assert refined.corpses_remove == []
    assert refined.node_updates == {}
    assert refined.building_updates == {}
    assert refined.home_storage_updates == {}
    assert refined.processed_transaction_ids == []
    assert refined.entity_updates[1].inventory is None

    assert _durable_snapshot(new_state) == before


def test_lock_loser_causes_no_durable_change_of_its_own():
    state = _contested_state()
    refined, new_state = _run(state, {
        1: [_intent("GROUND_ITEM", 10, "winner-tx", items_add=WOOD3)],
        2: [_intent("GROUND_ITEM", 10, "loser-tx", items_add=WOOD3)],
    })

    assert refined.entity_updates[2].inventory is None
    assert refined.ground_items_remove == [10]
    assert refined.processed_transaction_ids == ["winner-tx"]

    assert new_state.entities[2].inventory == state.entities[2].inventory
    assert new_state.ground_items.keys() == {11}
    assert new_state.corpses.keys() == state.corpses.keys()


def test_grouped_rejection_rolls_back_without_burning_ids():
    state = AuthoritativeState(
        tick=10, seed=42,
        entities={1: _actor(1, gold=1), 2: _actor(2)},
        ground_items={10: _ground_item(10)},
    )
    group = [
        ResourceTransferIntent(
            source_id=10, source_kind="GROUND_ITEM", transaction_id="group-loot-tx",
            transfer_kind="LOOT", items_add=WOOD3, group_id="g1",
        ),
        ResourceTransferIntent(
            source_id=0, source_kind="CRAFTING", transaction_id="group-craft-tx",
            transfer_kind="CRAFT", items_add=[ItemStack("stone", 1)], gold_cost=5, group_id="g1",
        ),
    ]
    refined, new_state = _run(state, {1: group, 2: [_intent("GROUND_ITEM", 10, "bystander-tx", items_add=WOOD3)]})

    assert _result_for(refined, 1, "group-loot-tx").accepted is False
    assert _result_for(refined, 1, "group-loot-tx").reason == ReasonCode.GROUP_ROLLBACK
    assert _result_for(refined, 1, "group-craft-tx").accepted is False
    assert _result_for(refined, 1, "group-craft-tx").reason == ReasonCode.INSUFFICIENT_GOLD

    for tx in ("group-loot-tx", "group-craft-tx"):
        assert tx not in refined.processed_transaction_ids
        assert tx not in new_state.processed_transaction_ids
    assert new_state.entities[1].inventory == state.entities[1].inventory

    bystander = _result_for(refined, 2, "bystander-tx")
    assert bystander.accepted is True
    assert refined.ground_items_remove == [10]
    assert 10 not in new_state.ground_items
    assert [(s.item_id, s.quantity) for s in new_state.entities[2].inventory.items] == [("wood", 3)]
