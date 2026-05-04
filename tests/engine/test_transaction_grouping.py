import pytest
from src.core.state import AuthoritativeState, EntityState, ItemStack, InventoryComponent, BuildingState
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent, RewardUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode

def test_interleaved_transaction_grouping():
    """
    RPG-1698: non_contiguous_group_stability
    RPG-1664: atomic_conservation_law
    Proof: This test ensures that grouped intents are processed together even if interleaved
           with independent intents in the proposal list.
    """
    actor = (V2EntityBuilder(1)
             .at((5, 5))
             .readiness(100.0)
             .build())
    
    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={1: actor}
    )
    
    # Intent A1 (Group 1)
    intent_a1 = ResourceTransferIntent(
        transaction_id="G1-1",
        group_id="GROUP_1",
        source_id="TOWN_HALL",
        source_kind="QUEST",
        gold_delta=10,
        transfer_kind="LOOT"
    )
    # Intent B (Independent)
    intent_b = ResourceTransferIntent(
        transaction_id="IND-1",
        source_id="BLACKSMITH",
        source_kind="TOWN_SERVICE",
        gold_delta=-5,
        transfer_kind="PICKUP"
    )
    # Intent A2 (Group 1)
    intent_a2 = ResourceTransferIntent(
        transaction_id="G1-2",
        group_id="GROUP_1",
        source_id="GUILD_HALL",
        source_kind="QUEST",
        reward_upd=RewardUpdate(xp_gain=100),
        transfer_kind="LOOT"
    )
    
    # Interleaved list
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=[intent_a1, intent_b, intent_a2])
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    res = refined.entity_updates[1].intent_results
    assert len(res) == 3
    
    # Verify they were all accepted
    assert all(r.accepted for r in res)
    
    # Verify XP was processed (it gets consumed by EvolutionSystem into evolution_points_delta)
    final_e1 = refined.entity_updates[1]
    # XP 100 should give some evolution points
    assert final_e1.identity.evolution_points_delta > 0 or final_e1.identity.evolution_level_set is not None
    assert final_e1.inventory.gold_delta == 5 # 10 - 5
    
def test_group_failure_rollback():
    """
    RPG-1697: transaction_grouping_atomicity
    Proof: This test ensures that if one intent in a group fails, the whole group is rolled back.
    """
    actor = (V2EntityBuilder(1)
             .at((5, 5))
             .readiness(100.0)
             .gold(0)
             .build())
    
    # Add a valid building for SHOP_BUY
    shop = BuildingState(id=10, kind="shop", position=(5,5), functional=True, inventory=InventoryComponent(items=[ItemStack("wood", 100)]))
    
    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={1: actor},
        buildings={10: shop}
    )
    
    # Intent A (Group 1) - Success (Gain 100 gold)
    intent_a = ResourceTransferIntent(
        transaction_id="G1-1",
        group_id="GROUP_1",
        source_id="GIFT",
        source_kind="QUEST",
        gold_delta=100,
        transfer_kind="LOOT"
    )
    # Intent B (Group 1) - Failure (Insufficient gold for cost)
    # Even with 100 from intent_a, 500 is too much.
    intent_b = ResourceTransferIntent(
        transaction_id="G1-2",
        group_id="GROUP_1",
        source_id=10, # SHOP
        source_kind="SHOP_BUY",
        items_add=[ItemStack("wood", 1)],
        gold_cost=500, 
        transfer_kind="BUY"
    )
    
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=[intent_a, intent_b])
        }
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    res = refined.entity_updates[1].intent_results
    assert len(res) == 2
    
    # Intent A should be REJECTED with GROUP_ROLLBACK because Intent B failed
    assert res[0].accepted is False
    assert res[0].reason == "GROUP_ROLLBACK"
    
    # Intent B should be REJECTED with INSUFFICIENT_GOLD
    assert res[1].accepted is False
    assert res[1].reason == ReasonCode.INSUFFICIENT_GOLD
    
    # Verify that NO gold was added
    assert refined.entity_updates[1].inventory is None or refined.entity_updates[1].inventory.gold_delta == 0
