"""Continuity models — bridging individual lives and historical memory. [PHASE 4]

Successor records track the handover of legacy, motives, and status from
a deceased entity to a household or specific heir.
"""

from __future__ import annotations
from typing import Any
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel


class SuccessorRecord(SimulationModel):
    """A bridge between a deceased entity and its shared legacy. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')

    source_entity_id: int
    successor_entity_id: int | None = None # Explicit hier if assigned
    household_id: str | None = None
    
    # Legacy data
    motive_fragments: dict[str, Any] = Field(default_factory=dict)
    
    # History Link
    death_event_id: str
    tick: int


# Pydantic model rebuild
SuccessorRecord.model_rebuild()
