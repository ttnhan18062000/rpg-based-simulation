import pytest
from src.core.state import (
    EntityState, AuthoritativeState, GroundItemState, CorpseState, ItemStack, InteractionComponent
)
from src.core.updates import StateUpdate
from src.actions.loot import LootAction
from src.systems.loot_system import LootSystem
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder

@pytest.mark.v2_contract
def test_loot_channeling_completion():
    # 1. Setup: Entity near a ground item
    ground_item = GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, ground_items={101: ground_item})
    
    # 2. Action: Start loot
    ent_upd = LootAction.start_loot(entity, 101, "ground_item", state)
    assert ent_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: ent_upd}))
    
    # 3. Progress for 9 ticks
    for _ in range(9):
        sys_upd = LootSystem.update(state)
        # Should not have completed yet
        assert len(sys_upd.ground_items_remove) == 0
        state = ApplyPath.apply_generation(state, sys_upd)
        
    # 4. Final tick (10th)
    sys_upd = LootSystem.update(state)
    
    from src.engine.pipeline import AuthoritativeApplyPipeline
    refined = AuthoritativeApplyPipeline.refine(state, sys_upd)
    
    assert 101 in refined.ground_items_remove
    state = ApplyPath.apply_generation(state, refined)
    
    # 5. Verify results
    assert 101 not in state.ground_items
    new_ent = state.entities[1]
    ore_found = any(stack.item_id == "iron_ore" and stack.quantity == 5 for stack in new_ent.inventory.items)
    assert ore_found

@pytest.mark.v2_contract
def test_loot_interruption_by_distance():
    ground_item = GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))
    # Start near
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, ground_items={101: ground_item})
    
    ent_upd = LootAction.start_loot(entity, 101, "ground_item", state)
    assert ent_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: ent_upd}))
    
    # Move away in tick 2
    from src.core.updates import EntityUpdate
    move_upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, new_position=(10, 10))})
    state = ApplyPath.apply_generation(state, move_upd)
    
    # System update should detect distance and reset interaction
    sys_upd = LootSystem.update(state)
    assert sys_upd.entity_updates[1].interaction.reset == True
    
    final_state = ApplyPath.apply_generation(state, sys_upd)
    assert final_state.entities[1].interaction.target_node_id is None
    assert 101 in final_state.ground_items # Item still there


@pytest.mark.v2_contract
def test_loot_no_interaction_or_no_target_is_skipped():
    ground_item = GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))
    no_interaction_entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    no_target_entity = (V2EntityBuilder(2)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=None, kind="ground_item"))
        .build())
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: no_interaction_entity, 2: no_target_entity},
        ground_items={101: ground_item},
    )

    sys_upd = LootSystem.update(state)

    assert 1 not in sys_upd.entity_updates
    assert 2 not in sys_upd.entity_updates


@pytest.mark.v2_contract
def test_loot_skips_non_lootable_interaction_kind():
    ground_item = GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=101, kind="harvest"))
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, ground_items={101: ground_item})

    sys_upd = LootSystem.update(state)

    assert 1 not in sys_upd.entity_updates


@pytest.mark.v2_contract
def test_loot_corpse_completion_transfers_all_item_stacks():
    # 1. Setup: Entity near a corpse with two distinct item stacks
    corpse = CorpseState(
        id=301, original_entity_id=999, position=(0, 1),
        items=[ItemStack("iron_ore", 3), ItemStack("wood", 2)],
        decay_tick=1000,
    )
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, corpses={301: corpse})

    # 2. Action: Start loot
    ent_upd = LootAction.start_loot(entity, 301, "corpse", state)
    assert ent_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: ent_upd}))

    # 3. Progress for 9 ticks
    for _ in range(9):
        sys_upd = LootSystem.update(state)
        assert len(sys_upd.corpses_remove) == 0
        state = ApplyPath.apply_generation(state, sys_upd)

    # 4. Final tick (10th) -- assert directly on the raw sys_upd first
    sys_upd = LootSystem.update(state)
    transfer = sys_upd.entity_updates[1].resource_transfers[0]
    assert transfer.source_kind == "CORPSE"
    assert transfer.items_add == [ItemStack("iron_ore", 3), ItemStack("wood", 2)]

    # 5. Then run it through the authoritative apply path and assert post-refine() state
    from src.engine.pipeline import AuthoritativeApplyPipeline
    refined = AuthoritativeApplyPipeline.refine(state, sys_upd)

    assert 301 in refined.corpses_remove
    state = ApplyPath.apply_generation(state, refined)

    assert 301 not in state.corpses
    new_ent = state.entities[1]
    iron_found = any(stack.item_id == "iron_ore" and stack.quantity == 3 for stack in new_ent.inventory.items)
    wood_found = any(stack.item_id == "wood" and stack.quantity == 2 for stack in new_ent.inventory.items)
    assert iron_found
    assert wood_found


@pytest.mark.v2_contract
def test_loot_resets_on_ground_item_gone():
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=999, kind="ground_item"))
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, ground_items={})

    sys_upd = LootSystem.update(state)

    assert sys_upd.entity_updates[1].interaction.reset is True


@pytest.mark.v2_contract
def test_loot_resets_on_corpse_gone():
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=999, kind="corpse"))
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, corpses={})

    sys_upd = LootSystem.update(state)

    assert sys_upd.entity_updates[1].interaction.reset is True


@pytest.mark.v2_contract
def test_loot_corpse_interruption_by_distance():
    corpse = CorpseState(
        id=301, original_entity_id=999, position=(0, 1),
        items=[ItemStack("iron_ore", 3)],
        decay_tick=1000,
    )
    # Start near
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, corpses={301: corpse})

    ent_upd = LootAction.start_loot(entity, 301, "corpse", state)
    assert ent_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: ent_upd}))

    # Move away in tick 2
    from src.core.updates import EntityUpdate
    move_upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, new_position=(10, 10))})
    state = ApplyPath.apply_generation(state, move_upd)

    # System update should detect distance and reset interaction
    sys_upd = LootSystem.update(state)
    assert sys_upd.entity_updates[1].interaction.reset == True

    final_state = ApplyPath.apply_generation(state, sys_upd)
    assert final_state.entities[1].interaction.target_node_id is None
    assert 301 in final_state.corpses # Corpse still there
