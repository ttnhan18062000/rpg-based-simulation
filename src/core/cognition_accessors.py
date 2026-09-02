# Compatibility Accessors for Phase 11 Migration

from src.core.state import EntityState
from src.core.cognition import CognitionModel
from src.core.self_model import (
    SelfAwarenessComponent,
    NeedInterpretationComponent,
    CapabilityEstimateComponent,
    KnowledgeModelComponent
)

def get_self_awareness(entity: EntityState) -> SelfAwarenessComponent:
    """Reads self_awareness from the real entity.self_model path (SelfModelBundle)."""
    return entity.self_model.self_awareness

def get_need_interpretation(entity: EntityState) -> NeedInterpretationComponent:
    """Reads needs from the real entity.self_model path (SelfModelBundle)."""
    return entity.self_model.needs

def get_capability_estimate(entity: EntityState) -> CapabilityEstimateComponent:
    """Reads capabilities from the real entity.self_model path (SelfModelBundle)."""
    return entity.self_model.capabilities

def get_knowledge_model(entity: EntityState) -> KnowledgeModelComponent:
    """Helper to read knowledge from new nested path."""
    return entity.cognition.subjective.knowledge
