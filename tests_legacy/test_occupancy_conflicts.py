import pytest
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.core.updates import StateUpdate, EntityUpdate
from src_legacy.engine.pipeline import AuthoritativeApplyPipeline

def test_occupancy_conflict_resolution():
    """Verify that two entities racing for the same tile resolve deterministically."""
    # Two entities at (0,0) and (2,0) both trying to move to (1,0)
    ent1 = EntityState(id=1, kind="HERO", position=(0, 0))
    ent2 = EntityState(id=2, kind="HERO", position=(2, 0))
    state = AuthoritativeState(tick=0, seed=1, entities={1: ent1, 2: ent2})
    
    # Proposal: Both move to (1,0)
    upd1 = EntityUpdate(entity_id=1, new_position=(1, 0))
    upd2 = EntityUpdate(entity_id=2, new_position=(1, 0))
    raw_update = StateUpdate(entity_updates={1: upd1, 2: upd2})
    
    # Refine
    refined_update = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify: Entity 1 wins (lower ID), Entity 2 loses
    assert refined_update.entity_updates[1].new_position == (1, 0)
    assert refined_update.entity_updates[2].new_position is None
    assert refined_update.entity_updates[2].navigation.failure_reason == "OCCUPANCY_CONFLICT"

def test_occupancy_conflict_with_static_entity():
    """Verify that a move is rejected if the target tile is occupied by a non-moving entity."""
    ent1 = EntityState(id=1, kind="HERO", position=(0, 0))
    ent2 = EntityState(id=2, kind="HERO", position=(1, 0)) # Already at target
    state = AuthoritativeState(tick=0, seed=1, entities={1: ent1, 2: ent2})
    
    # Proposal: Entity 1 moves to (1,0)
    upd1 = EntityUpdate(entity_id=1, new_position=(1, 0))
    raw_update = StateUpdate(entity_updates={1: upd1})
    
    # Refine
    refined_update = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify: Entity 1 loses because (1,0) is occupied
    assert refined_update.entity_updates[1].new_position is None
    assert refined_update.entity_updates[1].navigation.failure_reason == "OCCUPANCY_CONFLICT"
