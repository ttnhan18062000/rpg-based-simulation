"""Household models — primary unit of durable continuity. [PHASE 4]

Households anchor groups of entities to a home building and store shared
reputation, legacy, and historical associations.
"""

from __future__ import annotations
from pydantic import Field, ConfigDict
from src_legacy.core.models.base import SimulationModel


class HouseholdRecord(SimulationModel):
    """The stable 'soul' of a home location that outlives individuals. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')

    household_id: str
    home_building_id: int
    
    # Membership
    member_ids: set[int] = Field(default_factory=set)
    former_member_ids: list[int] = Field(default_factory=list)
    
    # Legacy & Status
    reputation: float = Field(default=0.0, ge=-100.0, le=100.0)
    legacy_gold: int = Field(default=0) # [PHASE 1 STAGE 13]
    storage_id: str | None = None # Reference to a shared persistent inventory
    heirloom_ids: list[str] = Field(default_factory=list) # [PHASE 4] Persistent equipment
    
    # History Links
    related_event_ids: list[str] = Field(default_factory=list)
    legacy_tags: list[str] = Field(default_factory=list)


# Pydantic model rebuild
HouseholdRecord.model_rebuild()
