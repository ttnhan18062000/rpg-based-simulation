import pytest
from src_legacy.core.state import (
    EntityState, AuthoritativeState, ResourceNodeState, ItemStack
)
from src_legacy.core.updates import StateUpdate
from src_legacy.actions.harvest import HarvestAction
from src_legacy.systems.harvest_system import HarvestSystem
from src_legacy.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_harvest_channeling_and_yield():
    # 1. Setup: Tree (Wood)
    node = ResourceNodeState(
        id=501, kind="tree", position=(0, 1), 
        yields_item="wood", remaining_charges=1, max_charges=1, 
        required_ticks=10
    )
    entity = EntityState(id=1, kind="hero", position=(0, 0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, resource_nodes={501: node})
    
    # 2. Action: Start harvest
    ent_upd = HarvestAction.start_harvest(entity, 501, state)
    assert ent_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: ent_upd}))
    
    # 3. Progress for 9 ticks
    for _ in range(9):
        sys_upd = HarvestSystem.update(state)
        assert len(sys_upd.node_updates) == 0 # No depletion yet
        state = ApplyPath.apply_generation(state, sys_upd)
        
    # 4. Final tick (10th)
    sys_upd = HarvestSystem.update(state)
    assert 501 in sys_upd.node_updates
    assert sys_upd.node_updates[501].charges_delta == -1
    assert len(sys_upd.entity_updates[1].inventory.items_add) == 1
    
    final_state = ApplyPath.apply_generation(state, sys_upd)
    
    # 5. Verify results
    assert final_state.resource_nodes[501].remaining_charges == 0
    assert final_state.entities[1].inventory.items[0].item_id == "wood"

@pytest.mark.v2_contract
def test_harvest_node_cooldown():
    # Setup: Node with 0 charges and active cooldown
    node = ResourceNodeState(
        id=501, kind="tree", position=(0, 1), 
        yields_item="wood", remaining_charges=0, max_charges=1, 
        required_ticks=10, respawn_cooldown=100, cooldown_remaining=1
    )
    state = AuthoritativeState(tick=1, seed=42, resource_nodes={501: node})
    
    # 1. System update should decrement cooldown
    sys_upd = HarvestSystem.update(state)
    assert sys_upd.node_updates[501].cooldown_set == 0
    
    state = ApplyPath.apply_generation(state, sys_upd)
    assert state.resource_nodes[501].cooldown_remaining == 0
    
    # 2. Action: Should now be able to start harvest if charges were > 0 
    # (Charges don't automatically refill in M3 system, but Action check works)
    entity = EntityState(id=1, kind="hero", position=(0, 0))
    ent_upd = HarvestAction.start_harvest(entity, 501, state)
    assert ent_upd is None # Still 0 charges
