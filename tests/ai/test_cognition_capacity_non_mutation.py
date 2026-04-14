import pytest
from src.ai.cognition_capacity import CognitionCapacityBuilder
from tests.ai.test_cognition_capacity_builder import create_mock_entity

def test_build_profile_does_not_mutate_entity_attributes():
    ent = create_mock_entity(int_=10, wis=10, per=10, cha=10)
    
    # Store snapshot of attribute before call
    initial_int = ent.progression.attributes.int_
    
    _ = CognitionCapacityBuilder.build(ent)
    
    # Assert same value survives the call
    assert ent.progression.attributes.int_ == initial_int

def test_build_profile_does_not_mutate_caps():
    ent = create_mock_entity(int_cap=15)
    _ = CognitionCapacityBuilder.build(ent)
    assert ent.progression.attribute_caps.int_cap == 15

def test_build_profile_does_not_mutate_stamina():
    ent = create_mock_entity(stamina=25, max_stamina=50)
    _ = CognitionCapacityBuilder.build(ent)
    assert ent.progression.stamina == 25
    assert ent.progression.max_stamina == 50

def test_build_profile_returns_new_profile_object_each_call():
    ent = create_mock_entity()
    p1 = CognitionCapacityBuilder.build(ent)
    p2 = CognitionCapacityBuilder.build(ent)
    
    # id(p1) and id(p2) must be different
    assert p1 is not p2
    # Ensure they are different instances of the same class
    assert id(p1) != id(p2)
