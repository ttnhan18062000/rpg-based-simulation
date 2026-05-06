import pytest
from src.core.state import AuthoritativeState, EntityState, ResourceNodeState, InventoryComponent, ItemStack, InteractionComponent, IdentityComponent, CombatComponent, NavigationComponent
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, ResourceTransferIntent
from src.systems.harvest_system import HarvestSystem
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.enums import EntityRole, Faction

@pytest.fixture
def base_state():
    # Setup a simple state
    node = ResourceNodeState(
        id=101,
        kind="IRON_NODE",
        position=(1, 0),
        yields_item="iron_ore", # Use lowercase as in registry
        remaining_charges=5,
        max_charges=5,
        required_ticks=1
    )
    
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(0, 0)
        .with_class("HERO")
        .combat(hp=100, max_hp=100)
        .inventory(max_slots=1)
        .with_interaction(target_id=101, progress=0)
        .with_properties({"interaction_kind": "harvest", "harvest_duration": 1})
        .build()
    )
    
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={101: node},
        terrain={(0,0): "FLOOR", (1,0): "FLOOR"}
    )

def test_harvest_full_inventory_does_not_deplete_node_v2(base_state):
    # 1. Fill inventory
    # Hero has max_slots=1. Give them 1 WOOD.
    full_inventory = InventoryComponent(max_slots=1, max_weight=100, items=[ItemStack("WOOD", 1)])
    entity = base_state.entities[1]
    from dataclasses import replace
    state = replace(base_state, entities={1: replace(entity, inventory=full_inventory)})
    
    # 2. Run HarvestSystem
    state.entities[1] = replace(state.entities[1], interaction=InteractionComponent(target_node_id=101, progress=0))
    raw_update = HarvestSystem.update(state)
    
    # 3. Refine the update
    refined_update = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # 4. Apply the update
    final_state = ApplyPath.apply_generation(state, refined_update)
    
    # PROOF OF LAW:
    # 1. Item was NOT added
    assert len(final_state.entities[1].inventory.items) == 1
    assert final_state.entities[1].inventory.items[0].item_id == "WOOD"
    
    # 2. Node was NOT depleted
    assert final_state.resource_nodes[101].remaining_charges == 5, "Node should not be depleted if item cannot be added"
