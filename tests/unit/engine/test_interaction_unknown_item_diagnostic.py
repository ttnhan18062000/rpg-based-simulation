"""Interaction rejections caused by an unknown item id are surfaced, not silent.

`InventoryService.can_add_items` returns False for an unknown item id AND for lack of capacity.
The unknown-id case is a content defect; `InteractionSystem.enforce` records it through the
authoritative rejection audit (counter + typed event) while keeping the non-fatal reset.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.inventory import InventoryService
from src.core.state import AuthoritativeState, InteractionComponent, ItemStack, ResourceNodeState
from src.core.updates import EntityUpdate, InteractionUpdate, StateUpdate
from src.engine.interaction import UNKNOWN_ITEM_REJECTION_KEY, InteractionSystem


def _state(yields_item: str, *, max_weight: float | None = None) -> AuthoritativeState:
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    entity = replace(entity, interaction=InteractionComponent(progress=0, target_node_id=10))
    if max_weight is not None:
        entity = replace(entity, inventory=replace(entity.inventory, max_weight=max_weight))
    node = ResourceNodeState(id=10, kind="k", position=(0, 0), yields_item=yields_item,
                             remaining_charges=1, max_charges=1, required_ticks=1)
    return AuthoritativeState(tick=7, seed=42, entities={1: entity}, resource_nodes={10: node})


def _harvest_update() -> StateUpdate:
    return StateUpdate(entity_updates={1: EntityUpdate(
        entity_id=1, interaction=InteractionUpdate(progress_delta=1.0, target_node_id=10))})


def test_unknown_item_id_is_recorded_and_still_non_fatal():
    refined = InteractionSystem.enforce(_state("herb_patch"), _harvest_update())

    assert refined.entity_updates[1].interaction.reset is True  # non-fatal reset preserved
    assert refined.rejections_delta == {UNKNOWN_ITEM_REJECTION_KEY: 1}
    (event,) = refined.rejection_events
    assert (event.tick, event.actor_id, event.reason, event.target_id) == (7, 1, ReasonCode.UNKNOWN_ITEM, 10)


def test_capacity_rejection_is_not_reported_as_unknown_item():
    refined = InteractionSystem.enforce(_state("iron_ore", max_weight=0.5), _harvest_update())

    assert refined.entity_updates[1].interaction.reset is True
    assert UNKNOWN_ITEM_REJECTION_KEY not in refined.rejections_delta
    assert not refined.rejection_events


def test_successful_harvest_records_nothing():
    refined = InteractionSystem.enforce(_state("herb"), _harvest_update())

    (intent,) = refined.entity_updates[1].resource_transfers  # the harvest completed
    assert [i.item_id for i in intent.items_add] == ["herb"]
    assert not refined.rejections_delta
    assert not refined.rejection_events


def test_enforce_is_pure_and_deterministic():
    state = _state("herb_patch")
    before = (dict(state.entities), dict(state.resource_nodes), dict(state.rejection_registry))
    first = InteractionSystem.enforce(state, _harvest_update())
    second = InteractionSystem.enforce(state, _harvest_update())

    assert (dict(state.entities), dict(state.resource_nodes), dict(state.rejection_registry)) == before
    assert first.rejections_delta == second.rejections_delta
    assert first.rejection_events == second.rejection_events


def test_unknown_item_ids_helper():
    stacks = [ItemStack("herb", 1), ItemStack("herb_patch", 1), ItemStack("herb_patch", 2), ItemStack("nope", 1)]
    assert InventoryService.unknown_item_ids(stacks) == ["herb_patch", "nope"]
    assert InventoryService.unknown_item_ids([ItemStack("herb", 1)]) == []
