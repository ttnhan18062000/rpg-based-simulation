"""Lived-structure core models — routines, place attachments, and group coordination. [PHASE 3]

These models provide the structural substrate for behavioral realism, allowing 
entities to have recurring life patterns, subjective location attachments, 
and small-group tactical coordination.
"""

from __future__ import annotations
from typing import Any, Literal
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.enums import GoalType, GroupKind, AttachmentKind
from src.core.models.vectors import Vector2


class RoutineProfile(SimulationModel):
    """Defines a recurring life-pattern or scheduled activity. [PHASE 3]
    
    A hybrid model supporting both temporal windows (Circadian Rhythm) 
    and event-based triggers (Emergency/Priority).
    """
    model_config = ConfigDict(extra='forbid')

    routine_id: str
    routine_type: str # e.g. "sleeping", "patrolling", "socializing"
    anchor_type: str  # "home", "work", "wander", "specific"
    anchor_pos: Vector2 | None = None # Only used if anchor_type is "specific"
    
    # Temporal Window (Hybrid Option A)
    # Hour range (0-23). 1 hour = 10 ticks.
    schedule_window: tuple[int, int] | None = None 
    
    # Event Drive (Hybrid Option C)
    # List of InterpretedLifeEventKind names or State thresholds
    event_triggers: list[str] = Field(default_factory=list) 
    
    priority: float = Field(default=1.0, ge=0.0, le=5.0)
    ideal_goal: GoalType | None = None # Maps to AI selection


class PlaceAttachment(SimulationModel):
    """Subjective importance of a world location assigned by an entity. [PHASE 3]
    
    Importance grows through repeated meaningful actions and decays via neglect.
    """
    model_config = ConfigDict(extra='forbid')

    location_pos: Vector2
    building_id: int | None = None
    kind: AttachmentKind = AttachmentKind.HOME
    
    # Dynamic Sentiment (Option C)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    
    last_action_tick: int = 0
    total_actions_here: int = 0
    
    tags: list[str] = Field(default_factory=list)


class GroupRecord(SimulationModel):
    """Shared coordination structure for small-group scenarios. [PHASE 3]
    
    Facilitates "Shared Tactical Intent" where members gains bonuses 
    and pursue collective goals.
    """
    model_config = ConfigDict(extra='forbid')

    group_id: str
    leader_id: int | None = None
    kind: GroupKind = GroupKind.SOCIAL_CLIQUE
    
    # Intent tracking (Option C)
    shared_goal: GoalType = GoalType.EXPLORE
    target_id: int | None = None # Subject of the group's intent
    
    member_ids: set[int] = Field(default_factory=set)
    anchor_pos: Vector2 | None = None # Rally point or center of activity
    
    # Cohesion Bonuses
    cohesion_level: float = Field(default=1.0, ge=0.0, le=2.0)
    bonuses: dict[str, float] = Field(default_factory=dict) # e.g. {"bravery": 0.2, "atk": 0.1}


# Pydantic model rebuild
RoutineProfile.model_rebuild()
PlaceAttachment.model_rebuild()
GroupRecord.model_rebuild()
