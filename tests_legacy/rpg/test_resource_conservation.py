import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, ResourceNodeState, InventoryComponent, ItemStack, InteractionComponent
from src_legacy.core.updates import StateUpdate, EntityUpdate, InteractionUpdate
from src_legacy.systems.harvest_system import HarvestSystem
from src_legacy.core.items import ItemRegistry

@pytest.fixture
def base_state():
    # Setup a simple state
    node = ResourceNodeState(
        id=101,
        kind="IRON_NODE",
        position=(1, 0),
        yields_item="IRON_ORE",
        remaining_charges=5,
        max_charges=5,
        required_ticks=1
    )
    
    entity = EntityState(
        id=1,
        kind="HERO",
        position=(0, 0),
        inventory=InventoryComponent(max_slots=1, items=[]),
        interaction=InteractionComponent(target_node_id=101, progress=0),
        properties={"interaction_kind": "harvest", "harvest_duration": 1}
    )
    
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={101: node},
        terrain={(0,0): "FLOOR", (1,0): "FLOOR"}
    )

def test_harvest_full_inventory_does_not_deplete_node(base_state):
    # 1. Fill inventory
    full_inventory = InventoryComponent(max_slots=1, items=[ItemStack("WOOD", 1)])
    entity = base_state.entities[1]
    base_state.entities[1] = AuthoritativeState.readonly_view(base_state).entities[1] # Ensure not frozen for this setup
    # Wait, AuthoritativeState is frozen, but we can use replace
    from dataclasses import replace
    base_state = replace(base_state, entities={1: replace(entity, inventory=full_inventory)})
    
    # 2. Run HarvestSystem
    # Progress is 0, duration is 1, so next tick it should complete
    update = HarvestSystem.update(base_state)
    
    # Check that it RESET interaction but did NOT add inventory update
    assert 1 in update.entity_updates
    ent_upd = update.entity_updates[1]
    assert ent_upd.inventory is None
    assert ent_upd.interaction is not None
    assert ent_upd.interaction.reset is True
    
    # Check that node is NOT depleted
    assert 101 not in update.node_updates
    
    # NOW: If we apply this update, the node loses a charge but inventory skip happens
    from src_legacy.engine.apply import ApplyPath
    final_state = ApplyPath.apply_generation(base_state, update)
    
    # VIOLATION CHECK:
    # Item was NOT added
    assert len(final_state.entities[1].inventory.items) == 1
    assert final_state.entities[1].inventory.items[0].item_id == "WOOD"
    # Node was NOT depleted
    assert final_state.resource_nodes[101].remaining_charges == 5, "Node should not be depleted if item cannot be added"
