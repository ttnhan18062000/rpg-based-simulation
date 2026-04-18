from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import Field, model_validator
from src.core.models.base import SimulationModel
from src.core.models.enums import (
    EntityRole, HeroClass, Faction, ArenaStopCondition, 
    ArenaStopCondSer, FactionSer, HeroClassSer
)
from src.core.models.vectors import Vector2

class ParticipantProfile(SimulationModel):
    """Archetype definition for an arena participant. [Milestone 6]"""
    kind: str = "hero"
    role: EntityRole = EntityRole.HERO
    hero_class: HeroClass = HeroClass.WARRIOR
    level: int = 1
    faction: Faction = Faction.HERO_GUILD
    stat_overrides: Dict[str, float] = Field(default_factory=dict)
    
    # Optional specific explicit overrides for convenience
    hp_over: Optional[int] = None
    atk_over: Optional[int] = None
    spd_over: Optional[int] = None

class StopCondition(SimulationModel):
    """Predicate for scenario termination. [Milestone 6]"""
    type: ArenaStopCondSer
    params: Dict[str, Any] = Field(default_factory=dict)

class Scenario(SimulationModel):
    """Authoritative data model for a combat/movement scenario. [Milestone 6]"""
    id: str
    name: str
    description: str = ""
    
    participants: List[ParticipantProfile]
    initial_placements: List[Vector2] # matches index of participants
    
    # Map/Grid setup
    grid_width: int = 64
    grid_height: int = 64
    # Optional materials (wall coordinates, etc.)
    grid_materials: Dict[str, List[Vector2]] = Field(default_factory=dict)
    
    stop_conditions: List[StopCondition] = Field(default_factory=list)
    max_ticks: int = 2000
    iterations: int = 10
    
    @model_validator(mode="after")
    def _validate_placements(self) -> "Scenario":
        if len(self.participants) != len(self.initial_placements):
            raise ValueError(f"Mismatch: {len(self.participants)} participants vs {len(self.initial_placements)} placements")
        return self

class ArenaResult(SimulationModel):
    """Outcome of a single iteration. [Milestone 6]"""
    iteration: int
    winner_faction: Optional[FactionSer] = None
    ticks: int
    stop_reason: ArenaStopCondSer
    total_damage: int = 0
    deaths: List[int] = Field(default_factory=list) # IDs of dead entities
    # Milestone 7: Observability Auditing
    rejection_counts: Dict[str, int] = Field(default_factory=dict) # ReasonCode -> Count
    
    # Milestone 6: Resource Metrics
    peak_rss_mb: float = 0.0
    cpu_time_sec: float = 0.0

class ScenarioReport(SimulationModel):
    """Aggregated metrics across multiple arena runs. [Milestone 6]"""
    scenario_id: str
    total_iterations: int
    win_rates: Dict[str, float] # Faction name -> % (0.0 to 1.0)
    avg_ticks: float
    stall_rate: float
    watchdog_timeout_rate: float = 0.0 # [Milestone 7]
    avg_damage: float
    stop_reason: Optional[ArenaStopCondSer] = None
    baseline_diffs: Optional[Dict[str, float]] = None
    # Milestone 7: Observability Auditing
    avg_rejection_counts: Dict[str, float] = Field(default_factory=dict)
    
    # Milestone 6: Resource Metrics
    avg_peak_rss: float = 0.0
    peak_rss_high_water: float = 0.0
    total_cpu_time: float = 0.0
