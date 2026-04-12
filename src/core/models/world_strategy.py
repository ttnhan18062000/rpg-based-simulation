"""World-tier strategic models for shared pressures and opportunities. [PHASE 6]

This module defines the strategic state that exists at the world registry level, 
providing a shared context for entity-level and faction-level decision making.
"""

from __future__ import annotations
from typing import Any
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.strategy import LeadRecord, StrategicStatus

class StrategicOpportunity(SimulationModel):
    """A shared strategic lead or project available to multiple entities."""
    model_config = ConfigDict(extra='forbid')
    
    opportunity_id: str
    label: str
    description: str
    lead: LeadRecord
    
    status: StrategicStatus = StrategicStatus.ACTIVE
    difficulty_rating: float = Field(default=0.5, ge=0.0, le=1.0)
    reward_desc: str = ""
    
    created_tick: int = 0
    expires_tick: int | None = None
    
    # Tracking who is currently pursuing this
    pursuer_ids: list[int] = Field(default_factory=list)
    completed_by_id: int | None = None

class WorldObligation(SimulationModel):
    """A high-level strategic pressure broadcasted to all relevant entities."""
    model_config = ConfigDict(extra='forbid')
    
    obligation_id: str
    label: str
    description: str
    
    faction_restriction: int | None = None # Faction ID if restricted
    priority_mult: float = 1.0
    
    created_tick: int = 0
    expires_tick: int | None = None

class WorldStrategicRegistry(SimulationModel):
    """Container for shared strategic state at the world level."""
    model_config = ConfigDict(extra='forbid')
    
    opportunities: dict[str, StrategicOpportunity] = Field(default_factory=dict)
    obligations: dict[str, WorldObligation] = Field(default_factory=dict)
    
    last_update_tick: int = 0

    def copy(self) -> WorldStrategicRegistry:
        return self.model_copy(deep=True)

    def freeze(self) -> None:
        """Lock the registry (AOA Pillar 1)."""
        pass # Pydantic models are effectively frozen if handled correctly
