"""
tests/unit/domains/memory/test_memory_update_phase_apply.py

TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING: guards that MemoryUpdatePhase.apply() routes through the
typed EntityUpdate/CognitionPatch apply path -- never mutating state.entities directly (Durable
State Rule) -- and that CognitionPatch/EntityUpdate.cognition_bundle_set correctly and
independently apply to entity.cognition without disturbing entity.self_model.
"""
from dataclasses import replace

from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.core.cognition import CognitionModel, MotivationModel, NamedIntentionBundle
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


def test_memory_update_reads_through_an_earlier_same_tick_cognition_write():
    """
    TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD: MemoryUpdatePhase.apply() must
    not silently discard a cognition_bundle_set an earlier phase already staged this same tick --
    EntityUpdate.merge()'s own cognition_bundle_set field is a whole-object replace, so building
    this phase's own updated CognitionModel from entity.cognition (the tick-START snapshot) instead
    of the already-accumulated `update` would clobber that earlier write once merged. This phase
    runs first in the real pipeline today, so this is a latent-risk regression test (a future phase
    reorder would silently arm it), not a reproduction of an already-observed failure.
    """
    entity = EntityState(id=1, kind="HERO")
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity})

    sentinel_intention = NamedIntentionBundle(text="avenge me", source_entity_id=99, created_tick=5)
    earlier_phase_cognition = replace(
        entity.cognition,
        motivation=replace(entity.cognition.motivation, named_intention=sentinel_intention),
    )
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, cognition_bundle_set=earlier_phase_cognition),
    })

    result = MemoryUpdatePhase.apply(state, update)

    new_cognition = result.entity_updates[1].cognition_bundle_set
    assert new_cognition is not None
    # The earlier phase's own write must survive (not discarded).
    assert new_cognition.motivation.named_intention == sentinel_intention
    # This phase's own real work (temporal urgency recalculation) must also be present -- proving
    # the two writes merged rather than one replacing the other outright.
    assert new_cognition.subjective.time is not entity.cognition.subjective.time
