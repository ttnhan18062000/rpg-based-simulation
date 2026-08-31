import dataclasses

import pytest
from src.core.state import EntityState
from src.core.cognition import (
    CognitionModel,
    SubjectiveModel,
    MemoryModel,
    MotivationModel,
    CommitmentModel,
    RelationshipModel,
    EmotionalModel,
    TemporalModel,
    RiskModel
)
from src.core.cognition_accessors import (
    get_self_awareness,
    get_need_interpretation,
    get_capability_estimate,
    get_knowledge_model
)

def test_entity_state_has_default_cognition_model():
    entity = EntityState(id=1, kind="HERO")
    assert isinstance(entity.cognition, CognitionModel)
    assert isinstance(entity.cognition.subjective, SubjectiveModel)
    assert isinstance(entity.cognition.memory, MemoryModel)
    assert isinstance(entity.cognition.motivation, MotivationModel)
    assert isinstance(entity.cognition.commitment, CommitmentModel)
    assert isinstance(entity.cognition.relationships, RelationshipModel)

def test_cognition_model_default_is_empty_and_safe():
    cog = CognitionModel.empty()
    assert isinstance(cog.subjective.emotion, EmotionalModel)
    assert isinstance(cog.subjective.time, TemporalModel)
    assert isinstance(cog.subjective.risk, RiskModel)

def test_cognition_model_serializes_deterministically():
    cog1 = CognitionModel.empty()
    cog2 = CognitionModel.empty()
    assert cog1.to_canonical_dict() == cog2.to_canonical_dict()

def test_subjective_model_has_no_self_field():
    field_names = {f.name for f in dataclasses.fields(SubjectiveModel)}
    assert "self" not in field_names

def test_cognition_canonical_dict_shape_after_self_model_decision():
    subjective_dict = CognitionModel.empty().to_canonical_dict()["subjective"]
    assert "self" not in subjective_dict

def test_cognition_accessors_read_real_self_model_path():
    entity = EntityState(id=1, kind="HERO")
    assert get_self_awareness(entity) == entity.self_model.self_awareness
    assert get_need_interpretation(entity) == entity.self_model.needs
    assert get_capability_estimate(entity) == entity.self_model.capabilities
    assert get_knowledge_model(entity) == entity.cognition.subjective.knowledge
