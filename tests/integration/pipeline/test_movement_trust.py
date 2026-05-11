import pytest
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder

def test_mutation_boundary_strips_unauthorized_teleportation():
    """
    Proof of TOWN-152: No standalone system can change position without authoritative validation.
    """
    e_id = 1
    # Hero at (0,0)
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    # Worker trying to teleport to (50, 50)
    unauthorized_upd = EntityUpdate(
        entity_id=e_id,
        new_position=(50, 50)
    )
    raw_update = StateUpdate(entity_updates={e_id: unauthorized_upd})
    
    # Process through pipeline
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify new_position is stripped
    assert refined.entity_updates[e_id].new_position is None, "Worker-side new_position should be stripped"
