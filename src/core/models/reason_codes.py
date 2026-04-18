from enum import Enum
from typing import Any, Dict
from pydantic import Field
from src.core.models.base import SimulationModel

class ReasonCode(Enum):
    """Stable identifiers for simulation decision drivers. [Milestone 7]"""
    # Movement
    ADVANCING = "advancing"
    OCCUPANCY_VIOLATION = "occupancy_violation"
    PATH_NOT_FOUND = "path_not_found"
    YIELDING = "yielding"
    SIDESTEPPING = "sidestepping"
    WAITING = "waiting"
    CONGESTION = "congestion"
    PATH_EXHAUSTED = "path_exhausted"
    TARGET_REACHED = "target_reached"
    
    # Combat
    OUT_OF_RANGE = "out_of_range"
    TARGET_INVALID = "target_invalid"
    ACTION_EXHAUSTION = "exhaustion"
    INTERACTION_REJECTED = "interaction_rejected"
    ENGAGED = "engaged"
    
    # Tactical AI
    NO_TARGET = "no_target"
    LOW_HP_RETREAT = "low_hp_retreat"
    KITING = "kiting"
    MAINTAIN_DISTANCE = "maintain_distance"
    ALLY_SPACING = "ally_spacing"
    CLOSING_RANGE = "closing_range"
    
    # Legacy (To be removed)
    LEGACY_FALLBACK = "legacy_fallback"

class ActionReason(SimulationModel):
    """Structured reason for an action proposal or intent update. [Milestone 7]"""
    code: ReasonCode
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_rejection: bool = False
    
    @property
    def reason_text(self) -> str:
        """Derived human-readable summary for logs and UI compatibility."""
        base_text = ""
        if self.code == ReasonCode.ADVANCING:
            target = self.metadata.get("target")
            base_text = f"Advancing toward {target}" if target else "Advancing"
        elif self.code == ReasonCode.OCCUPANCY_VIOLATION:
            base_text = "Target occupancy violation"
        elif self.code == ReasonCode.PATH_NOT_FOUND:
            base_text = "No path found"
        elif self.code == ReasonCode.YIELDING:
            blocker = self.metadata.get("blocker_id")
            base_text = f"Yielding to {blocker}" if blocker else "Yielding"
        elif self.code == ReasonCode.SIDESTEPPING:
            base_text = "Sidestepping"
        elif self.code == ReasonCode.WAITING:
            base_text = "Waiting"
        elif self.code == ReasonCode.OUT_OF_RANGE:
            rng = self.metadata.get("max_range") # Using max_range to be explicit
            base_text = f"Target out of range (max={rng})" if rng else "Target out of range"
        elif self.code == ReasonCode.TARGET_INVALID:
            base_text = "Target entity invalid or dead"
        elif self.code == ReasonCode.LOW_HP_RETREAT:
            base_text = "Low HP (Tactical withdrawal)"
        elif self.code == ReasonCode.KITING:
            base_text = "Target too close (Widen/Kite)"
        elif self.code == ReasonCode.MAINTAIN_DISTANCE:
            base_text = "In ideal range (Maintain)"
        elif self.code == ReasonCode.ALLY_SPACING:
            ally = self.metadata.get("ally_id")
            base_text = f"Preserving spacing with ally {ally}" if ally else "Preserving spacing"
        else:
            detail = self.metadata.get("detail", "")
            if detail:
                base_text = f"{self.code.value.replace('_', ' ').title()}: {detail}"
            else:
                base_text = self.code.value.replace("_", " ").title()
        
        return f"REJECTED: {base_text}" if self.is_rejection else base_text

    def __str__(self) -> str:
        return self.reason_text

    def __repr__(self) -> str:
        return f"Reason({self.code.value}, {self.metadata})"
