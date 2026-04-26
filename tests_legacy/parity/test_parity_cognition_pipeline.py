import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, CombatComponent, IdentityComponent, SocialComponent
from src_legacy.core.updates import StateUpdate, EntityUpdate
from src_legacy.engine.domain_logic import SimulationDomainLogic

@pytest.mark.v2_contract
def test_sensory_filtering_integration():
    # Setup state with many neighbors
    subject = EntityState(
        id=1, 
        kind="hero", 
        position=(0,0), 
        identity=IdentityComponent(faction=0)
    )
    
    # Add 10 neighbors
    entities = {1: subject}
    for i in range(2, 12):
        entities[i] = EntityState(
            id=i, 
            kind="monster", 
            position=(1,1), # All very close
            identity=IdentityComponent(faction=1)
        )
    
    state = AuthoritativeState(tick=1, seed=42, entities=entities)
    
    # execute_brain calls SensoryFilter.filter_saliency
    # SensoryFilter defaults to max_targets=5
    # We can check if it filters by looking at trace or mock
    # But for now we just verify it doesn't crash and returns a valid update
    upd_dict = SimulationDomainLogic.execute_brain(state, subject)
    assert 1 in upd_dict
    assert isinstance(upd_dict[1], EntityUpdate)

@pytest.mark.v2_contract
def test_emotional_appraisal_panic_flee():
    # Setup state with low HP (5%)
    subject = EntityState(
        id=1, 
        kind="hero", 
        position=(10,10), 
        combat=CombatComponent(hp=5, max_hp=100),
        identity=IdentityComponent(faction=0)
    )
    # Add a monster nearby to trigger panic
    monster = EntityState(
        id=2, 
        kind="monster", 
        position=(11,11), 
        identity=IdentityComponent(faction=1)
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: subject, 2: monster})
    
    # execute_brain should result in a flee task
    upd_dict = SimulationDomainLogic.execute_brain(state, subject)
    upd = upd_dict[1]
    
    # Check if task is PANIC_RETREAT or similar
    # TacticalDecisionSystem.evaluate_entity_intent handles the actual task creation based on emotion
    assert upd.task is not None
    assert "PANIC" in upd.task.payload_set.get("reason", "")
    # Fleeing entities set navigation target to (0,0)
    assert upd.navigation is not None
    assert upd.navigation.target_set == (0.0, 0.0)
