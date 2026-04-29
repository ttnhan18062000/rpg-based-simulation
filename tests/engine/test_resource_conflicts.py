import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CorpseState, ItemStack, InventoryComponent
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_contested_corpse_loot_conflict():
    """
    Law: One accepted destructive transfer per source per tick.
    Proof: This test proves that if two actors try to loot the same corpse in the same tick,
           only the first one (lowest ID) succeeds and the second one gets SOURCE_LOCKED.
           
    RPG-1694: actor_validity_enforcement
    RPG-1695: source_locked_conflict
    RPG-1696: source_depleted_enforcement
    """
    # 1. Setup state with a corpse and two actors
    corpse = CorpseState(id=10, original_entity_id=50, position=(5, 5), items=[ItemStack("wood", 10)], decay_tick=200)
    actor_a = EntityState(id=1, kind="HERO", position=(5, 5), active=True, inventory=InventoryComponent(max_slots=10))
    actor_b = EntityState(id=2, kind="HERO", position=(5, 5), active=True, inventory=InventoryComponent(max_slots=10))
    
    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={1: actor_a, 2: actor_b},
        corpses={10: corpse}
    )
    
    # 2. Propose updates: Both actors loot corpse 10
    intent_a = ResourceTransferIntent(
        transaction_id="A-1",
        source_id=10,
        source_kind="CORPSE",
        items_add=[ItemStack("wood", 10)],
        transfer_kind="LOOT"
    )
    intent_b = ResourceTransferIntent(
        transaction_id="B-1",
        source_id=10,
        source_kind="CORPSE",
        items_add=[ItemStack("wood", 10)],
        transfer_kind="LOOT"
    )
    
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=[intent_a]),
            2: EntityUpdate(entity_id=2, resource_transfers=[intent_b])
        }
    )
    
    # 3. Apply pipeline refinement
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # 4. Verify results
    # Actor 1 should succeed
    res_1 = refined.entity_updates[1].intent_results
    assert len(res_1) == 1
    assert res_1[0].accepted is True
    
    # Actor 2 should fail with SOURCE_LOCKED
    res_2 = refined.entity_updates[2].intent_results
    assert len(res_2) == 1
    assert res_2[0].accepted is False
    assert res_2[0].reason == "SOURCE_LOCKED"
    
    # Only one corpse removal should be proposed
    assert len(refined.corpses_remove) == 1
    assert refined.corpses_remove[0] == 10
