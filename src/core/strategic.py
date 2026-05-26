# Compliance IDs: API-006, API-007, API-008, DATA-077, DATA-114, DATA-121, DATA-122, DATA-123, INFRA-006, INFRA-151, INFRA-152, SOC-003, SOC-006, SOC-017, SOC-023, SOC-025, SOC-029, SOC-030, SOC-037, STRAT-001, STRAT-002, STRAT-003, STRAT-004, STRAT-005, STRAT-006, STRAT-012, STRAT-013, STRAT-014, STRAT-018, STRAT-023, STRAT-024, STRAT-025, STRAT-026, STRAT-027, STRAT-030, STRAT-031, STRAT-033, STRAT-049, STRAT-050, STRAT-051, STRAT-052, STRAT-054, STRAT-056, STRAT-075, STRAT-094, STRAT-101, STRAT-106, STRAT-107, STRAT-109, STRAT-110, STRAT-111, STRAT-112, STRAT-113, STRAT-138, STRAT-141, STRAT-142, STRAT-143, STRAT-149, STRAT-150, STRAT-151, STRAT-152, STRAT-153, STRAT-154, STRAT-155, STRAT-156, STRAT-161, STRAT-163, STRAT-168, STRAT-176, STRAT-177, STRAT-178, STRAT-179, STRAT-180, STRAT-181, STRAT-182, STRAT-183, STRAT-184, STRAT-185, STRAT-186, STRAT-187, STRAT-188, STRAT-189, STRAT-190, STRAT-191, STRAT-192, STRAT-193, STRAT-194, STRAT-195, STRAT-197
# Compliance IDs: SOC-003, SOC-006, STRAT-001, STRAT-060, STRAT-061, STRAT-062, STRAT-063, STRAT-191, STRAT-192, STRAT-193, STRAT-194, STRAT-201, STRAT-202, STRAT-203, STRAT-214, SUB-022
# Compliance IDs: STRAT-060, STRAT-061, STRAT-062, STRAT-063, SUB-022
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


class ContractStatus(str, Enum):
    """Lifecycle status of a social contract."""
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    COUNTERED = "COUNTERED"
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    COMPLETED = "FULFILLED" # Alias for project-like completion
    FAILED = "FAILED"
    BETRAYED = "BETRAYED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ContractKind(str, Enum):
    """Types of social contracts."""
    RECRUITMENT = "RECRUITMENT"
    LOAN = "LOAN"
    PROTECTION = "PROTECTION"
    MERCHANT = "MERCHANT"

    # Movement/social coordination:
    # One entity asks another to swap adjacent positions.
    POSITION_SWAP = "POSITION_SWAP"
    

class DirectiveKind(str, Enum):
    """Types of strategic directives."""
    AVENGE = "avenge"
    EXPLORE = "explore"
    STABILIZE = "stabilize"
    ACQUIRE = "acquire"
    PROTECT = "protect"
    COMBAT = "combat"


class BlockerKind(str, Enum):
    """Types of strategic blockers."""
    MATERIAL = "material"
    CAPABILITY = "capability"
    ACCESS = "access"
    SOCIAL = "social"
    GROUP = "group"


class ObjectiveKind(str, Enum):
    """Types of project objectives."""
    REACH_LOCATION = "reach_location"
    ACQUIRE_ITEM = "acquire_item"
    DEFEAT_ENEMY = "defeat_enemy"
    INVESTIGATE = "investigate"


class GoalKind(str, Enum):
    """Types of strategic goals/scorers."""
    HARVESTING = "harvesting"
    FATIGUE = "fatigue"
    HUNGER = "hunger"
    SOCIAL = "social"
    TOWN_RETURN = "town_return"
    COMBAT_ENGAGE = "combat_engage"
    COMBAT_RETREAT = "combat_retreat"
    RECOVER = "recover"
    RESOLVE_BLOCKER = "resolve_blocker"


class ProjectKind(str, Enum):
    """Types of strategic projects."""
    CRAFTING = "crafting"
    QUEST = "quest"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    SOCIAL = "social"


class ConcernKind(str, Enum):
    """Types of strategic concerns."""
    DANGER = "danger"
    HUNGER = "hunger"
    FATIGUE = "fatigue"
    SOCIAL_THREAT = "social_threat"
    OPPORTUNITY = "opportunity"


class TurningPointKind(str, Enum):
    """Types of significant life events."""
    BETRAYAL = "betrayal"
    NEAR_DEATH = "near_death"
    FIRST_KILL = "first_kill"
    GREAT_VICTORY = "great_victory"
    LOSS = "loss"


class RiskLevel(str, Enum):
    """Subjective risk assessment."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass(frozen=True, slots=True)
class ContractState:
    """
    A formal obligation between two or more parties.
    VERIFIED v2: ContractState
    """
    id: str
    kind: ContractKind
    source_id: int
    target_id: int
    terms: Dict[str, Any] = field(default_factory=dict)
    expiry_tick: int = -1
    status: ContractStatus = ContractStatus.OFFERED
    created_tick: int = 0
    negotiation_count: int = 0


@dataclass(frozen=True, slots=True)
class BlockerState:
    """Explicit reason for strategic stalling."""
    id: str
    kind: BlockerKind
    subject: str  # e.g. 'iron_ore', 'gold', 'ally'
    severity: float = 0.5
    resolved: bool = False
    target_quantity: int = 1


@dataclass(frozen=True, slots=True)
class LeadState:
    """Uncertain clue or pointer to a strategic opportunity."""
    id: str
    kind: str  # 'location', 'object', 'event', 'person'
    subject: str
    detail: str = ""
    discovered_tick: int = 0
    certainty: LeadCertainty = LeadCertainty.VAGUE # VERIFIED v2: LeadState.certainty
    source_entity_id: Optional[int] = None
    tested: bool = False
    test_outcome: Optional[str] = None  # 'SUCCESS', 'FAILURE', None
    failure_count: int = 0
    suppression_until_tick: int = 0


@dataclass(frozen=True, slots=True)
class DirectiveState:
    """Enduring strategic intention (e.g. 'AVENGE', 'EXPLORE', 'STABILIZE')."""
    id: str
    kind: DirectiveKind
    target: Optional[str] = None  # Target entity/region/item
    priority: DirectivePriority = DirectivePriority.NORMAL
    salience: float = 0.0  # Accumulated weight from repeated events
    created_tick: int = 0


@dataclass(frozen=True, slots=True)
class ObjectiveState:
    """Concrete goal within a project."""
    id: str
    kind: ObjectiveKind
    target: Optional[str] = None
    target_position: Optional[tuple[float, float]] = None
    status: ObjectiveStatus = ObjectiveStatus.UNRESOLVED
    blocker_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ProjectState:
    """A bounded strategic effort with objectives."""
    id: str
    kind: ProjectKind
    status: ProjectStatus = ProjectStatus.ACTIVE
    score: float = 0.0  # Current evaluation score
    lock_until_tick: int = 0  # Prevents switching before this tick
    objectives: List[ObjectiveState] = field(default_factory=list)
    active_objective_id: Optional[str] = None
    created_tick: int = 0
    failure_count: int = 0


@dataclass(frozen=True, slots=True)
class ConcernState:
    """An environmental or social pressure on the entity."""
    id: str
    kind: ConcernKind
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
class TurningPointState:
    """
    A significant life event that persistently biases future behavior.
    VERIFIED v2: LifeEvent
    """
    id: str
    kind: TurningPointKind
    subject_id: Optional[int] = None  # Related entity
    salience: float = 0.5  # How impactful (0.0 to 1.0)
    tick: int = 0


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
    max_turning_points: int = 20
    interruption_resistance: float = 0.3  # 0.0 (easy switch) to 1.0 (never switch)
    resistance_multiplier: float = 30.0   # Scales resistance into project utility score
    detour_breadth: int = 3  # Max detour suggestions per tick
    reserved_detour_depth: int = 2    # Max nesting depth for detour chains (reserved for future recursive planning)


@dataclass(frozen=True, slots=True)
class StrategicComponent:
    """
    Aggregate strategic stratum attached to an entity.
    VERIFIED v2: StrategicComponent
    """
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
    contracts: Dict[str, ContractState] = field(default_factory=dict)
    turning_points: List[TurningPointState] = field(default_factory=list)
    beliefs: Dict[str, Any] = field(default_factory=dict)

    # Active tracking
    current_project_id: Optional[str] = None
    current_objective_id: Optional[str] = None

    # Cognition profile (derived, not stored permanently)
    profile: CognitionProfile = field(default_factory=CognitionProfile)

    # Overload tracking
    primary_overload_source: Optional[str] = None
    last_overload_tick: int = 0

    # Boredom (PH5 M2)
    boredom: Dict[str, float] = field(default_factory=dict) # GoalKind -> score
