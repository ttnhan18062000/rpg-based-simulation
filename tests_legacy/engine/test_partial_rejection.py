import pytest
from dataclasses import replace
from src_legacy.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src_legacy.core.updates import StateUpdate, EntityUpdate, CombatUpdate, NavigationUpdate
from src_legacy.engine.pipeline import AuthoritativeApplyPipeline

@pytest.fixture
def base_state():
    e1 = EntityState(id=1, kind="HERO", position=(0.0, 0.0), active=True)
    e2 = EntityState(id=2, kind="HERO", position=(1.0, 1.0), active=True)
    return AuthoritativeState(
        tick=100,
        world_time=1000,
        seed=42,
        entities={1: e1, 2: e2},
        regions={},
        resource_nodes={},
        buildings={}
    )

def test_partial_rejection_occupancy_vs_combat(base_state):
    """
    Law: Rejecting a move (Occupancy Conflict) must not reject unrelated deltas (e.g. HP loss).
    Scenario: Entity 1 and Entity 2 both try to move to (0,0).
    Entity 1 is already at (0,0) and stays there.
    Entity 2 tries to move to (0,0) but also suffers HP loss (e.g. from a hazard or poison).
    """
    # Entity 2 proposes move to (0,0) AND HP loss
    ent_upd_2 = EntityUpdate(
        entity_id=2,
        new_position=(0.0, 0.0),
        moved_this_tick=True,
        combat=CombatUpdate(hp_delta=-10)
    )
    
    raw_update = StateUpdate(entity_updates={2: ent_upd_2})
    
    # Refine the update
    refined_update = AuthoritativeApplyPipeline.refine(base_state, raw_update)
    
    # Entity 2's move should be rejected (since 1 is there)
    res_2 = refined_update.entity_updates[2]
    assert res_2.new_position is None
    assert res_2.moved_this_tick is False
    assert res_2.navigation.failure_reason == "OCCUPANCY_CONFLICT"
    
    # BUT the HP loss must be preserved
    assert res_2.combat.hp_delta == -10

def test_partial_rejection_occupancy_vs_readiness(base_state):
    """
    Law: Rejecting a move must not reject unrelated deltas (e.g. readiness changes).
    """
    ent_upd_2 = EntityUpdate(
        entity_id=2,
        new_position=(0.0, 0.0),
        moved_this_tick=True,
        readiness_delta=50.0
    )
    
    raw_update = StateUpdate(entity_updates={2: ent_upd_2})
    refined_update = AuthoritativeApplyPipeline.refine(base_state, raw_update)
    
    res_2 = refined_update.entity_updates[2]
    assert res_2.new_position is None # Rejected
    assert res_2.readiness_delta == 50.0 # Preserved
