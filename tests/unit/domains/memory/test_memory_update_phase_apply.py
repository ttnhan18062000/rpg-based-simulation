"""
tests/unit/domains/memory/test_memory_update_phase_apply.py

TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING: guards that MemoryUpdatePhase.apply() routes through the
typed EntityUpdate/CognitionPatch apply path -- never mutating state.entities directly (Durable
State Rule) -- and that CognitionPatch/EntityUpdate.cognition_bundle_set correctly and
independently apply to entity.cognition without disturbing entity.self_model.
"""
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.core.cognition import CognitionModel
from src.core.self_model import SelfModelBundle
from src.domains.memory.phase import MemoryUpdatePhase
from src.engine.patches import extract_patches
from src.engine.apply import ApplyPath


def test_memory_update_phase_apply_does_not_mutate_state_entities():
    entity = EntityState(id=1, kind="HERO")
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity})

    original_entities = state.entities
    original_cognition = state.entities[1].cognition

    result = MemoryUpdatePhase.apply(state, StateUpdate())

    # state.entities object is untouched -- no in-place mutation.
    assert state.entities is original_entities
    assert state.entities[1].cognition is original_cognition

    entity_up = result.entity_updates.get(1)
    assert entity_up is not None
    assert entity_up.cognition_bundle_set is not None
    assert isinstance(entity_up.cognition_bundle_set, CognitionModel)
    assert entity_up.cognition_bundle_set is not original_cognition


def test_cognition_bundle_set_applies_to_entity_cognition_field():
    entity = EntityState(id=1, kind="HERO")
    original_self_model = entity.self_model

    new_cognition = CognitionModel()
    update = EntityUpdate(entity_id=1, cognition_bundle_set=new_cognition)

    patches = extract_patches(1, update)
    changes = {}
    for patch in patches:
        patch.apply(entity, changes)

    new_entity = ApplyPath._fast_replace_entity(entity, changes)

    assert new_entity.cognition is new_cognition
    assert new_entity.self_model is original_self_model
