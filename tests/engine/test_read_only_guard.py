import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, ReadOnlyError
from src.engine.domain_logic import SimulationDomainLogic
from src.engine.tactical import TacticalDecisionSystem
from src.core.updates import EntityUpdate

def test_read_only_guard_enforcement():
    # Setup state
    state = AuthoritativeState(tick=100, seed=42)
    entity = EntityState(id=1, kind="hero", position=(0.0, 0.0))
    state = replace(state, entities={1: entity})
    
    # We need to mock or monkeypatch something in the brain to attempt mutation
    # Let's monkeypatch TacticalDecisionSystem.evaluate_entity_intent
    
    original_evaluate = TacticalDecisionSystem.evaluate_entity_intent
    
    def malicious_evaluate(s, e):
        # Attempt to mutate the state!
        try:
            s.entities[1] = e # This should raise ReadOnlyError because s.entities is a ReadOnlyDict
        except ReadOnlyError as ex:
            raise ex # Propagate
        return original_evaluate(s, e)
    
    import src.engine.tactical
    src.engine.tactical.TacticalDecisionSystem.evaluate_entity_intent = malicious_evaluate
    
    try:
        with pytest.raises(ReadOnlyError) as excinfo:
            SimulationDomainLogic.execute_brain(state, entity)
        assert "Authoritative mutation attempted" in str(excinfo.value)
        print(f"\nCaught expected mutation attempt: {excinfo.value}")
    finally:
        # Restore original
        src.engine.tactical.TacticalDecisionSystem.evaluate_entity_intent = original_evaluate

def test_read_only_properties_mutation():
    # Entities themselves should have read-only properties
    state = AuthoritativeState(tick=100, seed=42)
    entity = EntityState(id=1, kind="hero", position=(0.0, 0.0), properties={"gold": 100})
    state = replace(state, entities={1: entity})
    
    readonly_state = state.to_readonly()
    readonly_entity = readonly_state.entities[1]
    
    with pytest.raises(ReadOnlyError):
        readonly_entity.properties["gold"] = 200
        
    print("\nSuccessfully blocked direct property mutation on read-only entity.")
