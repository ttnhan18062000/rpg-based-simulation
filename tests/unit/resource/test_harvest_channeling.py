import pytest
from src.core.state import (
    EntityState, AuthoritativeState, ResourceNodeState, ItemStack, InteractionComponent
)
from src.core.updates import StateUpdate
from src.actions.harvest import HarvestAction
from src.systems.harvest_system import HarvestSystem
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder

@pytest.mark.v2_contract
def test_harvest_channeling_and_yield():
    # 1. Setup: Tree (Wood)
    node = ResourceNodeState(
        id=501, kind="tree", position=(0, 1), 
        yields_item="wood", remaining_charges=1, max_charges=1, 
        required_ticks=10
    )
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
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
    
    from src.engine.pipeline import AuthoritativeApplyPipeline
    refined = AuthoritativeApplyPipeline.refine(state, sys_upd)
    
    assert 501 in refined.node_updates
    state = ApplyPath.apply_generation(state, refined)
    
    # 5. Verify inventory gain
    new_ent = state.entities[1]
    # Check for wood in inventory
    wood_found = any(stack.item_id == "wood" for stack in new_ent.inventory.items)
    assert wood_found
    
    # Verify results
    assert state.resource_nodes[501].remaining_charges == 0

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
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    ent_upd = HarvestAction.start_harvest(entity, 501, state)
    assert ent_upd is None # Still 0 charges


@pytest.mark.v2_contract
def test_harvest_no_interaction_or_no_target_is_skipped():
    node = ResourceNodeState(
        id=501, kind="tree", position=(0, 1),
        yields_item="wood", remaining_charges=1, max_charges=1,
        required_ticks=10
    )
    no_interaction_entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    no_target_entity = (V2EntityBuilder(2)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=None, kind="harvest"))
        .build())
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: no_interaction_entity, 2: no_target_entity},
        resource_nodes={501: node},
    )

    sys_upd = HarvestSystem.update(state)

    assert 1 not in sys_upd.entity_updates
    assert 2 not in sys_upd.entity_updates


@pytest.mark.v2_contract
def test_harvest_skips_non_harvest_interaction_kind():
    node = ResourceNodeState(
        id=501, kind="tree", position=(0, 1),
        yields_item="wood", remaining_charges=1, max_charges=1,
        required_ticks=10
    )
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=501, kind="ground_item"))
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, resource_nodes={501: node})

    sys_upd = HarvestSystem.update(state)

    assert 1 not in sys_upd.entity_updates


@pytest.mark.v2_contract
def test_harvest_resets_on_missing_node():
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=999, kind="harvest"))
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, resource_nodes={})

    sys_upd = HarvestSystem.update(state)

    assert sys_upd.entity_updates[1].interaction.reset is True


@pytest.mark.v2_contract
def test_harvest_resets_on_depleted_node():
    node = ResourceNodeState(
        id=501, kind="tree", position=(0, 0),
        yields_item="wood", remaining_charges=0, max_charges=1,
        required_ticks=10
    )
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=501, kind="harvest"))
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, resource_nodes={501: node})

    sys_upd = HarvestSystem.update(state)

    assert sys_upd.entity_updates[1].interaction.reset is True


@pytest.mark.v2_contract
def test_harvest_resets_on_distance():
    node = ResourceNodeState(
        id=501, kind="tree", position=(0, 2),
        yields_item="wood", remaining_charges=1, max_charges=1,
        required_ticks=10
    )
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .replace_interaction(InteractionComponent(target_node_id=501, kind="harvest"))
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, resource_nodes={501: node})

    sys_upd = HarvestSystem.update(state)

    assert sys_upd.entity_updates[1].interaction.reset is True


@pytest.mark.v2_contract
@pytest.mark.skip(
    reason=(
        "harvesting.py:69-74 (the `if current_upd:` merge branch in the node-cooldown loop) is "
        "provably unreachable through a single HarvestSystem.update() call: node_updates is a "
        "local dict re-initialized empty on every call (line 12) and is only ever written by this "
        "same loop, keyed one-for-one by node.id (state.resource_nodes is Dict[int, "
        "ResourceNodeState], so each id appears at most once per call) -- current_upd can never be "
        "truthy on first encounter of a given node id. Documented per TCK-20260902-"
        "HARVEST-LOOT-TEST-COVERAGE Step 3 rather than forced via an artificial/degenerate state."
    )
)
def test_harvest_node_cooldown_merge_branch_is_unreachable():
    pass
