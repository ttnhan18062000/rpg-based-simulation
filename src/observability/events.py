from __future__ import annotations
import time
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, Field

class SimulationEvent(BaseModel):
    """Base schema for all curated simulation telemetry events."""
    tick: int
    timestamp: float = Field(default_factory=time.time)
    entity_id: int
    event_type: str

class CombatDamageEvent(SimulationEvent):
    """Emitted when an entity takes damage in combat."""
    attacker_id: Optional[int] = None
    damage: int
    is_lethal: bool
    event_type: str = "combat_damage"

class CombatKillEvent(SimulationEvent):
    """Emitted when an entity defeats/kills another entity."""
    killer_id: Optional[int] = None
    event_type: str = "combat_kill"

class GoldTransactionEvent(SimulationEvent):
    """Emitted when gold changes hands (trade, loot, quest reward, etc.)."""
    amount: float
    transaction_kind: str
    counterparty_id: Optional[int] = None
    event_type: str = "gold_transaction"

class QuestEvent(SimulationEvent):
    """Emitted when an entity progresses or updates a quest status."""
    quest_id: str
    status: str  # "started", "progress", "completed", "failed"
    progress_delta: float = 0.0
    event_type: str = "quest_event"

class MovementEvent(SimulationEvent):
    """Emitted when an entity moves to a new position."""
    start_pos: Tuple[float, float]
    end_pos: Tuple[float, float]
    event_type: str = "movement"

class LifecycleEvent(SimulationEvent):
    """Emitted on spawn, level-up, death, or major lifecycle milestone."""
    action: str  # "spawn", "despawn", "level_up", "age"
    details: Dict[str, Any] = Field(default_factory=dict)
    event_type: str = "lifecycle"
