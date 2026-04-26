"""Phase Contract: Defines the access patterns for Engine Phases."""

from __future__ import annotations
from enum import IntFlag, auto
from dataclasses import dataclass

class PhaseAccess(IntFlag):
    """Access level for an EngineContext field during a phase."""
    NONE = 0
    READ = auto()
    MUTATE = auto()
    READ_WRITE = READ | MUTATE

@dataclass(frozen=True, slots=True)
class PhaseContract:
    """Metadata describing the formal read/write contract of an EnginePhase."""
    name: str
    description: str
    
    # Map of EngineContext field names to their allowed access level
    # e.g. {"world": PhaseAccess.READ, "tick_applied": PhaseAccess.MUTATE}
    permissions: dict[str, PhaseAccess]
    
    # Explicitly allowed side-effects (e.g., event emission)
    allow_emit: bool = True
