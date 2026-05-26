from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

EventCategory = Literal[
    "movement", "combat", "resource", "economy", "inventory",
    "quest", "strategy", "social", "lifecycle", "region",
    "infrastructure", "hard_law", "anomaly"
]

EventSeverity = Literal[
    "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
]

class SimulationEvent(BaseModel):
    """Phase 2 standardized SimulationEvent envelope schema."""
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    event_type: str
    event_category: EventCategory
    tick: int
    severity: EventSeverity = "INFO"
    source_system: str
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    
    # Optional context fields
    run_id: Optional[str] = None
    scenario_id: Optional[str] = None
    entity_id: Optional[int] = None
    related_entity_ids: List[int] = Field(default_factory=list)
    target_id: Optional[int] = None
    region_id: Optional[str] = None
    faction_id: Optional[str] = None
    quest_id: Optional[str] = None
    transaction_id: Optional[str] = None
    causal_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)

class CombatDamageEvent(SimulationEvent):
    """Emitted when an entity takes damage in combat."""
    attacker_id: Optional[int] = None
    damage: int
    is_lethal: bool
    event_type: str = "combat_damage"
    event_category: EventCategory = "combat"
    severity: EventSeverity = "INFO"
    source_system: str = "combat_system"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            att = data.get("attacker_id")
            dmg = data.get("damage")
            lethal = " lethal" if data.get("is_lethal") else ""
            data["message"] = f"Entity {ent} took {dmg}{lethal} damage from Attacker {att}"
        super().__init__(**data)

class CombatKillEvent(SimulationEvent):
    """Emitted when an entity defeats/kills another entity."""
    killer_id: Optional[int] = None
    event_type: str = "combat_kill"
    event_category: EventCategory = "combat"
    severity: EventSeverity = "INFO"
    source_system: str = "combat_system"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            victim = data.get("entity_id")
            killer = data.get("killer_id")
            data["message"] = f"Entity {victim} was killed by Killer {killer}"
        super().__init__(**data)

class GoldTransactionEvent(SimulationEvent):
    """Emitted when gold changes hands (trade, loot, quest reward, etc.)."""
    amount: float
    transaction_kind: str
    counterparty_id: Optional[int] = None
    event_type: str = "gold_transaction"
    event_category: EventCategory = "economy"
    severity: EventSeverity = "INFO"
    source_system: str = "economy_system"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            amt = data.get("amount")
            kind = data.get("transaction_kind")
            data["message"] = f"Entity {ent} had gold transaction of {amt} ({kind})"
        super().__init__(**data)

class QuestEvent(SimulationEvent):
    """Emitted when an entity progresses or updates a quest status."""
    quest_id: str
    status: str  # "started", "progress", "completed", "failed"
    progress_delta: float = 0.0
    event_type: str = "quest_event"
    event_category: EventCategory = "quest"
    severity: EventSeverity = "INFO"
    source_system: str = "quest_system"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            qid = data.get("quest_id")
            status = data.get("status")
            data["message"] = f"Entity {ent} quest {qid} updated to status {status}"
        super().__init__(**data)

class MovementEvent(SimulationEvent):
    """Emitted when an entity moves to a new position."""
    start_pos: Tuple[float, float]
    end_pos: Tuple[float, float]
    event_type: str = "movement"
    event_category: EventCategory = "movement"
    severity: EventSeverity = "INFO"
    source_system: str = "locomotion_system"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            sp = data.get("start_pos")
            ep = data.get("end_pos")
            data["message"] = f"Entity {ent} moved from {sp} to {ep}"
        super().__init__(**data)

class LifecycleEvent(SimulationEvent):
    """Emitted on spawn, level-up, death, or major lifecycle milestone."""
    action: str  # "spawn", "despawn", "level_up", "age"
    details: Dict[str, Any] = Field(default_factory=dict)
    event_type: str = "lifecycle"
    event_category: EventCategory = "lifecycle"
    severity: EventSeverity = "INFO"
    source_system: str = "lifecycle_system"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            act = data.get("action")
            data["message"] = f"Entity {ent} lifecycle state changed: {act}"
        super().__init__(**data)
