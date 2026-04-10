"""Strategic domain models for durable long-term continuity. [PHASE 1]

This module defines the strategic stratum of the entity mind, providing 
first-class containers for directives, projects, objectives, and 
unfinished business.
"""

from __future__ import annotations
from enum import IntEnum, unique
from typing import Any
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.vectors import Vector2
from src.core.models.enums import (
    ContractKind, OfferStatus, StrategicStatus, DirectiveKind, 
    ProjectKind, ObjectiveKind, ConcernKind, LeadKind, BlockerKind
)

class DecisionDriver(SimulationModel):
    """A structured record explaining a bias or decision driver. [phase_2_stage_9]"""
    model_config = ConfigDict(extra='forbid')
    
    kind: str # 'motive', 'personality', 'emotion', 'belief', 'social', 'biological'
    label: str
    weight: float
    description: str | None = None

class DirectiveRecord(SimulationModel):
    """Enduring orientations rooted in identity or role. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    directive_id: str
    kind: DirectiveKind = DirectiveKind.PERSONAL
    label: str
    priority: float = Field(default=1.0, ge=0.0, le=5.0)
    source: str = "" # e.g. "archetype", "role", "history"
    created_tick: int = 0

class BlockerRecord(SimulationModel):
    """Explicit reason for strategic stalling. [phase_3_task_2]"""
    model_config = ConfigDict(extra='forbid')
    
    blocker_id: str
    kind: BlockerKind
    label: str
    subject_ref: str | int | None = None # e.g. "iron_ore", entity_id
    
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Traceability [phase_3_task_2]
    evidence_refs: list[str] = Field(default_factory=list) # lead_ids or event_ids
    spawned_from_id: str | None = None # project_id or objective_id
    
    # Detour logic [phase_3_task_2]
    suggested_detour_types: list[ObjectiveKind] = Field(default_factory=list)
    
    resolved: bool = False
    superseded_by_id: str | None = None # successor blocker_id
    
    discovered_tick: int = 0

class LeadRecord(SimulationModel):
    """Uncertain clue or pointer to a strategic opportunity. [phase_3_task_1]"""
    model_config = ConfigDict(extra='forbid')
    
    lead_id: str
    kind: LeadKind
    label: str
    subject: str = "" # [phase_3_task_1]
    
    # Optional Exact Targets (for precise leads/verified outcomes)
    target_coords: Vector2 | None = None
    target_entity_id: int | None = None
    
    source_type: str = "" # e.g. "guild", "gossip", "observation"
    source_entity_id: int | None = None
    
    # Uncertainty & Provenance [phase_3_task_1]
    certainty: float = Field(default=0.5, ge=0.0, le=1.0)
    directness: float = Field(default=1.0, ge=0.0, le=1.0) # 1.0 = direct, <1.0 = gossiped
    source_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    freshness_tick: int = 0
    discovered_tick: int = 0
    
    # Semantic Context [phase_3_task_1]
    semantic_tags: list[str] = Field(default_factory=list)
    interpreted_meaning: str = ""
    related_project_ids: list[str] = Field(default_factory=list)
    
    # Status & Hypothesis Links [phase_3_task_1]
    tested: bool = False
    contradiction_count: int = 0
    
    candidate_zone_ids: list[str] = Field(default_factory=list)
    candidate_entity_ids: list[int] = Field(default_factory=list)
    candidate_topic_ids: list[str] = Field(default_factory=list)
    
    last_search_tick: int = 0
    is_exhausted: bool = False

class CandidateZoneRecord(SimulationModel):
    """Represented hypothesized region or site of interest. [phase_3_task_1]"""
    model_config = ConfigDict(extra='forbid')
    
    zone_id: str
    region_id: str | None = None # Anchor region
    region_tags: list[str] = Field(default_factory=list) # e.g. "mountain", "swamp"
    
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_lead_ids: list[str] = Field(default_factory=list)
    contradiction_count: int = 0
    
    last_search_tick: int = 0
    search_outcome: str = "" # "empty", "evidence_found", "danger_high"
    visited_tiles: list[tuple[int, int]] = Field(default_factory=list) # [phase_3_task_8]

class HypothesisRecord(SimulationModel):
    """Narrowed interpretation of multiple leads. [phase_3_task_1]"""
    model_config = ConfigDict(extra='forbid')
    
    hypothesis_id: str
    label: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_lead_ids: list[str] = Field(default_factory=list)
    contradicted_by_lead_ids: list[str] = Field(default_factory=list)
    
    is_active: bool = True
    resolved_tick: int | None = None

class ObjectiveRecord(SimulationModel):
    """Concrete sub-task within a project. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    objective_id: str
    project_id: str
    kind: ObjectiveKind
    label: str
    status: StrategicStatus = StrategicStatus.ACTIVE
    
    priority: float = Field(default=1.0, ge=0.0, le=5.0)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    
    target_id: int | None = None
    target_pos: Vector2 | None = None
    
    blockers: list[BlockerRecord] = Field(default_factory=list)
    leads: list[LeadRecord] = Field(default_factory=list)
    
    # Traceability [phase_3_task_2]
    evidence_refs: list[str] = Field(default_factory=list) # lead_ids or event_ids
    spawned_from_id: str | None = None # blocker_id or project_id
    
    created_tick: int = 0
    resolved_tick: int | None = None

class ProjectRecord(SimulationModel):
    """Durable long-term pursuit with lifecycle tracking. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    project_id: str
    kind: ProjectKind
    label: str
    status: StrategicStatus = StrategicStatus.ACTIVE
    
    priority: float = Field(default=1.0, ge=0.0, le=5.0)
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    emotional_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    reversibility: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Continuity & Commitment [phase_2_stage_3]
    committed_at: int = 0
    abandonment_cost: float = Field(default=0.5, ge=0.0, le=1.0)
    interruption_threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    interruption_policy: str = "default" # "ignore_minor", "ignore_all", "default"
    
    objectives: list[ObjectiveRecord] = Field(default_factory=list)
    active_objective_id: str | None = None
    
    created_tick: int = 0
    updated_tick: int = 0
    resolved_tick: int | None = None
    
    # Project Interruption & Recovery [PHASE 5]
    interrupted_by_event_ids: list[str] = Field(default_factory=list)
    suspension_reason: str = ""
    recovery_behavior: str = "default" # "resume", "restart", "abandon"
    
    mutation_source_id: str | None = None # project_id that this project mutated from
    split_from_id: str | None = None # project_id that this project split from
    
    resume_conditions: dict[str, Any] = Field(default_factory=dict)
    abandonment_reason: str = ""
    symbolic_closure_required: bool = False
    
    metadata: dict[str, Any] = Field(default_factory=dict)

class ConcernRecord(SimulationModel):
    """Immediate high-salience strategic interrupt. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    concern_id: str
    kind: ConcernKind
    label: str
    priority: float = Field(default=2.0, ge=0.0, le=10.0)
    
    # Context & History [PHASE 5]
    cause_type: str = "" # e.g. "event", "scar", "environmental"
    source_event_id: str | None = None
    linked_scar_ids: list[str] = Field(default_factory=list)
    
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    irreversibility: float = Field(default=0.0, ge=0.0, le=1.0)
    attachment_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    social_cost: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Visibility [PHASE 5]
    visibility: str = "private" # 'private', 'shared', 'public'
    
    created_tick: int = 0
    resolved_tick: int | None = None

class ObligationRecord(SimulationModel):
    """Unilateral duty or debt to another entity. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    obligation_id: str
    target_id: int
    label: str
    priority: float = Field(default=1.0, ge=0.0, le=5.0)
    deadline_tick: int | None = None
    created_tick: int = 0
    resolved_tick: int | None = None

class ContractTermRecord(SimulationModel):
    """Specific clause within a social contract. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')
    
    term_type: str # 'payout', 'protection', 'duration', 'behavior'
    label: str
    params: dict[str, Any] = Field(default_factory=dict)

class SocialContractRecord(SimulationModel):
    """Mutual agreement or party-based commitment. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')
    
    contract_id: str
    kind: ContractKind
    purpose: str
    formation_reason: str = ""
    
    project_id: str | None = None # The underlying strategic project
    party_id: str | None = None # Linked tactical GroupRecord ID
    
    founder_id: int
    member_ids: list[int] = Field(default_factory=list)
    invited_ids: list[int] = Field(default_factory=list)
    member_roles: dict[int, str] = Field(default_factory=dict) # entity_id -> role_name
    
    required_roles: dict[str, int] = Field(default_factory=dict) # role_name -> count
    reward_logic: str = "equal_split" # 'fixed', 'equal_split', 'performance'
    
    terms: list[ContractTermRecord] = Field(default_factory=list)
    fallback_conditions: list[str] = Field(default_factory=list)
    dissolution_conditions: list[str] = Field(default_factory=list)
    
    status: StrategicStatus = StrategicStatus.ACTIVE
    created_tick: int = 0
    expires_tick: int | None = None
    
    breach_history: list[dict[str, Any]] = Field(default_factory=list)
    visibility: str = "party" # 'public', 'party', 'private'
    
    resolved_tick: int | None = None

class RecruitmentOfferRecord(SimulationModel):
    """A proposal for cooperation between entities. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')
    
    offer_id: str
    recruiter_id: int
    candidate_id: int
    contract_kind: ContractKind
    project_id: str | None = None
    
    proposed_terms: list[ContractTermRecord] = Field(default_factory=list)
    
    status: OfferStatus = OfferStatus.PENDING
    created_tick: int = 0
    expires_tick: int | None = None

class StrategicState(SimulationModel):
    """Aggregate strategic stratum attached to MindAspect. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    directives: list[DirectiveRecord] = Field(default_factory=list)
    projects: list[ProjectRecord] = Field(default_factory=list)
    concerns: list[ConcernRecord] = Field(default_factory=list)
    obligations: list[ObligationRecord] = Field(default_factory=list)
    contracts: list[SocialContractRecord] = Field(default_factory=list)
    offers: list[RecruitmentOfferRecord] = Field(default_factory=list) # [PHASE 4]
    leads: list[LeadRecord] = Field(default_factory=list)
    candidate_zones: list[CandidateZoneRecord] = Field(default_factory=list) # [phase_3_task_1]
    hypotheses: list[HypothesisRecord] = Field(default_factory=list) # [phase_3_task_1]
    
    current_project_id: str | None = None
    current_objective_id: str | None = None
    interrupted_project_id: str | None = None
    
    # Continuity [phase_2_stage_3]
    project_lock_until: int = 0
    
    # Observability [phase_2_stage_9]
    recent_drivers: list[DecisionDriver] = Field(default_factory=list)
    
    last_strategic_tick: int = 0

    @property
    def current_project(self) -> ProjectRecord | None:
        """Resolve the active project record from current_project_id."""
        if not self.current_project_id:
            return None
        return next((p for p in self.projects if p.project_id == self.current_project_id), None)

    @property
    def current_objective(self) -> ObjectiveRecord | None:
        """Resolve the active objective record from current_objective_id."""
        prj = self.current_project
        if not prj or not self.current_objective_id:
            return None
        return next((o for o in prj.objectives if o.objective_id == self.current_objective_id), None)

# --- Pydantic model rebuilds ---
def rebuild_strategic_models():
    """Resolve forward references in strategic models."""
    DirectiveRecord.model_rebuild()
    BlockerRecord.model_rebuild()
    LeadRecord.model_rebuild()
    CandidateZoneRecord.model_rebuild()
    HypothesisRecord.model_rebuild()
    ObjectiveRecord.model_rebuild()
    ProjectRecord.model_rebuild()
    ConcernRecord.model_rebuild()
    ObligationRecord.model_rebuild()
    ContractTermRecord.model_rebuild()
    SocialContractRecord.model_rebuild()
    RecruitmentOfferRecord.model_rebuild()
    StrategicState.model_rebuild()

rebuild_strategic_models()
