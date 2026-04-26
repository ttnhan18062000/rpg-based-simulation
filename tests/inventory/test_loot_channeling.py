import pytest
from src.core.state import (
    EntityState, AuthoritativeState, GroundItemState, ItemStack, InteractionComponent
)
from src.core.updates import StateUpdate
from src.actions.loot import LootAction
from src.systems.loot_system import LootSystem
from src.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_loot_channeling_completion():
    # 1. Setup: Entity near a ground item
    ground_item = GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))
    entity = EntityState(id=1, kind="hero", position=(0, 0))
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
    assert 101 in sys_upd.ground_items_remove
    assert len(sys_upd.entity_updates[1].inventory.items_add) == 1
    
    final_state = ApplyPath.apply_generation(state, sys_upd)
    
    # 5. Verify authoritative handoff
    assert 101 not in final_state.ground_items
    assert final_state.entities[1].inventory.items[0].item_id == "iron_ore"
    assert final_state.entities[1].inventory.items[0].quantity == 5

@pytest.mark.v2_contract
def test_loot_interruption_by_distance():
    ground_item = GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))
    # Start near
    entity = EntityState(id=1, kind="hero", position=(0, 0))
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
