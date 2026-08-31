"""Tests for TCK-20260831-ITEM-INSTANCE-HISTORY.

Covers: the new ItemInstance typed model/state location, ItemInstanceService's stateful
per-tick id allocation (Finding 2 fix), StateUpdate.merge_many's extension for the three new
item_instance* fields (Finding 1 fix), the append-only owner_history transfer through
ApplyPath.apply_generation, and re-verification that TOWN-128 (item_id/kind identity) is
unaffected by ItemInstance's addition.
"""
import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.items import ItemRegistry
from src.core.state import (
    AuthoritativeState, ItemStack, ItemKind, ItemInstance, AcquiredMethod,
)
from src.core.updates import StateUpdate, EntityUpdate
from src.core.update_models.inventory import InventoryUpdate, ItemInstanceUpdate
from src.core.inventory import ItemInstanceService
from src.engine.apply import ApplyPath


def test_item_instance_typed_state_location_not_untyped_dict():
    inst = ItemInstance(
        instance_id=1,
        item_id="iron_sword",
        owner_history=["1"],
        acquired_tick=1,
        acquired_method=AcquiredMethod.LOOT,
    )
    state = AuthoritativeState(tick=1, seed=1, item_instances={1: inst})

    assert isinstance(state.item_instances, dict)
    assert isinstance(state.item_instances[1], ItemInstance)
    assert all(isinstance(k, int) for k in state.item_instances.keys())

    # Not stored in ItemStack.properties or any other untyped dict.
    stack = ItemStack("iron_sword", 1)
    assert stack.properties == {}
    item_stack_field_names = {f.name for f in dataclasses.fields(ItemStack)}
    assert "instance_id" not in item_stack_field_names
    assert "owner_history" not in item_stack_field_names
    assert "acquired_method" not in item_stack_field_names


def test_only_significant_items_receive_item_instance():
    # Default OFF: even significant=True mints nothing and consumes no id.
    state_off = AuthoritativeState(tick=1, seed=1)
    svc_off = ItemInstanceService(state_off)
    result_off = svc_off.maybe_create_instance(
        "iron_sword", True, 1, 1, AcquiredMethod.LOOT, state_off
    )
    assert result_off is None
    assert svc_off.last_id == 0

    state_on = AuthoritativeState(
        tick=1, seed=1, feature_flags={"ENABLE_ITEM_INSTANCE_HISTORY": "ON"}
    )
    svc_on = ItemInstanceService(state_on)

    # significant=False: ordinary ItemStack path, unaffected, even with flag ON.
    result_not_significant = svc_on.maybe_create_instance(
        "iron_sword", False, 1, 1, AcquiredMethod.LOOT, state_on
    )
    assert result_not_significant is None
    assert svc_on.last_id == 0

    result_significant = svc_on.maybe_create_instance(
        "iron_sword", True, 1, 1, AcquiredMethod.LOOT, state_on
    )
    assert isinstance(result_significant, ItemInstance)
    assert result_significant.instance_id == 1
    assert result_significant.owner_history == ["1"]


def test_significant_item_merge_does_not_collapse_instances():
    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .inventory(items=[])
        .build()
    )
    prior_state = AuthoritativeState(
        tick=1, seed=1, entities={1: entity},
        feature_flags={"ENABLE_ITEM_INSTANCE_HISTORY": "ON"},
    )
    svc = ItemInstanceService(prior_state)
    inst_1 = svc.maybe_create_instance("iron_ore", True, 1, 1, AcquiredMethod.LOOT, prior_state)
    inst_2 = svc.maybe_create_instance("iron_ore", True, 1, 1, AcquiredMethod.LOOT, prior_state)
    assert inst_1.instance_id != inst_2.instance_id

    ent_upd = EntityUpdate(
        entity_id=1,
        inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 1), ItemStack("iron_ore", 1)]),
    )
    state_upd = StateUpdate(
        entity_updates={1: ent_upd},
        item_instances_add_or_update=[inst_1, inst_2],
        next_item_instance_id_set=svc.last_id + 1,
    )
    new_state = ApplyPath.apply_generation(prior_state, state_upd)

    # ItemStack side: the two same-item_id additions merge into a single stack of quantity 2 --
    # InventoryService.apply_update's existing merge-by-item_id path is untouched.
    stacks = new_state.entities[1].inventory.items
    assert len(stacks) == 1
    assert stacks[0].item_id == "iron_ore"
    assert stacks[0].quantity == 2

    # ItemInstance side: the two minted instances remain distinct, un-collapsed records.
    assert len(new_state.item_instances) == 2
    assert new_state.item_instances[inst_1.instance_id].instance_id == inst_1.instance_id
    assert new_state.item_instances[inst_2.instance_id].instance_id == inst_2.instance_id


def test_transfer_significant_item_appends_owner_history_via_apply_pipeline():
    state = AuthoritativeState(
        tick=1, seed=1, feature_flags={"ENABLE_ITEM_INSTANCE_HISTORY": "ON"}
    )
    svc = ItemInstanceService(state)
    inst = svc.maybe_create_instance("iron_sword", True, 1, 1, AcquiredMethod.LOOT, state)

    add_update = StateUpdate(
        item_instances_add_or_update=[inst],
        next_item_instance_id_set=svc.last_id + 1,
    )
    state_after_mint = ApplyPath.apply_generation(state, add_update)
    assert state_after_mint.item_instances[inst.instance_id].owner_history == ["1"]

    transfer_update = StateUpdate(
        item_instance_updates={
            inst.instance_id: ItemInstanceUpdate(instance_id=inst.instance_id, owner_history_append="2")
        }
    )
    state_after_transfer = ApplyPath.apply_generation(state_after_mint, transfer_update)

    # Append-only: prior owner is retained, new owner appended.
    assert state_after_transfer.item_instances[inst.instance_id].owner_history == ["1", "2"]


def test_item_instance_id_generation_is_deterministic():
    state = AuthoritativeState(
        tick=1, seed=1, feature_flags={"ENABLE_ITEM_INSTANCE_HISTORY": "ON"}
    )

    # Replay determinism: identical inputs from an identical prior state produce the same id.
    svc_a = ItemInstanceService(state)
    result_a = svc_a.maybe_create_instance("iron_sword", True, 1, 1, AcquiredMethod.LOOT, state)
    svc_b = ItemInstanceService(state)
    result_b = svc_b.maybe_create_instance("iron_sword", True, 1, 1, AcquiredMethod.LOOT, state)
    assert result_a.instance_id == result_b.instance_id

    # Finding 2 fix: two mints within the same tick, on the same ItemInstanceService instance,
    # never collide -- distinct, sequentially-incrementing instance_ids.
    svc_c = ItemInstanceService(state)
    inst_1 = svc_c.maybe_create_instance("iron_sword", True, 1, 1, AcquiredMethod.LOOT, state)
    inst_2 = svc_c.maybe_create_instance("steel_sword", True, 1, 1, AcquiredMethod.LOOT, state)
    assert inst_1.instance_id != inst_2.instance_id
    assert inst_2.instance_id == inst_1.instance_id + 1


def test_significance_flag_requires_explicit_caller_input():
    state = AuthoritativeState(
        tick=1, seed=1, feature_flags={"ENABLE_ITEM_INSTANCE_HISTORY": "ON"}
    )
    svc = ItemInstanceService(state)

    # `significant` has no default -- omitting it is a TypeError, not a silent True/False.
    with pytest.raises(TypeError):
        svc.maybe_create_instance(
            item_id="iron_sword", owner_entity_id=1, tick=1,
            acquired_method=AcquiredMethod.LOOT, state=state,
        )

    # No auto-classifier: an item with no rarity/value signal still requires an explicit flag.
    result = svc.maybe_create_instance("iron_sword", False, 1, 1, AcquiredMethod.LOOT, state)
    assert result is None
    assert svc.last_id == 0


def test_item_instance_update_merge_many_single_transfer_per_tick_contract():
    # Common case: different instance_ids in the same tick both survive the merge (Finding 1 fix
    # -- before it, merge_many's replace(...) call did not list these fields at all and would
    # have silently dropped both).
    update_a = StateUpdate(
        item_instance_updates={1: ItemInstanceUpdate(instance_id=1, owner_history_append="a")}
    )
    update_b = StateUpdate(
        item_instance_updates={2: ItemInstanceUpdate(instance_id=2, owner_history_append="b")}
    )
    merged = update_a.merge_many([update_b])
    assert merged.item_instance_updates[1].owner_history_append == "a"
    assert merged.item_instance_updates[2].owner_history_append == "b"

    # Documented boundary: two updates for the SAME instance_id in the same tick -- plain
    # last-write-wins overwrite, not a combine. Only the second survives.
    update_c = StateUpdate(
        item_instance_updates={1: ItemInstanceUpdate(instance_id=1, owner_history_append="first")}
    )
    update_d = StateUpdate(
        item_instance_updates={1: ItemInstanceUpdate(instance_id=1, owner_history_append="second")}
    )
    merged_same_id = update_c.merge_many([update_d])
    assert merged_same_id.item_instance_updates[1].owner_history_append == "second"
    assert len(merged_same_id.item_instance_updates) == 1


def test_town_128_item_kind_identity_unaffected_by_item_instance():
    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .inventory(items=[])
        .build()
    )
    state = AuthoritativeState(
        tick=1, seed=1, entities={1: entity},
        feature_flags={"ENABLE_ITEM_INSTANCE_HISTORY": "ON"},
    )
    svc = ItemInstanceService(state)
    inst = svc.maybe_create_instance("iron_sword", True, 1, 1, AcquiredMethod.LOOT, state)

    ent_upd = EntityUpdate(
        entity_id=1,
        inventory=InventoryUpdate(items_add=[ItemStack("iron_sword", 1)]),
    )
    state_upd = StateUpdate(
        entity_updates={1: ent_upd},
        item_instances_add_or_update=[inst],
        next_item_instance_id_set=svc.last_id + 1,
    )
    new_state = ApplyPath.apply_generation(state, state_upd)

    stack = new_state.entities[1].inventory.items[0]
    assert stack.item_id == "iron_sword"
    defn = ItemRegistry.get(stack.item_id)
    assert defn.kind == ItemKind.WEAPON

    # ItemInstance is a strictly additive sidecar -- the underlying ItemStack's item_id/kind
    # identity (TOWN-128) is untouched; the sidecar records the same identity, not a divergent one.
    minted = new_state.item_instances[inst.instance_id]
    assert minted.item_id == stack.item_id
    assert ItemRegistry.get(minted.item_id).kind == defn.kind
