from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING, List
if TYPE_CHECKING:
    from src_v2.core.strategic import (
        BlockerState, LeadState, DirectiveState, ProjectState,
        ConcernState, CandidateZone, HypothesisState, SourceTrustEntry,
        CognitionProfile
    )


@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    """Multi-tick progress update."""
    target_node_id: Optional[int] = None
    progress_delta: float = 0.0
    reset: bool = False

@dataclass(frozen=True, slots=True)
class CombatUpdate:
    """Authoritative combat interaction results."""
    damage_taken: int = 0
    hp_delta: int = 0
    attacker_id: Optional[int] = None
    is_opportunity_attack: bool = False
    alive_set: Optional[bool] = None
    outcome_kind: str = "SURVIVE" # SURVIVE, DEFEAT, KILL
    is_lethal: bool = False
    max_hp_delta: int = 0

@dataclass(frozen=True, slots=True)
class NavigationUpdate:
    """Updates to movement intent and pathfinding."""
    target_set: Optional[tuple[float, float]] = None
    path_set: Optional[List[tuple[float, float]]] = None
    moved_recently_set: Optional[bool] = None
    failure_reason: Optional[str] = None

@dataclass(frozen=True, slots=True)
class TaskUpdate:
    """Updates to next-tick work intent."""
    work_kind_set: Optional[str] = None
    payload_set: Optional[Dict[str, Any]] = None
    
@dataclass(frozen=True, slots=True)
class IdentityUpdate:
    """Updates to characteristics or knowledge."""
    role_set: Optional[int] = None
    faction_set: Optional[int] = None
    recipes_learned: list[str] = field(default_factory=list)
    craft_target: Optional[str] = None
    evolution_level_set: Optional[int] = None
    evolution_points_delta: int = 0

@dataclass(frozen=True, slots=True)
class SocialUpdate:
    """Updates to trust, reputation, and betrayal history."""
    trust_delta: Dict[int, float] = field(default_factory=dict) # EntityID -> Delta
    betrayal_increment: int = 0
    reputation_set: Optional[float] = None
    

@dataclass(frozen=True, slots=True)
class BiologicalUpdate:
    """Updates to sleep, hunger, and biological pressures."""
    sleep_debt_delta: float = 0.0
    hunger_delta: float = 0.0
    rest_pressure_delta: float = 0.0
    last_meal_tick_set: Optional[int] = None
    last_sleep_tick_set: Optional[int] = None
    well_rested_until_set: Optional[int] = None
    

@dataclass(frozen=True, slots=True)
class LifecycleUpdate:
    """Updates to aging and death mechanics."""
    age_delta: int = 0
    is_permadeath_set: Optional[bool] = None
    death_tick_set: Optional[int] = None
    death_reason_set: Optional[str] = None
    heir_entity_id_set: Optional[int] = None
    heirlooms_add: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class StrategicUpdate:
    """Updates to strategic markers (blockers, leads, directives, projects, concerns, etc.)."""
    # Blockers
    blockers_add_or_update: list[BlockerState] = field(default_factory=list)
    blockers_remove: list[str] = field(default_factory=list)
    # Leads
    leads_add_or_update: list[LeadState] = field(default_factory=list)
    leads_remove: list[str] = field(default_factory=list)
    # Directives
    directives_add_or_update: list[DirectiveState] = field(default_factory=list)
    directives_remove: list[str] = field(default_factory=list)
    # Projects
    projects_add_or_update: list[ProjectState] = field(default_factory=list)
    projects_remove: list[str] = field(default_factory=list)
    current_project_id_set: Optional[str] = None
    current_objective_id_set: Optional[str] = None
    # Concerns
    concerns_add_or_update: list[ConcernState] = field(default_factory=list)
    concerns_remove: list[str] = field(default_factory=list)
    # Candidate Zones
    candidate_zones_add_or_update: list[CandidateZone] = field(default_factory=list)
    candidate_zones_remove: list[str] = field(default_factory=list)
    # Hypotheses
    hypotheses_add_or_update: list[HypothesisState] = field(default_factory=list)
    hypotheses_remove: list[str] = field(default_factory=list)
    # Source Trust
    source_trust_updates: list[SourceTrustEntry] = field(default_factory=list)
    # Overload
    overload_source_set: Optional[str] = None
    overload_tick_set: Optional[int] = None

@dataclass(frozen=True, slots=True)
class InventoryUpdate:
    """Authoritative inventory changes."""
    items_added: list[str] = field(default_factory=list)
    items_removed: list[str] = field(default_factory=list)
    gold_delta: int = 0


@dataclass(frozen=True, slots=True)
class EntityUpdate:
    """
    Authoritative update for a single entity.
    """
    entity_id: int
    kind_set: Optional[str] = None
    new_position: Optional[tuple[float, float]] = None
    moved_this_tick: bool = False
    readiness_delta: float = 0.0
    active: Optional[bool] = None
    interaction: Optional[InteractionUpdate] = None
    identity: Optional[IdentityUpdate] = None
    inventory: Optional[InventoryUpdate] = None
    strategic: Optional[StrategicUpdate] = None
    social: Optional[SocialUpdate] = None
    biological: Optional[BiologicalUpdate] = None
    lifecycle: Optional[LifecycleUpdate] = None
    combat: Optional[CombatUpdate] = None
    navigation: Optional[NavigationUpdate] = None
    task: Optional[TaskUpdate] = None
    property_updates: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResourceNodeUpdate:
    """Updates to a harvestable node."""
    node_id: int
    charges_delta: int = 0
    cooldown_set: Optional[int] = None


@dataclass(frozen=True, slots=True)
class BuildingUpdate:
    """Updates to building health/status."""
    building_id: int
    hp_delta: int = 0
    functional_set: Optional[bool] = None


@dataclass(frozen=True, slots=True)
class WorldUpdate:
    """Updates to regional world state."""
    region_id: str
    hazard_level_set: Optional[float] = None
    suppression_set: Optional[bool] = None
    calamity_intensity_set: Optional[float] = None
    trauma_delta: float = 0.0


@dataclass(frozen=True, slots=True)
class StateUpdate:
    """
    A collection of authoritative changes to be applied to the world state.
    """
    entity_updates: Dict[int, EntityUpdate] = field(default_factory=dict)
    node_updates: Dict[int, ResourceNodeUpdate] = field(default_factory=dict)
    building_updates: Dict[int, BuildingUpdate] = field(default_factory=dict)
    world_updates: Dict[str, WorldUpdate] = field(default_factory=dict)
    resource_updates: Dict[str, float] = field(default_factory=dict)
    periodic_updates: Dict[str, int] = field(default_factory=dict)
    work_debt_updates: Dict[str, int] = field(default_factory=dict)
    rng_checkpoint: Any = None
