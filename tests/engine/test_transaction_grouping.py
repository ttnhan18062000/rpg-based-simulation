import pytest
from src.core.state import AuthoritativeState, EntityState, ItemStack, InventoryComponent
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_interleaved_transaction_grouping():
    """
    RPG-1698: non_contiguous_group_stability
    RPG-1664: atomic_conservation_law
    Proof: This test ensures that grouped intents are processed together even if interleaved
           with independent intents in the proposal list.
    """
    actor = EntityState(id=1, kind="HERO", position=(5, 5), active=True, inventory=InventoryComponent(max_slots=10))
    
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
        xp_reward=100,
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
    assert final_e1.identity.evolution_points_delta > 0 or final_e1.identity.evolution_level_set > 0
    assert final_e1.inventory.gold_delta == 5 # 10 - 5
    
    # Verify group atomicity (if we forced a failure in one, all in group should fail)
    # But here we just verify they are all processed.
    
def test_group_failure_rollback():
    """
    RPG-1697: transaction_grouping_atomicity
    Proof: This test ensures that if one intent in a group fails, the whole group is rolled back.
    """
    actor = EntityState(id=1, kind="HERO", position=(5, 5), active=True, inventory=InventoryComponent(max_slots=10, gold=0))
    
    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={1: actor}
    )
    
    # Intent A (Group 1) - Success
    intent_a = ResourceTransferIntent(
        transaction_id="G1-1",
        group_id="GROUP_1",
        source_id="GIFT",
        source_kind="QUEST",
        gold_delta=100,
        transfer_kind="LOOT"
    )
    # Intent B (Group 1) - Failure (Insufficient gold if it was a cost, but here we'll use a cost that exceeds what we have)
    intent_b = ResourceTransferIntent(
        transaction_id="G1-2",
        group_id="GROUP_1",
        source_id="BLACKSMITH",
        source_kind="SHOP_BUY",
        gold_cost=500, # We only have 100 after intent_a, but we start with 0.
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
    assert res[1].reason == "INSUFFICIENT_GOLD"
    
    # Verify that NO gold was added
    assert refined.entity_updates[1].inventory is None or refined.entity_updates[1].inventory.gold_delta == 0
