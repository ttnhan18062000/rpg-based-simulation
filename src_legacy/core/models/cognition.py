from __future__ import annotations
from src_legacy.core.models.base import SimulationModel
from pydantic import ConfigDict

class CognitionCapacityProfile(SimulationModel):
    """Exact data contract for bounded metacognition.
    
    This model defines the cognition quality of an entity, decomposed into
    planning, judgment, evidence handling, and social bandwidth.
    """
    model_config = ConfigDict(extra='forbid')
    
    planning_budget: int
    judgment_stability: float
    evidence_quality: float
    social_bandwidth: int
    detour_depth_limit: int
    active_slice_limit: int
    concern_intake_limit: int
    lead_retention_limit: int
    candidate_zone_limit: int
    ally_evaluation_limit: int
    blocker_resolution_patience: float
    resume_reliability: float
    interruption_resistance: float
    abandonment_threshold_mod: float
    contradiction_sensitivity: float
    source_trust_learning_rate: float
