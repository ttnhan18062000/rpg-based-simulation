# Compliance IDs: WORLD-ASM-001, WORLD-ASM-002
from __future__ import annotations

from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field, ConfigDict


class ResolvedEntityProfile(BaseModel):
    """Internal compile-ready properties for a specific unit group/population."""
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    legacy_role: int
    legacy_faction: int
    hp: int
    max_hp: int
    atk: int
    def_stat: int = Field(..., alias="def")
    attack_range: int
    readiness: float
    inventory_seed: Optional[str] = None
    cognition_seed: Optional[str] = None
    spawn_position: Optional[Tuple[float, float]] = None

    # Archetype metadata fields (Phase 25)
    archetype_id: Optional[str] = None
    species_id: Optional[str] = None
    role_id: Optional[str] = None
    faction_id: Optional[str] = None
    traits: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    stat_profile_id: Optional[str] = None
    combat_profile_id: Optional[str] = None
    cognition_profile_id: Optional[str] = None
    drive_profile_id: Optional[str] = None
    need_profile_id: Optional[str] = None
    sense_profile_id: Optional[str] = None
    inventory_profile_id: Optional[str] = None
    skill_profile_id: Optional[str] = None



class ResolvedBuildingProfile(BaseModel):
    """Internal compile-ready properties for a specific building group."""
    hp: int
    max_hp: int
    service_profile_id: Optional[str] = None
    owner_faction: Optional[int] = None


class ResolvedResourceProfile(BaseModel):
    """Internal compile-ready properties for a specific resource type."""
    required_ticks: int
    resource_type: str
    yield_policy: Optional[str] = None


class ResolvedFactionEconomyProfile(BaseModel):
    """Internal compile-ready properties for a faction's treasury."""
    starting_gold: float
