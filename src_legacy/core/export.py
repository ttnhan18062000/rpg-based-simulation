from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class EntityDTO(BaseModel):
    """
    Export-ready Data Transfer Object for an Entity.
    Supports validation and API-centric naming.
    """
    model_config = ConfigDict(frozen=True)

    id: int
    kind: str
    position_x: float
    position_y: float
    readiness: float
    is_active: bool = Field(alias="active")
    props: Dict[str, Any] = Field(default_factory=dict, alias="properties")


class StateDTO(BaseModel):
    """
    Export-ready DTO for the simulation state.
    Used for persistence and external API responses.
    """
    model_config = ConfigDict(frozen=True)

    tick: int
    seed: int
    world_time: int
    entities: List[EntityDTO]
    resources: Dict[str, float] = Field(default_factory=dict, alias="global_resources")


def to_export_state(state: 'AuthoritativeState') -> StateDTO:
    """
    Factory function to build a StateDTO from AuthoritativeState.
    Isolation: AuthoritativeState remains Pydantic-free.
    """
    entity_dtos = [
        EntityDTO(
            id=ent.id,
            kind=ent.kind,
            position_x=ent.position[0],
            position_y=ent.position[1],
            readiness=ent.readiness,
            active=ent.active,
            properties=ent.properties
        )
        for ent in sorted(state.entities.values(), key=lambda e: e.id)
    ]
    
    return StateDTO(
        tick=state.tick,
        seed=state.seed,
        world_time=state.world_time,
        entities=entity_dtos,
        global_resources=state.global_resources
    )
