import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, ItemStack
from src.core.quests import QuestState, QuestStatus, RewardState, QuestKind
from src.core.strategic import StrategicComponent
from src.core.updates import EntityUpdate, QuestUpdate, StateUpdate, ResourceTransferIntent
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.engine.pipeline import AuthoritativeApplyPipeline

@pytest.fixture
def base_entity():
    return V2EntityBuilder(entity_id=1).identity(role=EntityRole.HERO).build()

def test_atomic_group_success(base_entity):
    from src.core.state import BuildingState, InventoryComponent, ItemStack
    shop = BuildingState(
        id="shop", kind="SHOP", functional=True,
        position=(0,0),
        inventory=InventoryComponent(items=[ItemStack(item_id="herb", quantity=10)])
    )
    state = AuthoritativeState(tick=0, seed=123, entities={base_entity.id: base_entity}, buildings={"shop": shop})
    
    intent_a = ResourceTransferIntent(
        source_id="shop", source_kind="SHOP_BUY", 
        gold_cost=0, items_add=[ItemStack(item_id="herb", quantity=1)],
        group_id="g1"
    )
    intent_b = ResourceTransferIntent(
        source_id="quest", source_kind="QUEST", 
        gold_delta=100, group_id="g1"
    )
    
    update = StateUpdate(entity_updates={
        base_entity.id: EntityUpdate(entity_id=base_entity.id, resource_transfers=[intent_a, intent_b])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    final_state = ApplyPath.apply_generation(state, refined)
    
    entity = final_state.entities[base_entity.id]
    assert entity.inventory.gold == 100
    assert any(item.item_id == "herb" for item in entity.inventory.items)

def test_atomic_group_rollback_on_inventory_full(base_entity):
    # Fill inventory (max_slots is 16)
    items = [ItemStack(item_id="iron_ore", quantity=1) for _ in range(16)]
    full_entity = replace(base_entity, inventory=replace(base_entity.inventory, items=items))
    from src.core.state import ResourceNodeState
    node = ResourceNodeState(
        id="loot", kind="LOOT", position=(0,0), 
        yields_item="iron_sword", remaining_charges=1, max_charges=1, required_ticks=1
    )
    state = AuthoritativeState(tick=0, seed=123, entities={full_entity.id: full_entity}, resource_nodes={"loot": node})
    
    # Intent A succeeds (Gold), Intent B fails (Items)
    intent_a = ResourceTransferIntent(
        source_id="quest", source_kind="QUEST", 
        gold_delta=500, group_id="g1"
    )
    intent_b = ResourceTransferIntent(
        source_id="loot", source_kind="NODE", 
        items_add=[ItemStack(item_id="iron_sword", quantity=1)],
        group_id="g1"
    )
    
    update = StateUpdate(entity_updates={
        full_entity.id: EntityUpdate(entity_id=full_entity.id, resource_transfers=[intent_a, intent_b])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    final_state = ApplyPath.apply_generation(state, refined)
    
    entity = final_state.entities[full_entity.id]
    # Intent A must be rolled back because Intent B failed in the same group
    assert entity.inventory.gold == 0
    assert not any(item.item_id == "iron_sword" for item in entity.inventory.items)

def test_mixed_independent_and_grouped_intents(base_entity):
    from src.core.state import GroundItemState
    ground_item = GroundItemState(id=101, item_id="herb", position=(0,0), quantity=1)
    state = AuthoritativeState(tick=0, seed=123, entities={base_entity.id: base_entity}, ground_items={101: ground_item})
    
    # Intent 1: Independent success
    intent_1 = ResourceTransferIntent(
        source_id=101, source_kind="GROUND_ITEM", 
        items_add=[ItemStack(item_id="herb", quantity=1)], group_id=None
    )
    # Intent 2: Group success
    intent_2 = ResourceTransferIntent(
        source_id="quest", source_kind="QUEST", 
        gold_delta=100, group_id="g1"
    )
    # Intent 3: Group failure (triggering rollback of Intent 2)
    # Use invalid gold cost to force failure
    intent_3 = ResourceTransferIntent(
        source_id="tax", source_kind="CRAFTING", 
        gold_cost=9999, group_id="g1"
    )
    
    update = StateUpdate(entity_updates={
        base_entity.id: EntityUpdate(entity_id=base_entity.id, resource_transfers=[intent_1, intent_2, intent_3])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    final_state = ApplyPath.apply_generation(state, refined)
    
    entity = final_state.entities[base_entity.id]
    # Intent 1 should succeed
    assert any(item.item_id == "herb" for item in entity.inventory.items)
    # Intent 2 should be rolled back because of Intent 3
    assert entity.inventory.gold == 0

def test_quest_status_rollback_on_group_failure(base_entity):
    quest = QuestState(
        id="q1", kind="quest", quest_kind=QuestKind.HUNT,
        quest_status=QuestStatus.ACTIVE, goal_value=5.0, current_value=0.0,
        reward=RewardState(gold=100)
    )
    entity = replace(base_entity, strategic=StrategicComponent(projects={"q1": quest}))
    state = AuthoritativeState(tick=0, seed=123, entities={entity.id: entity})
    
    # Intent A: Quest Reward (succeeds)
    intent_a = ResourceTransferIntent(
        source_id="q1", source_kind="QUEST", 
        gold_delta=100, transfer_kind="QUEST_REWARD", group_id="g1"
    )
    # Intent B: Secondary effect (fails)
    intent_b = ResourceTransferIntent(
        source_id="penalty", source_kind="CRAFTING", 
        gold_cost=9999, group_id="g1"
    )
    
    update = StateUpdate(entity_updates={
        entity.id: EntityUpdate(entity_id=entity.id, quest=QuestUpdate(quest_id="q1"), resource_transfers=[intent_a, intent_b])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    final_state = ApplyPath.apply_generation(state, refined)
    
    new_quest = final_state.entities[entity.id].strategic.projects["q1"]
    # Should still be ACTIVE because group failed (and it was ACTIVE initially)
    assert new_quest.quest_status == QuestStatus.ACTIVE
    assert final_state.entities[entity.id].inventory.gold == 0
