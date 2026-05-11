import pytest
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder

def test_mutation_boundary_strips_unauthorized_combat_hp():
    """
    Proof of TOWN-151: No standalone system can change combat HP without authoritative validation.
    """
    e_id = 1
    entity = V2EntityBuilder(e_id).kind("HERO").location(0, 0).combat(hp=100).build()
    state = AuthoritativeState(tick=100, seed=42, entities={e_id: entity})
    
    # Worker trying to directly mutate HP
    unauthorized_upd = EntityUpdate(
        entity_id=e_id,
        combat=CombatUpdate(hp_delta=-999)
    )
    raw_update = StateUpdate(entity_updates={e_id: unauthorized_upd})
    
    # Process through pipeline
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify combat update is stripped or hp_delta is zeroed
    combat_ref = refined.entity_updates[e_id].combat
    if combat_ref:
        assert combat_ref.hp_delta == 0, "Worker-side hp_delta should be stripped"
    else:
        assert combat_ref is None, "Worker-side combat update should be stripped"
