"""
src/domains/world_emergence/schema.py
───────────────────────────────────────────────────────────────────────────────
Phase 8 — World Emergence Typed Models and Schemas.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models.quests import QuestOpportunity

class WorldEventCategory(str, Enum):
    ENTITY_DEATH = "ENTITY_DEATH"
    NEAR_DEATH = "NEAR_DEATH"
    RESOURCE_HARVESTED = "RESOURCE_HARVESTED"
    RESOURCE_DEPLETED = "RESOURCE_DEPLETED"
    RESOURCE_RECOVERED = "RESOURCE_RECOVERED"
    QUEST_COMPLETED = "QUEST_COMPLETED"
    QUEST_FAILED = "QUEST_FAILED"
    CAMP_CLEARED = "CAMP_CLEARED"
    CAMP_RAID = "CAMP_RAID"
    SHOP_STOCK_DEPLETED = "SHOP_STOCK_DEPLETED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    REGION_ENTERED = "REGION_ENTERED"
    REGION_AVOIDED = "REGION_AVOIDED"
    RUMOR_CONFIRMED = "RUMOR_CONFIRMED"
    RUMOR_CONTRADICTED = "RUMOR_CONTRADICTED"
    PARTY_ABANDONED = "PARTY_ABANDONED"
    # E52A: Demographic cycle events
    POPULATION_BIRTH = "POPULATION_BIRTH"
    POPULATION_DEATH = "POPULATION_DEATH"
    # E52B: Migration pressure
    POPULATION_MIGRATION = "POPULATION_MIGRATION"
    # E53Bd: Diplomatic transition events
    FACTION_WAR_DECLARED = "FACTION_WAR_DECLARED"
    FACTION_ALLIANCE_FORMED = "FACTION_ALLIANCE_FORMED"
    FACTION_PEACE_TREATY = "FACTION_PEACE_TREATY"
    # E53Cc: Territory transfer via siege completion
    TERRITORY_TRANSFERRED = "TERRITORY_TRANSFERRED"
    # E53Cd: War exhaustion peace resolution
    WAR_ENDED_EXHAUSTION = "WAR_ENDED_EXHAUSTION"
    # E53Db: Siege onset and betrayal
    SIEGE_BEGINS = "SIEGE_BEGINS"
    BETRAYAL = "BETRAYAL"

@dataclass(frozen=True, slots=True)
class WorldEvent:
    category: WorldEventCategory
    tick: int
    region_id: Optional[str] = None
    subject: Optional[str] = None
    severity: float = 1.0
    payload: Dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class WorldEventAggregate:
    region_id: Optional[str]
    category: WorldEventCategory
    subject: Optional[str]
    count: int
    severity_sum: float
    first_tick: int
    last_tick: int

@dataclass(frozen=True, slots=True)
class RegionalPressure:
    region_id: str
    pressure_kind: str
    intensity: float
    confidence: float
    source_aggregates: Tuple[str, ...]
    reason: str

@dataclass(frozen=True, slots=True)
class ResourceScarcitySignal:
    region_id: str
    resource_type: str
    availability: float
    scarcity_level: float
    trend: str
    confidence: float
    reason: str

@dataclass(frozen=True, slots=True)
class WorldOpportunityPressure:
    id: str
    kind: str
    region_id: str
    subject: Optional[str]
    urgency: float
    suggested_opportunity_kinds: Tuple[str, ...]
    reason: str

@dataclass(frozen=True, slots=True)
class QuestSeed:
    id: str
    kind: str
    region_id: str
    subject: Optional[str]
    difficulty_hint: int
    reward_hint: int
    urgency: float
    source_pressure_id: str
    valid_resolution_tags: Tuple[str, ...]

@dataclass(frozen=True, slots=True)
class RumorSeed:
    id: str
    subject: str
    region_id: Optional[str]
    certainty: float
    source_kind: str
    spread_scope: str
    reason: str

@dataclass(frozen=True, slots=True)
class ServicePressure:
    service_id: str
    pressure_kind: str
    intensity: float
    effect_tags: Tuple[str, ...]
    reason: str

@dataclass(frozen=True, slots=True)
class WorldEmergenceResult:
    pressures: Tuple[RegionalPressure, ...] = field(default_factory=tuple)
    scarcity: Tuple[ResourceScarcitySignal, ...] = field(default_factory=tuple)
    opportunities: Tuple[WorldOpportunityPressure, ...] = field(default_factory=tuple)
    quest_seeds: Tuple[QuestSeed, ...] = field(default_factory=tuple)
    rumor_seeds: Tuple[RumorSeed, ...] = field(default_factory=tuple)
    service_pressures: Tuple[ServicePressure, ...] = field(default_factory=tuple)
    quest_opportunities: Tuple[QuestOpportunity, ...] = field(default_factory=tuple)
