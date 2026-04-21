from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class BlockerState:
    """Explicit reason for strategic stalling."""
    id: str
    kind: str # 'material', 'capability', 'access'
    subject: str # e.g. 'iron_ore', 'gold'
    severity: float = 0.5
    resolved: bool = False

@dataclass(frozen=True, slots=True)
class LeadState:
    """Uncertain clue or pointer to a strategic opportunity."""
    id: str
    kind: str # 'location', 'object', 'event'
    subject: str
    detail: str = ""
    discovered_tick: int = 0

@dataclass(frozen=True, slots=True)
class StrategicComponent:
    """Aggregate strategic stratum attached to an entity."""
    blockers: Dict[str, BlockerState] = field(default_factory=dict)
    leads: Dict[str, LeadState] = field(default_factory=dict)
