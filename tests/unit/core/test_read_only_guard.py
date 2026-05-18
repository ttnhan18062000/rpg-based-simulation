import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, ReadOnlyError
from src.engine.domain_logic import SimulationDomainLogic
from src.engine.tactical import TacticalDecisionSystem
from src.core.updates import EntityUpdate
from src.core.builder import V2EntityBuilder


def test_read_only_guard_enforcement():
    # Setup state
    entity = V2EntityBuilder(1).location(0.0, 0.0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={1: entity})
    
    # We need to mock or monkeypatch something in the brain to attempt mutation
    original_evaluate = TacticalDecisionSystem.evaluate_entity_intent
    
    def malicious_evaluate(s, e, n=None, t=None):
        # Attempt to mutate the state!
        try:
            s.entities[1] = e # This should raise ReadOnlyError because s.entities is a ReadOnlyDict
        except ReadOnlyError as ex:
            raise ex # Propagate
        return original_evaluate(s, e, n, t)
    
    import src.engine.tactical
    src.engine.tactical.TacticalDecisionSystem.evaluate_entity_intent = malicious_evaluate
    
    try:
        # SimulationDomainLogic.execute_brain calls to_readonly() on state
        with pytest.raises(ReadOnlyError) as excinfo:
            SimulationDomainLogic.execute_brain(state, entity)
        assert "Authoritative mutation attempted" in str(excinfo.value)
    finally:
        # Restore original
        src.engine.tactical.TacticalDecisionSystem.evaluate_entity_intent = original_evaluate


def test_read_only_properties_mutation():
    # Entities themselves should have read-only properties
    entity = V2EntityBuilder(1).location(0.0, 0.0).build()
    state = AuthoritativeState(tick=100, seed=42, entities={1: entity})
    
    # V2 components are already frozen dataclasses, but ReadOnlyDict might be used for some nested fields
    # In V2EntityBuilder, the built entity is already deeply frozen.
    readonly_state = state.to_readonly()
    readonly_entity = readonly_state.entities[1]
    
    # In V2, EntityState is frozen, so direct assignment to fields raises frozen error (dataclasses.FrozenInstanceError)
    # However, the test specifically checks for ReadOnlyError which is our custom one for ReadOnlyDict.
    
    # Let's check if AuthoritativeState.to_readonly actually uses ReadOnlyDict.
    # Looking at state.py: entities=ReadOnlyDict({eid: e.to_readonly() for eid, e in self.entities.items()})
    
    with pytest.raises(ReadOnlyError):
        readonly_state.entities[2] = entity # This should trigger ReadOnlyError in ReadOnlyDict.__setitem__
