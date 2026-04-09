"""Local Scar models — spatial world memory of major events. [PHASE 4]

Local scars track the aftermath of traumatic events at specific locations,
influencing behavioral safety and recovery tracks.
"""

from __future__ import annotations
from enum import Enum
from pydantic import Field, ConfigDict
from src.core.models.base import SimulationModel
from src.core.models.vectors import Vector2


class ScarKind(str, Enum):
    """Types of localized scars."""
    RAID_DAMAGE = "raid_damage"
    BATTLE_FIELD = "battle_field"
    FEAR_ZONE = "fear_zone"
    BOSS_DEVASTATION = "boss_devastation"


class LocalScarRecord(SimulationModel):
    """A physical marker of local trauma or significant history at a coordinate. [PHASE 4]

    Scars are created by the RegionalConsequenceSystem in response to historical events 
    like fatalities or raids. They are perceivable by AI and can influence emotions 
    (e.g., inducing dread or situational panic).

    Attributes:
        scar_id: Domain-unique identifier.
        pos: World coordinates of the event.
        kind: Semantic type (e.g., 'battlefield', 'raid_site', 'devastation').
        severity: Intensity of the trauma (0.0 to 1.0).
        tick: Simulation tick when the event occurred.
        duration: How many ticks the scar persists before full decay.
    """
    model_config = ConfigDict(extra='forbid')

    location_pos: Vector2
    kind: ScarKind
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Timing & Recovery
    created_tick: int
    recovery_rate: float = Field(default=0.001) # Severity reduction per tick
    
    # History Link
    source_event_id: str
    
    # Behavioral Influence
    behavioral_modifiers: dict[str, float] = Field(default_factory=dict)


# Pydantic model rebuild
LocalScarRecord.model_rebuild()
