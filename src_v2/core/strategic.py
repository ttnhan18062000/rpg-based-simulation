from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class DirectivePriority(str, Enum):
    """Priority level for strategic directives."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class ProjectStatus(str, Enum):
    """Lifecycle status of a strategic project."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class ObjectiveStatus(str, Enum):
    """Status of a project objective."""
    UNRESOLVED = "UNRESOLVED"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class LeadCertainty(str, Enum):
    """How certain a lead is."""
    PRECISE = "PRECISE"      # Direct observation
    APPROXIMATE = "APPROXIMATE"  # Heard from trusted source
    VAGUE = "VAGUE"          # Rumor / indirect
    EXHAUSTED = "EXHAUSTED"  # Tested and failed


@dataclass(frozen=True, slots=True)
class BlockerState:
    """Explicit reason for strategic stalling."""
    id: str
    kind: str  # 'material', 'capability', 'access', 'social', 'group'
    subject: str  # e.g. 'iron_ore', 'gold', 'ally'
    severity: float = 0.5
    resolved: bool = False


@dataclass(frozen=True, slots=True)
class LeadState:
    """Uncertain clue or pointer to a strategic opportunity."""
    id: str
    kind: str  # 'location', 'object', 'event', 'person'
    subject: str
    detail: str = ""
    discovered_tick: int = 0
    certainty: LeadCertainty = LeadCertainty.VAGUE
    source_entity_id: Optional[int] = None
    tested: bool = False
    test_outcome: Optional[str] = None  # 'SUCCESS', 'FAILURE', None


@dataclass(frozen=True, slots=True)
class DirectiveState:
    """Enduring strategic intention (e.g. 'AVENGE', 'EXPLORE', 'STABILIZE')."""
    id: str
    kind: str  # 'avenge', 'explore', 'stabilize', 'acquire', 'protect'
    target: Optional[str] = None  # Target entity/region/item
    priority: DirectivePriority = DirectivePriority.NORMAL
    salience: float = 0.0  # Accumulated weight from repeated events
    created_tick: int = 0


@dataclass(frozen=True, slots=True)
class ObjectiveState:
    """Concrete goal within a project."""
    id: str
    kind: str  # 'reach_location', 'acquire_item', 'defeat_enemy', 'investigate'
    target: Optional[str] = None
    status: ObjectiveStatus = ObjectiveStatus.UNRESOLVED
    blocker_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ProjectState:
    """A bounded strategic effort with objectives."""
    id: str
    kind: str  # 'crafting', 'quest', 'exploration', 'combat', 'social'
    status: ProjectStatus = ProjectStatus.ACTIVE
    score: float = 0.0  # Current evaluation score
    lock_until_tick: int = 0  # Prevents switching before this tick
    objectives: List[ObjectiveState] = field(default_factory=list)
    active_objective_id: Optional[str] = None
    created_tick: int = 0


@dataclass(frozen=True, slots=True)
class ConcernState:
    """An environmental or social pressure on the entity."""
    id: str
    kind: str  # 'danger', 'hunger', 'fatigue', 'social_threat', 'opportunity'
    source: str = ""  # Region/entity/event that caused it
    urgency: float = 0.0
    created_tick: int = 0


@dataclass(frozen=True, slots=True)
class CandidateZone:
    """A region or area of strategic interest."""
    id: str
    region_id: str
    reason: str = ""
    score: float = 0.0


@dataclass(frozen=True, slots=True)
class HypothesisState:
    """A strategic guess about the world, subject to verification."""
    id: str
    subject: str
    claim: str
    confidence: float = 0.5  # 0.0 to 1.0
    supporting_lead_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SourceTrustEntry:
    """Trust score for a specific information source."""
    entity_id: int
    trust: float = 0.5  # 0.0 to 1.0
    interactions: int = 0
    last_outcome: Optional[str] = None  # 'SUCCESS', 'FAILURE'


@dataclass(frozen=True, slots=True)
class CognitionProfile:
    """
    Profile-specific capacity limits for strategic cognition.
    Derived from entity attributes (WIS, INT, level, archetype).
    """
    max_active_projects: int = 3
    max_leads: int = 8
    max_concerns: int = 5
    max_candidate_zones: int = 4
    max_hypotheses: int = 3
    interruption_resistance: float = 0.3  # 0.0 (easy switch) to 1.0 (never switch)
    detour_breadth: int = 3  # Max detour suggestions per tick
    detour_depth: int = 2    # Max nesting depth for detour chains


@dataclass(frozen=True, slots=True)
class StrategicComponent:
    """Aggregate strategic stratum attached to an entity."""
    # Core state
    home_region_id: Optional[str] = None
    blockers: Dict[str, BlockerState] = field(default_factory=dict)
    leads: Dict[str, LeadState] = field(default_factory=dict)
    directives: Dict[str, DirectiveState] = field(default_factory=dict)
    projects: Dict[str, ProjectState] = field(default_factory=dict)
    concerns: Dict[str, ConcernState] = field(default_factory=dict)
    candidate_zones: Dict[str, CandidateZone] = field(default_factory=dict)
    hypotheses: Dict[str, HypothesisState] = field(default_factory=dict)
    source_trust: Dict[int, SourceTrustEntry] = field(default_factory=dict)

    # Active tracking
    current_project_id: Optional[str] = None
    current_objective_id: Optional[str] = None

    # Cognition profile (derived, not stored permanently)
    profile: CognitionProfile = field(default_factory=CognitionProfile)

    # Overload tracking
    primary_overload_source: Optional[str] = None
    last_overload_tick: int = 0
