"""World History models — tracking causality and major events. [PHASE 4]

These models provide a central registry of "What happened here" (HistoricalEvents),
allowing state records (Households, Scars, Regions) to link back to their causes.
"""

from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.vectors import Vector2


class EventKind(str, Enum):
    """Types of meaningful world events."""
    DEATH = "death"
    RAID = "raid"
    BOSS_FALL = "boss_fall"
    HOUSEHOLD_FOUNDED = "household_founded"
    REGION_LIBERATION = "region_liberation"
    BUILDING_DESTROYED = "building_destroyed"
    CALAMITY_START = "calamity_start"


class HistoricalEvent(SimulationModel):
    """A record of a single meaningful event in the world's timeline. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')

    event_id: str
    tick: int
    kind: EventKind
    location: Vector2 | None = None
    involved_ids: set[int] = Field(default_factory=set)
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorldHistoryRegistry(SimulationModel):
    """Central store for all historical events. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')

    # Keyed by event_id
    events: dict[str, HistoricalEvent] = Field(default_factory=dict)

    def add_event(self, event: HistoricalEvent) -> None:
        self.events[event.event_id] = event

    def get_event(self, event_id: str) -> HistoricalEvent | None:
        return self.events.get(event_id)

    def copy(self) -> "WorldHistoryRegistry":
        """Manual deep copy for snapshotting, avoiding mappingproxy pickling issues."""
        new_events = {}
        for k, v in self.events.items():
            # Use model_dump + model_validate to get a fresh mutable copy 
            # while bypassing pickling issues with MappingProxyType fields.
            new_events[k] = HistoricalEvent.model_validate(v.model_dump())
            
        return WorldHistoryRegistry(events=new_events)


# Pydantic model rebuild
HistoricalEvent.model_rebuild()
WorldHistoryRegistry.model_rebuild()
