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
    """Helper to read self_awareness from new nested path."""
    return entity.cognition.subjective.self.awareness

def get_need_interpretation(entity: EntityState) -> NeedInterpretationComponent:
    """Helper to read needs from new nested path."""
    return entity.cognition.subjective.self.needs

def get_capability_estimate(entity: EntityState) -> CapabilityEstimateComponent:
    """Helper to read capabilities from new nested path."""
    return entity.cognition.subjective.self.capability

def get_knowledge_model(entity: EntityState) -> KnowledgeModelComponent:
    """Helper to read knowledge from new nested path."""
    return entity.cognition.subjective.knowledge
