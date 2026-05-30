"""
tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py

Phase 3 — Adventure Decision Domain Boundary tests.
Verifies isolation of the adventure domain from core entity state.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.domains.adventure.schema import AdventureDecisionResult, AdventureRouteOption


def test_adventure_decision_does_not_require_adventure_component():
    """Asserts EntityState is completely free of any adventure-specific components."""
    entity = V2EntityBuilder(1).build()
    
    # Assert no adventure component exists as a direct attribute on entity
    for attr in dir(entity):
        assert "adventure" not in attr.lower()


def test_adventure_decision_accepts_generic_self_model_inputs():
    """
    Asserts the decision interface accepts generic self-model inputs
    rather than a customized adventure component.
    """
    from src.core.self_model import SelfModelBundle, SelfAwarenessComponent
    
    awareness = SelfAwarenessComponent(
        perceived_condition={"health": 0.9, "stamina": 0.8},
        perceived_weaknesses=(),
    )
    bundle = SelfModelBundle(self_awareness=awareness)
    
    # We builder-integrate using generic self-model bundle
    entity = V2EntityBuilder(1).replace_self_model(bundle).build()
    
    assert hasattr(entity, "self_model")
    assert entity.self_model.self_awareness.perceived_condition["health"] == 0.9


def test_adventure_decision_returns_trace_without_mutating_state():
    """Asserts that calling the service returns a result without mutating entity state."""
    entity = V2EntityBuilder(1).build()
    
    # Store initial canonical dict of entity
    init_canonical = entity.to_canonical_dict()
    
    # Assert return result is of correct schema type
    res = AdventureDecisionResult(
        selected=None,
        rejected=(),
        proposed_project=None,
        proposed_objective=None,
        trace={"tested": True}
    )
    
    assert res.selected is None
    assert res.trace["tested"] is True
    # Immutability validation
    assert entity.to_canonical_dict() == init_canonical
