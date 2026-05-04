import pytest
from src.core.state import EntityState, CombatComponent
from src.core.builder import V2EntityBuilder

def test_frozen_state_mutation_tripwire():
    builder = V2EntityBuilder(1)
    entity = builder.build()
    
    # Attempting to mutate a frozen dataclass should raise FrozenInstanceError
    with pytest.raises(Exception): # Usually FrozenInstanceError
        entity.combat.readiness = 100.0
        
    with pytest.raises(Exception):
        entity.combat.hp = 0
        
    print("\nSuccessfully verified that direct mutation of EntityState is blocked by the frozen contract.")

def test_tactical_legality_envelope_mock():
    # This test verifies that the tactical AI should only propose legal actions.
    # In V2, the AI returns INTENTS (MovementIntent, CombatIntent) which are then 
    # validated by the Authoritative Kernel.
    
    from src.engine.tactical import TacticalDecisionSystem
    from src.core.state import AuthoritativeState
    
    # Setup a scenario where an entity is "frozen" or "stunned"
    hero = (V2EntityBuilder(1)
            .at((5.0, 5.0))
            .with_property("status_stunned", True)
            .build())
    
    state = AuthoritativeState(tick=1, entities={1: hero}, seed=42)
    
    # Decision system should still run, but if the actor is stunned, it might return no action or restricted action
    decision = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    
    # Check that if stunned, we don't have movement or combat intents
    # (Assuming TacticalDecisionSystem respects status effects)
    assert decision.navigation is None
    assert decision.task is None
        
    print("\nSuccessfully verified tactical decision envelope (status awareness).")
