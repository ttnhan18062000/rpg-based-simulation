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

class DecisionDriver(SimulationModel):
    """A structured record explaining a bias or decision driver. [phase_2_stage_9]"""
    model_config = ConfigDict(extra='forbid')
    
    kind: str # 'motive', 'personality', 'emotion', 'belief', 'social', 'biological'
    label: str
    weight: float
    description: str | None = None

@unique
class StrategicStatus(IntEnum):
    """Lifecycle status for projects and objectives."""
    ACTIVE = 0
    SUSPENDED = 1
    RESOLVED = 2
    ABANDONED = 3

@unique
class DirectiveKind(IntEnum):
    """Categories for enduring orientations."""
    IDEOLOGICAL = 0
    PROFESSIONAL = 1
    FACTIONAL = 2
    PERSONAL = 3

@unique
class ProjectKind(IntEnum):
    """Broad categories for strategic pursuits."""
    QUEST = 0
    EXPLORATION = 1
    SOCIAL = 2
    INVESTIGATION = 3
    DEVELOPMENT = 4

@unique
class ObjectiveKind(IntEnum):
    """Specific types of strategic sub-tasks."""
    VISIT = 0
    KILL = 1
    COLLECT = 2
    INTERACT = 3
    WAIT = 4
    INVESTIGATE = 5

@unique
class ConcernKind(IntEnum):
    """Immediate strategic interrupts or priorities."""
    THREAT = 0
    OPPORTUNITY = 1
    OBLIGATION = 2

@unique
class LeadKind(IntEnum):
    """Types of uncertain strategic clues."""
    LOCATION = 0
    PERSON = 1
    OBJECT = 2
    EVENT = 3

@unique
class BlockerKind(IntEnum):
    """Reasons why a project or objective cannot proceed."""
    CAPABILITY = 0
    KNOWLEDGE = 1
    SOCIAL = 2
    MATERIAL = 3
    REPUTATION = 4

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
    """Explicit reason for strategic stalling. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    blocker_id: str
    kind: BlockerKind
    label: str
    description: str = ""
    discovered_tick: int = 0

class LeadRecord(SimulationModel):
    """Uncertain clue or pointer to a strategic opportunity. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    lead_id: str
    kind: LeadKind
    label: str
    description: str = ""
    source_id: int | None = None
    
    # [PHASE 3] Spatial Uncertainty
    target_coords: Vector2 | None = None
    candidate_regions: list[str] = Field(default_factory=list)
    
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reliability: float = Field(default=1.0, ge=0.0, le=1.0) # Source quality
    
    discovered_tick: int = 0
    last_search_tick: int = 0
    is_exhausted: bool = False

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
    
    metadata: dict[str, Any] = Field(default_factory=dict)

class ConcernRecord(SimulationModel):
    """Immediate high-salience strategic interrupt. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    concern_id: str
    kind: ConcernKind
    label: str
    priority: float = Field(default=2.0, ge=0.0, le=10.0)
    source_event_id: str | None = None
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

class SocialContractRecord(SimulationModel):
    """Mutual agreement or party-based commitment. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    contract_id: str
    party_id: str | None = None
    purpose: str
    terms: dict[str, Any] = Field(default_factory=dict)
    members: list[int] = Field(default_factory=list)
    status: StrategicStatus = StrategicStatus.ACTIVE
    created_tick: int = 0
    resolved_tick: int | None = None

class StrategicState(SimulationModel):
    """Aggregate strategic stratum attached to MindAspect. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    directives: list[DirectiveRecord] = Field(default_factory=list)
    projects: list[ProjectRecord] = Field(default_factory=list)
    concerns: list[ConcernRecord] = Field(default_factory=list)
    obligations: list[ObligationRecord] = Field(default_factory=list)
    contracts: list[SocialContractRecord] = Field(default_factory=list)
    leads: list[LeadRecord] = Field(default_factory=list) # [PHASE 3]
    
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
    ObjectiveRecord.model_rebuild()
    ProjectRecord.model_rebuild()
    ConcernRecord.model_rebuild()
    ObligationRecord.model_rebuild()
    SocialContractRecord.model_rebuild()
    StrategicState.model_rebuild()

rebuild_strategic_models()
