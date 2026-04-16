import pytest
from src.ai.cognition_capacity import CognitionCapacityBuilder
from tests.ai.test_cognition_capacity_builder import create_mock_entity

def test_profile_derivation_is_deterministic_for_same_entity_state():
    ent = create_mock_entity(int_=10, wis=10, per=10, cha=10)
    
    p1 = CognitionCapacityBuilder.build(ent, tick=100)
    p2 = CognitionCapacityBuilder.build(ent, tick=100)
    
    # Asserting dictionaries to catch any field differences
    assert p1.model_dump() == p2.model_dump()

def test_profile_derivation_is_independent_of_tick_in_milestone_1():
    ent = create_mock_entity(int_=10, wis=10, per=10, cha=10)
    
    p1 = CognitionCapacityBuilder.build(ent, tick=100)
    p2 = CognitionCapacityBuilder.build(ent, tick=200)
    
    assert p1.model_dump() == p2.model_dump()

def test_profile_derivation_does_not_use_rng():
    # Since we can't easily prove negative, we check if multiple calls with same state produce same result
    # (The implementation doesn't use random, but this is a contract test)
    ent = create_mock_entity(int_=8, wis=8, per=8, cha=8)
    
    results = [CognitionCapacityBuilder.build(ent).model_dump() for _ in range(10)]
    for r in results[1:]:
        assert r == results[0]
