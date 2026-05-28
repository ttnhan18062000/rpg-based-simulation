"""
tests/unit/domains/cooperation/test_phase7_cooperation_boundary.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests verifying the immutable domain boundary and mutations constraints.
"""

import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase


def test_cooperation_service_does_not_mutate_state():
    # Verify that evaluating cooperation decisions does not directly mutate the entities in the state
    b = (V2EntityBuilder(1)
         .kind("HERO")
         .location(0.0, 0.0)
         .combat(hp=100, max_hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=123)
    update = StateUpdate()
    
    refined = CooperationPhase.execute(state, update)
    
    # Original entity must remain unchanged (no side-effect direct mutations)
    assert entity.inventory.gold == 0
    assert entity.combat.hp == 100


def test_cooperation_service_does_not_execute_contract_directly():
    # Verify that a decision outputs a contract intent for downstream apply sequence instead of mutating state
    b = (V2EntityBuilder(1)
         .kind("HERO")
         .location(0.0, 0.0)
         .combat(hp=100, max_hp=100)
         .lifecycle(active=True))
    entity = b.build()
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=123)
    update = StateUpdate()
    
    refined = CooperationPhase.execute(state, update)
    
    # Assert that no direct contract was committed into entity state
    assert len(entity.strategic.contracts) == 0
