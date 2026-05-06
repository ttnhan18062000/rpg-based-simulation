from __future__ import annotations

from typing import Iterable

from src.core.state import ItemStack
from src.core.updates import EntityUpdate, StateUpdate


def item_id(value) -> str:
    return value.item_id if hasattr(value, "item_id") else value


def item_quantity(value) -> int:
    return value.quantity if hasattr(value, "quantity") else 1


def item_ids(values: Iterable) -> list[str]:
    return sorted(item_id(value) for value in values)


def expanded_item_ids(values: Iterable) -> list[str]:
    expanded: list[str] = []
    for value in values:
        expanded.extend([item_id(value)] * item_quantity(value))
    return sorted(expanded)


def assert_inventory_delta(
    entity_update: EntityUpdate,
    *,
    gold_delta: int | None = None,
    removed: list[str] | None = None,
    added: list[str] | None = None,
) -> None:
    assert entity_update.inventory is not None, "Expected an InventoryUpdate, got None"

    if gold_delta is not None:
        assert entity_update.inventory.gold_delta == gold_delta

    if removed is not None:
        assert expanded_item_ids(entity_update.inventory.items_remove) == sorted(removed)

    if added is not None:
        assert item_ids(entity_update.inventory.items_add) == sorted(added)


def assert_no_inventory_update(update: StateUpdate, entity_id: int) -> None:
    entity_update = update.entity_updates.get(entity_id)
    assert entity_update is None or entity_update.inventory is None


def entity_update(update: StateUpdate, entity_id: int) -> EntityUpdate:
    assert entity_id in update.entity_updates, f"Missing EntityUpdate for entity {entity_id}"
    return update.entity_updates[entity_id]


def assert_latest_intent_rejected(entity_update: EntityUpdate, reason=None) -> None:
    results = getattr(entity_update, "latest_intent_results", None) or []
    assert results, "Expected at least one transaction/intent result"
    assert any(not result.accepted for result in results)

    if reason is not None:
        assert any(result.reason == reason for result in results)


def assert_latest_intent_accepted(entity_update: EntityUpdate) -> None:
    results = getattr(entity_update, "latest_intent_results", None) or []
    assert results, "Expected at least one transaction/intent result"
    assert any(result.accepted for result in results)
