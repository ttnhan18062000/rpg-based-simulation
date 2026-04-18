"""Strategic domain models for durable long-term continuity. [PHASE 1]

This module defines the strategic stratum of the entity mind, providing 
first-class containers for directives, projects, objectives, and 
unfinished business.
"""

from __future__ import annotations
from enum import IntEnum, unique
import logging
from typing import Any
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.vectors import Vector2
from src.core.models.enums import (
    ContractKind, OfferStatus, StrategicStatus, DirectiveKind, 
    ProjectKind, ObjectiveKind, ConcernKind, LeadKind, BlockerKind
)
from src.core.models.cognition import CognitionCapacityProfile

logger = logging.getLogger(__name__)

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
    
    source_project_id: str | None = None # [phase_2_intel_capacity]
    
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
    source_id: str | None = None # Generic ID for trust mapping
    
    # Appraisal [phase_2_intel_capacity]
    priority: float = Field(default=1.0, ge=0.0, le=5.0)
    certainty: float = Field(default=0.5, ge=0.0, le=1.0) # [phase_3_intel_capacity]
    contradiction_count: int = 0 # [phase_3_intel_capacity]
    freshness: float = Field(default=0.5, ge=0.0, le=1.0)
    source_quality: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Uncertainty & Provenance [phase_3_task_1]
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
    approx_coords: Vector2 | None = None # Scout center [PHASE 3]
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
    
    blocker_ids: list[str] = Field(default_factory=list)
    blockers: list[BlockerRecord] = Field(default_factory=list)
    leads: list[LeadRecord] = Field(default_factory=list)
    
    # Traceability [phase_3_task_2]
    evidence_refs: list[str] = Field(default_factory=list) # lead_ids or event_ids
    spawned_from_id: str | None = None # blocker_id or project_id
    detour_depth: int = 0 # [phase_3_intel_capacity]
    
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
    
    # Appraisal [phase_2_intel_capacity]
    salience: float = Field(default=0.5, ge=0.0, le=1.0)
    last_selected_tick: int = 0
    
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
    
    # Appraisal [phase_2_intel_capacity]
    salience: float = Field(default=0.5, ge=0.0, le=1.0)
    source_project_id: str | None = None
    
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
    urgency: float = Field(default=0.5, ge=0.0, le=1.0) # [phase_2_intel_capacity]
    deadline_pressure: float = Field(default=0.0, ge=0.0, le=1.0) # [phase_2_intel_capacity]
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
    priority: float = Field(default=1.0, ge=0.0, le=5.0) # [phase_2_intel_capacity]
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
    
    # Negotiation History [phase_3_task_1]
    counter_reason: str = ""
    original_founder_id: int | None = None
    negotiation_count: int = 0
    negotiation_history: list[dict[str, Any]] = Field(default_factory=list) # [{tick, from, status, terms}]

class StrategicState(SimulationModel):
    """Aggregate strategic stratum attached to MindAspect. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    directives: list[DirectiveRecord] = Field(default_factory=list)
    blockers: list[BlockerRecord] = Field(default_factory=list)
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
    engaged_ticks: int = 0
    
    # Observability [phase_2_stage_9]
    recent_drivers: list[DecisionDriver] = Field(default_factory=list)
    
    last_strategic_tick: int = 0
    last_interpreted_event_tick: int = 0
    
    # Knowledge Continuity [phase_3_task_3]
    tested_lead_ids: list[str] = Field(default_factory=list)
    source_trust: dict[str, float] = Field(default_factory=dict) # [phase_3_intel_capacity]
    
    # Cognitive Bounding Metrics [phase_2_intel_capacity]
    last_capacity_profile: CognitionCapacityProfile | None = None
    active_slice_used: int = 0
    active_concerns_used: int = 0
    retained_leads_used: int = 0
    candidate_zones_used: int = 0
    ally_evaluations_used: int = 0
    detour_depth_used: int = 0
    dropped_candidates_count: int = 0
    latent_concerns_count: int = 0
    is_overloaded: bool = False
    overload_score: float = 0.0
    primary_overload_source: str | None = None
    last_overload_tick: int | None = None

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

    def apply_update(self, up: "StrategicUpdate") -> None:
        """Apply a StrategicUpdate to this state in-place. [AOA STABILIZATION]"""
        if up.current_project_id is not None:
            self.current_project_id = up.current_project_id
        if up.current_objective_id is not None:
            self.current_objective_id = up.current_objective_id
        if up.interrupted_project_id is not None:
            self.interrupted_project_id = up.interrupted_project_id
        if up.project_lock_until is not None:
            self.project_lock_until = up.project_lock_until
        if up.engaged_ticks is not None:
            self.engaged_ticks = up.engaged_ticks
        if up.last_interpreted_event_tick is not None:
            self.last_interpreted_event_tick = up.last_interpreted_event_tick
        
        # Collections (Add or Update)
        for d in up.directives_add:
            found = False
            for i, ex in enumerate(self.directives):
                if ex.directive_id == d.directive_id:
                    self.directives[i] = d
                    found = True
                    break
            if not found: self.directives.append(d)
        
        for p in up.projects_add_or_update:
            found = False
            for i, ex in enumerate(self.projects):
                if ex.project_id == p.project_id:
                    self.projects[i] = p
                    found = True
                    break
            if not found: self.projects.append(p)
            
        for c in up.concerns_add_or_update:
            found = False
            for i, ex in enumerate(self.concerns):
                if ex.concern_id == c.concern_id:
                    self.concerns[i] = c
                    found = True
                    break
            if not found: self.concerns.append(c)
            
        for ld in up.leads_add_or_update:
            found = False
            for i, ex in enumerate(self.leads):
                if ex.lead_id == ld.lead_id:
                    # Protection [AOA PERSISTENCE]: Don't let stale updates revert tested/exhausted flags
                    updated_ld = ld.model_copy()
                    if ex.tested: updated_ld.tested = True
                    if ex.is_exhausted: updated_ld.is_exhausted = True
                    
                    self.leads[i] = updated_ld
                    found = True
                    break
            if not found: self.leads.append(ld)

        for cz in up.candidate_zones_add_or_update:
            found = False
            for i, existing in enumerate(self.candidate_zones):
                if existing.zone_id == cz.zone_id:
                    self.candidate_zones[i] = cz
                    found = True
                    break
            if not found: self.candidate_zones.append(cz)

        for hy in up.hypotheses_add_or_update:
            found = False
            for i, existing in enumerate(self.hypotheses):
                if existing.hypothesis_id == hy.hypothesis_id:
                    self.hypotheses[i] = hy
                    found = True
                    break
            if not found: self.hypotheses.append(hy)

        for o in up.obligations_add_or_update:
            found = False
            for i, existing in enumerate(self.obligations):
                if existing.obligation_id == o.obligation_id:
                    self.obligations[i] = o
                    found = True
                    break
            if not found: self.obligations.append(o)

        for ct in up.contracts_add_or_update:
            found = False
            for i, existing in enumerate(self.contracts):
                if existing.contract_id == ct.contract_id:
                    self.contracts[i] = ct
                    found = True
                    break
            if not found: self.contracts.append(ct)

        for off in up.offers_add_or_update:
            found = False
            for i, existing in enumerate(self.offers):
                if existing.offer_id == off.offer_id:
                    self.offers[i] = off
                    found = True
                    break
            if not found: self.offers.append(off)

        for bl in up.blockers_add_or_update:
            found = False
            for i, existing in enumerate(self.blockers):
                if existing.blocker_id == bl.blocker_id:
                    self.blockers[i] = bl
                    found = True
                    break
            if not found: self.blockers.append(bl)

        # Scalar/Flag Updates
        if up.tested_lead_ids:
            for lid in up.tested_lead_ids:
                if lid not in self.tested_lead_ids: self.tested_lead_ids.append(lid)

        # Removes
        if up.directives_remove:
            self.directives = [d for d in self.directives if d.directive_id not in up.directives_remove]
        if up.projects_remove:
            self.projects = [p for p in self.projects if p.project_id not in up.projects_remove]
        if up.concerns_remove:
            self.concerns = [c for c in self.concerns if c.concern_id not in up.concerns_remove]
        if up.leads_remove:
            self.leads = [ld for ld in self.leads if ld.lead_id not in up.leads_remove]
        if up.candidate_zones_remove:
            self.candidate_zones = [cz for cz in self.candidate_zones if cz.zone_id not in up.candidate_zones_remove]
        if up.hypotheses_remove:
            self.hypotheses = [hy for hy in self.hypotheses if hy.hypothesis_id not in up.hypotheses_remove]
        if up.obligations_remove:
            self.obligations = [o for o in self.obligations if o.obligation_id not in up.obligations_remove]
        if up.contracts_remove:
            self.contracts = [ct for ct in self.contracts if ct.contract_id not in up.contracts_remove]
        if up.offers_remove:
            self.offers = [off for off in self.offers if off.offer_id not in up.offers_remove]
        if up.blockers_remove:
            self.blockers = [bl for bl in self.blockers if bl.blocker_id not in up.blockers_remove]
            
        # [phase_3_intel_capacity]
        if up.source_trust_updates:
            self.source_trust.update(up.source_trust_updates)

        # Cognitive Metrics & Overload
        if up.last_capacity_profile is not None: self.last_capacity_profile = up.last_capacity_profile
        if up.active_slice_used is not None: self.active_slice_used = up.active_slice_used
        if up.active_concerns_used is not None: self.active_concerns_used = up.active_concerns_used
        if up.retained_leads_used is not None: self.retained_leads_used = up.retained_leads_used
        if up.candidate_zones_used is not None: self.candidate_zones_used = up.candidate_zones_used
        if up.ally_evaluations_used is not None: self.ally_evaluations_used = up.ally_evaluations_used
        if up.detour_depth_used is not None: self.detour_depth_used = up.detour_depth_used
        if up.dropped_candidates_count is not None: self.dropped_candidates_count = up.dropped_candidates_count
        if up.latent_concerns_count is not None: self.latent_concerns_count = up.latent_concerns_count
        if up.is_overloaded is not None: self.is_overloaded = up.is_overloaded
        if up.overload_score is not None: self.overload_score = up.overload_score
        if up.primary_overload_source is not None: self.primary_overload_source = up.primary_overload_source
        if up.last_overload_tick is not None: self.last_overload_tick = up.last_overload_tick
        
        # Traceability
        if up.strategic_drivers:
            self.recent_drivers = up.strategic_drivers

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
