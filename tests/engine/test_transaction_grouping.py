import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, ItemStack, InventoryComponent
from src.core.updates import EntityUpdate, StateUpdate, ResourceTransferIntent
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole

@pytest.fixture
def base_entity():
    return V2EntityBuilder(entity_id=1).role(EntityRole.HERO).build()

def test_atomic_group_success(base_entity):
    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=101, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=1)
    node2 = ResourceNodeState(id=102, kind="ore", position=(0,0), yields_item="iron_ore", remaining_charges=3, max_charges=3, required_ticks=1)
    
    state = AuthoritativeState(tick=0, seed=123, entities={base_entity.id: base_entity}, resource_nodes={101: node1, 102: node2})
    
    # Two intents in the same group
    intent1 = ResourceTransferIntent(
        source_id=101, source_kind="NODE",
        items_add=[ItemStack("herb", 1)],
        group_id="batch1", is_group_required=True
    )
    intent2 = ResourceTransferIntent(
        source_id=102, source_kind="NODE",
        items_add=[ItemStack("iron_ore", 1)],
        group_id="batch1", is_group_required=True
    )
    
    update = StateUpdate(entity_updates={
        base_entity.id: EntityUpdate(entity_id=base_entity.id, resource_transfers=[intent1, intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Both should be in inventory items_add
    ent_upd = refined.entity_updates[base_entity.id]
    assert ent_upd.inventory is not None
    assert len(ent_upd.inventory.items_add) == 2
    assert any(s.item_id == "herb" for s in ent_upd.inventory.items_add)
    assert any(s.item_id == "iron_ore" for s in ent_upd.inventory.items_add)

def test_atomic_group_rollback_on_partial_failure(base_entity):
    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=101, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=1)
    node2 = ResourceNodeState(id=102, kind="ore", position=(0,0), yields_item="iron_ore", remaining_charges=3, max_charges=3, required_ticks=1)
    
    # Setup entity with 1 slot available
    entity = replace(base_entity, 
        inventory=InventoryComponent(max_slots=1, items=[])
    )
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity}, resource_nodes={101: node1, 102: node2})
    
    # Intent 1 fits, Intent 2 does not. Since they are grouped and required, both should fail.
    intent1 = ResourceTransferIntent(
        source_id=101, source_kind="NODE",
        items_add=[ItemStack("herb", 1)],
        group_id="batch1", is_group_required=True
    )
    intent2 = ResourceTransferIntent(
        source_id=102, source_kind="NODE",
        items_add=[ItemStack("iron_ore", 1)],
        group_id="batch1", is_group_required=True
    )
    
    update = StateUpdate(entity_updates={
        entity.id: EntityUpdate(entity_id=entity.id, resource_transfers=[intent1, intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Inventory should be empty in the update (rolled back)
    ent_upd = refined.entity_updates[entity.id]
    assert ent_upd.inventory is None or len(ent_upd.inventory.items_add) == 0

def test_independent_transfers_allow_partial_success(base_entity):
    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=101, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=1)
    node2 = ResourceNodeState(id=102, kind="ore", position=(0,0), yields_item="iron_ore", remaining_charges=3, max_charges=3, required_ticks=1)
    
    # Setup entity with 1 slot available
    entity = replace(base_entity, 
        inventory=InventoryComponent(max_slots=1, items=[])
    )
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity}, resource_nodes={101: node1, 102: node2})
    
    # Two independent intents (different or None group_id)
    intent1 = ResourceTransferIntent(
        source_id=101, source_kind="NODE",
        items_add=[ItemStack("herb", 1)],
        group_id=None # Independent
    )
    intent2 = ResourceTransferIntent(
        source_id=102, source_kind="NODE",
        items_add=[ItemStack("iron_ore", 1)],
        group_id=None # Independent
    )
    
    update = StateUpdate(entity_updates={
        entity.id: EntityUpdate(entity_id=entity.id, resource_transfers=[intent1, intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Should have herb but NOT iron_ore
    ent_upd = refined.entity_updates[entity.id]
    assert ent_upd.inventory is not None
    assert len(ent_upd.inventory.items_add) == 1
    assert ent_upd.inventory.items_add[0].item_id == "herb"

def test_optional_group_allows_partial_success(base_entity):
    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=101, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=1)
    node2 = ResourceNodeState(id=102, kind="ore", position=(0,0), yields_item="iron_ore", remaining_charges=3, max_charges=3, required_ticks=1)
    
    # Setup entity with 1 slot available
    entity = replace(base_entity, 
        inventory=InventoryComponent(max_slots=1, items=[])
    )
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity}, resource_nodes={101: node1, 102: node2})
    
    # Grouped but NOT required
    intent1 = ResourceTransferIntent(
        source_id=101, source_kind="NODE",
        items_add=[ItemStack("herb", 1)],
        group_id="batch_optional", is_group_required=False
    )
    intent2 = ResourceTransferIntent(
        source_id=102, source_kind="NODE",
        items_add=[ItemStack("iron_ore", 1)],
        group_id="batch_optional", is_group_required=False
    )
    
    update = StateUpdate(entity_updates={
        entity.id: EntityUpdate(entity_id=entity.id, resource_transfers=[intent1, intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Should have herb but NOT iron_ore (partial success allowed in optional group)
    ent_upd = refined.entity_updates[entity.id]
    assert ent_upd.inventory is not None
    assert len(ent_upd.inventory.items_add) == 1
    assert ent_upd.inventory.items_add[0].item_id == "herb"

def test_atomic_group_rollback_prevents_xp_gain(base_entity):
    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=101, kind="herb", position=(0,0), yields_item="herb", remaining_charges=3, max_charges=3, required_ticks=1)
    
    # Setup entity with 0 slots available
    entity = replace(base_entity, 
        inventory=InventoryComponent(max_slots=0, items=[])
    )
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity}, resource_nodes={101: node1})
    
    # Intent: Herb (fails) + XP (would succeed)
    intent1 = ResourceTransferIntent(
        source_id=101, source_kind="NODE",
        items_add=[ItemStack("herb", 1)],
        group_id="batch_xp", is_group_required=True
    )
    intent2 = ResourceTransferIntent(
        source_id=102, source_kind="COMBAT", # Combat-sourced XP
        xp_reward=50,
        group_id="batch_xp", is_group_required=True
    )
    
    update = StateUpdate(entity_updates={
        entity.id: EntityUpdate(entity_id=entity.id, resource_transfers=[intent1, intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Everything should be rolled back
    ent_upd = refined.entity_updates[entity.id]
    assert ent_upd.identity is None or ent_upd.identity.evolution_points_delta == 0
    assert ent_upd.inventory is None or len(ent_upd.inventory.items_add) == 0
