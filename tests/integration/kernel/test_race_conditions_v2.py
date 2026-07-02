import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, ResourceNodeState, ItemStack, GroundItemState, StrategicComponent, InventoryComponent, ItemKind
from src.core.enums import EntityRole, ReasonCode
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent
from src.core.items import ItemRegistry, ItemDefinition

# NOTE: ItemRegistry.bootstrap() is called lazily on the first refine() via a module-level
# side-effect in src.core.registries (seed_phase1_content). That wipes any items registered
# at import time. We re-register the test items in an autouse fixture that runs after all
# module-level imports have settled, so they are present for every test in this file.

def _register_test_items():
    """Re-register items needed by these tests. Safe to call multiple times."""
    ItemRegistry._items["iron_ore"] = ItemDefinition(id="iron_ore", name="Iron Ore", kind=ItemKind.MATERIAL, weight=2.0)
    ItemRegistry._items["gold_coin"] = ItemDefinition(id="gold_coin", name="Gold Coin", kind=ItemKind.CURRENCY, weight=0.01, stack_size=999)
    ItemRegistry._items["bone"] = ItemDefinition(id="bone", name="Bone", kind=ItemKind.MATERIAL, weight=0.5)
    ItemRegistry._items["steel_sword"] = ItemDefinition(id="steel_sword", name="Steel Sword", kind=ItemKind.WEAPON, weight=5.0, stack_size=1, properties={"slot": "MAIN_HAND"})
    ItemRegistry._items["coal"] = ItemDefinition(id="coal", name="Coal", kind=ItemKind.MATERIAL, weight=0.5)

@pytest.fixture(autouse=True)
def ensure_test_items():
    """Ensure test items survive any bootstrap() call triggered by lazy imports."""
    _register_test_items()

def create_mock_entity(id, pos=(0,0)):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(id)
            .kind("hero")
            .location(*pos)
            .identity(role=EntityRole.HERO)
            .combat(hp=100)
            .inventory(max_slots=10, max_weight=100.0)
            .build())

@pytest.mark.v2_contract
def test_race_condition_node_depletion():
    """Verify that multiple entities cannot over-harvest a node in one tick."""
    e1 = create_mock_entity(1, pos=(1,1))
    e2 = create_mock_entity(2, pos=(1,1))
    # Node with only 1 charge
    node = ResourceNodeState(id=10, kind="iron_ore", position=(1,1), remaining_charges=1, max_charges=1, yields_item="iron_ore", required_ticks=1)
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1, 2: e2}, resource_nodes={10: node})
    
    intent1 = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)])
    intent2 = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)])
    
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, resource_transfers=[intent1]),
        2: EntityUpdate(entity_id=2, resource_transfers=[intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Entity 1 (lower ID) should succeed
    res1 = next(r for r in refined.entity_updates[1].intent_results if r.source_id == 10)
    assert res1.accepted is True
    
    # Entity 2 should be rejected
    res2 = next(r for r in refined.entity_updates[2].intent_results if r.source_id == 10)
    assert res2.accepted is False
    assert res2.reason == "SOURCE_DEPLETED"

@pytest.mark.v2_contract
def test_race_condition_ground_item_lock():
    """Verify that only one entity can pick up a ground item in one tick."""
    e1 = create_mock_entity(1, pos=(1,1))
    e2 = create_mock_entity(2, pos=(1,1))
    
    # Ground item 100
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1, 2: e2}, ground_items={100: GroundItemState(id=100, item_id="gold_coin", quantity=50, position=(5.0, 5.0))})
    
    intent1 = ResourceTransferIntent(source_id=100, source_kind="GROUND_ITEM", items_add=[ItemStack("gold_coin", 50)])
    intent2 = ResourceTransferIntent(source_id=100, source_kind="GROUND_ITEM", items_add=[ItemStack("gold_coin", 50)])
    
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, resource_transfers=[intent1]),
        2: EntityUpdate(entity_id=2, resource_transfers=[intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Entity 1 succeeds
    assert refined.entity_updates[1].intent_results[0].accepted is True
    # Entity 2 fails with TARGET_LOCKED
    assert refined.entity_updates[2].intent_results[0].accepted is False
    assert refined.entity_updates[2].intent_results[0].reason == ReasonCode.TARGET_LOCKED

@pytest.mark.v2_contract
def test_race_condition_corpse_loot_lock():
    """Verify that only one entity can loot a corpse in one tick."""
    e1 = create_mock_entity(1, pos=(1,1))
    e2 = create_mock_entity(2, pos=(1,1))
    
    # Corpse 500
    from src.core.state import CorpseState
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1, 2: e2}, corpses={500: CorpseState(id=500, original_entity_id=99, position=(1,1), items=[ItemStack("bone", 1)], decay_tick=10)})
    
    intent1 = ResourceTransferIntent(source_id=500, source_kind="CORPSE", items_add=[ItemStack("bone", 1)])
    intent2 = ResourceTransferIntent(source_id=500, source_kind="CORPSE", items_add=[ItemStack("bone", 1)])
    
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, resource_transfers=[intent1]),
        2: EntityUpdate(entity_id=2, resource_transfers=[intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    assert refined.entity_updates[1].intent_results[0].accepted is True
    assert refined.entity_updates[2].intent_results[0].accepted is False
    assert refined.entity_updates[2].intent_results[0].reason == ReasonCode.TARGET_LOCKED

@pytest.mark.v2_contract
def test_multi_intent_group_rollback_race():
    """Verify that a failed group reservation is correctly rolled back for subsequent entities."""
    e1 = create_mock_entity(1, pos=(1,1))
    e2 = create_mock_entity(2, pos=(1,1))
    
    node = ResourceNodeState(id=10, kind="iron_ore", position=(1,1), remaining_charges=1, max_charges=1, yields_item="iron_ore", required_ticks=1)
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1, 2: e2}, resource_nodes={10: node})
    
    # Entity 1 has a GROUPED intent: [Loot Node 10, Failed Crafting]
    intent1 = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)], group_id="G1", is_group_required=True)
    # Crafting fails if materials are missing (intent.items_remove)
    intent2 = ResourceTransferIntent(source_id="C1", source_kind="CRAFTING", items_add=[ItemStack("steel_sword", 1)], items_remove=[ItemStack("coal", 5)], group_id="G1", is_group_required=True)
    
    # Entity 2 wants to loot Node 10
    intent3 = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)])
    
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, resource_transfers=[intent1, intent2]),
        2: EntityUpdate(entity_id=2, resource_transfers=[intent3])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Entity 1 fails the group
    assert refined.entity_updates[1].intent_results[0].accepted is False
    assert refined.entity_updates[1].intent_results[0].reason == "GROUP_ROLLBACK"
    
    # Entity 2 should now succeed because Entity 1's reservation was rolled back!
    assert refined.entity_updates[2].intent_results[0].accepted is True
