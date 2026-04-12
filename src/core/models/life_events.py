"""Life event models — turning points and interpreted social events. [PHASE 2]

These models represent the semantic layer between raw simulation events and
durable social memory. TurningPointRecord captures life-defining moments.
InterpretedLifeEvent captures the social meaning of observed actions.
"""

from __future__ import annotations

from typing import Any
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.enums import TurningPointKind, InterpretedLifeEventKind
from src.core.models.vectors import Vector2


class TurningPointRecord(SimulationModel):
    """A durable record of a life-defining moment. [PHASE 2]

    Only high-impact memories belong here — near death, ally death, revenge,
    betrayal, rescue, disgrace, boss encounter, or first kill.
    Turning points are rare, meaningful, and behaviorally relevant.
    """
    model_config = ConfigDict(extra='forbid')

    event_id: str
    kind: TurningPointKind
    tick: int
    location: Vector2 = Field(default_factory=lambda: Vector2(x=0, y=0))
    involved_entity_ids: list[int] = Field(default_factory=list)
    summary_tag: str = ""
    emotional_impact: float = Field(default=0.0, ge=-10.0, le=10.0)
    relationship_effects: dict[int, dict[str, float]] = Field(default_factory=dict)
    reputation_effects: dict[str, float] = Field(default_factory=dict)
    motive_effects: dict[str, float] = Field(default_factory=dict)
    tags_add: list[str] = Field(default_factory=list)
    tags_remove: list[str] = Field(default_factory=list)
    still_salient: bool = True

    salience_score: float = Field(default=0.0, ge=0.0)


class InterpretedLifeEvent(SimulationModel):
    """A socially meaningful interpretation of a raw simulation event. [PHASE 2]

    This is a semantic interpretation layer, not prose generation.
    Interpreted events are sparse, high-value, and feed into turning points,
    relationships, and reputation.
    """
    model_config = ConfigDict(extra='forbid')

    event_id: str
    kind: InterpretedLifeEventKind
    tick: int
    actor_id: int
    subject_ids: list[int] = Field(default_factory=list)
    location: Vector2 = Field(default_factory=lambda: Vector2(x=0, y=0))
    evidence_refs: list[str] = Field(default_factory=list)
    severity: float = Field(default=0.0, ge=0.0, le=10.0)
    public_visibility: float = Field(default=0.0, ge=0.0, le=1.0)
    relationship_deltas: dict[int, dict[str, float]] = Field(default_factory=dict)
    reputation_deltas: dict[str, float] = Field(default_factory=dict)
    tags_add: list[str] = Field(default_factory=list)
    tags_remove: list[str] = Field(default_factory=list)
    turning_point_candidate: bool = False
    details: dict[str, Any] = Field(default_factory=dict) # [PHASE 5] Metadata for divergence logic


class ReputationProfile(SimulationModel):
    """A public-facing profile of an entity's social standing. [PHASE 2]
    
    Reputation is earned through visible InterpretedLifeEvents.
    It decays slowly over time to allow for notoriety to fade.
    """
    model_config = ConfigDict(extra='forbid')

    heroism_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    cowardice_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    greed_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    defender_score: float = Field(default=0.0, ge=-10.0, le=10.0)
    trustworthiness: float = Field(default=0.0, ge=-10.0, le=10.0)
    threat_notoriety: float = Field(default=0.0, ge=-10.0, le=10.0)
    
    reputation_tags: list[str] = Field(default_factory=list)


class SocialBondRecord(SimulationModel):
    """A subjective relationship record between two entities. [PHASE 2]"""
    model_config = ConfigDict(extra='forbid')

    target_id: int
    trust: float = Field(default=0.0, ge=-1.0, le=1.0)
    fear: float = Field(default=0.0, ge=0.0, le=1.0)
    loyalty: float = Field(default=0.0, ge=-1.0, le=1.0)
    resentment: float = Field(default=0.0, ge=0.0, le=1.0)
    admiration: float = Field(default=0.0, ge=0.0, le=1.0)
    rivalry: float = Field(default=0.0, ge=0.0, le=1.0)
    debt: float = Field(default=0.0, ge=-10.0, le=10.0)
    
    familiarity: float = Field(default=0.0, ge=0.0, le=1.0)
    last_interaction_tick: int = 0
    tags: list[str] = Field(default_factory=list)


# Pydantic model rebuild
TurningPointRecord.model_rebuild()
InterpretedLifeEvent.model_rebuild()
ReputationProfile.model_rebuild()
SocialBondRecord.model_rebuild()
