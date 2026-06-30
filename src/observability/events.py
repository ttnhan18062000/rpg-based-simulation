from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ObservabilityEventEnvelope:
    """
    Standard lightweight event envelope for cheap hot-path observability dispatch.
    """
    event_id: str
    run_id: str
    tick: int
    entity_id: Optional[int]
    event_type: str
    event_category: str
    severity: str
    source_system: str
    message: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    related_entity_ids: tuple[int, ...] = ()

    @classmethod
    def from_simulation_event(cls, event: SimulationEvent, run_id: Optional[str] = None) -> ObservabilityEventEnvelope:
        return cls(
            event_id=event.event_id,
            run_id=run_id or event.run_id or "unknown_run",
            tick=event.tick,
            entity_id=event.entity_id,
            event_type=event.event_type,
            event_category=event.event_category,
            severity=event.severity,
            source_system=event.source_system,
            message=event.message,
            payload=event.payload,
            related_entity_ids=tuple(event.related_entity_ids)
        )


EventCategory = Literal[
    "movement", "combat", "resource", "economy", "inventory",
    "quest", "strategy", "social", "lifecycle", "region", "faction",
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


# ---------------------------------------------------------------------------
# Economy health alert events (TCK-20260619-E33B-ALERTS-REST)
# ---------------------------------------------------------------------------

class DeflationRiskEvent(SimulationEvent):
    """Emitted when macro-economy Gini coefficient indicates deflation risk.

    Deferred: threshold depends on transaction_velocity which is stub=0.0 in E33B.
    Defined here for completeness; not yet emitted by EconomyHealthMonitor.
    """
    gini_coefficient: float
    event_type: str = "DEFLATION_RISK"
    event_category: EventCategory = "economy"
    severity: EventSeverity = "WARNING"
    source_system: str = "economy_health_monitor"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            gini = data.get("gini_coefficient", 0.0)
            region = data.get("region_id")
            region_str = f" in region {region}" if region else ""
            data["message"] = f"Deflation risk detected{region_str}: gini={gini:.4f}"
        super().__init__(**data)


class InflationSpiralEvent(SimulationEvent):
    """Emitted when Gini coefficient exceeds INFLATION_SPIRAL_GINI_THRESHOLD (0.7)."""
    gini_coefficient: float
    event_type: str = "INFLATION_SPIRAL"
    event_category: EventCategory = "economy"
    severity: EventSeverity = "WARNING"
    source_system: str = "economy_health_monitor"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            gini = data.get("gini_coefficient", 0.0)
            region = data.get("region_id")
            region_str = f" in region {region}" if region else ""
            data["message"] = f"Inflation spiral detected{region_str}: gini={gini:.4f}"
        super().__init__(**data)


class EconomicCollapseEvent(SimulationEvent):
    """Emitted when a region has zero economic activity for ≥200 ticks.

    Deferred: requires transaction_velocity which is stub=0.0 in E33B.
    Defined here for completeness; not yet emitted by EconomyHealthMonitor.
    """
    gini_coefficient: float
    event_type: str = "ECONOMIC_COLLAPSE"
    event_category: EventCategory = "economy"
    severity: EventSeverity = "CRITICAL"
    source_system: str = "economy_health_monitor"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            region = data.get("region_id")
            region_str = f" in region {region}" if region else ""
            data["message"] = f"Economic collapse detected{region_str}: zero transactions sustained"
        super().__init__(**data)


class GoldHoardingEvent(SimulationEvent):
    """Emitted when Gini coefficient exceeds GOLD_HOARDING_GINI_THRESHOLD (0.8)."""
    gini_coefficient: float
    event_type: str = "GOLD_HOARDING"
    event_category: EventCategory = "economy"
    severity: EventSeverity = "WARNING"
    source_system: str = "economy_health_monitor"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            gini = data.get("gini_coefficient", 0.0)
            region = data.get("region_id")
            region_str = f" in region {region}" if region else ""
            data["message"] = f"Gold hoarding detected{region_str}: gini={gini:.4f}"
        super().__init__(**data)


# ---------------------------------------------------------------------------
# Party lifecycle events (TCK-20260619-E41B-LEADERSHIP)
# ---------------------------------------------------------------------------

class LeadershipChangedEvent(SimulationEvent):
    """Emitted when party leadership changes due to sociability-based election.

    Logic ID: SOC-228 (Leadership election emits LeadershipChangedEvent on transition)
    """
    group_id: int
    old_leader_id: int
    new_leader_id: int
    morale_delta: float = 0.1
    event_type: str = "leadership_changed"
    event_category: EventCategory = "social"
    severity: EventSeverity = "INFO"
    source_system: str = "party_lifecycle_service"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data or not data["message"]:
            g = data.get("group_id")
            old = data.get("old_leader_id")
            new = data.get("new_leader_id")
            data["message"] = (
                f"Group {g} leadership transferred from entity {old} to entity {new}"
            )
        super().__init__(**data)


class BetrayalDesertionEvent(SimulationEvent):
    """Emitted when a party member defects due to accumulated grievances.

    Logic ID: SOC-230 (Defection fires betrayal_desertion when grievance_log >= 3)
    """
    group_id: int
    grievance_count: int
    event_type: str = "betrayal_desertion"
    event_category: EventCategory = "social"
    severity: EventSeverity = "WARNING"
    source_system: str = "party_lifecycle_service"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data or not data["message"]:
            eid = data.get("entity_id")
            g = data.get("group_id")
            gc = data.get("grievance_count", 0)
            data["message"] = (
                f"Entity {eid} defected from group {g} after {gc} unresolved grievances"
            )
        super().__init__(**data)

    @classmethod
    def create(
        cls,
        tick: int,
        group_id: int,
        entity_id: int,
        grievance_count: int,
        remaining_member_ids: List[int],
    ) -> "BetrayalDesertionEvent":
        return cls(
            tick=tick,
            group_id=group_id,
            entity_id=entity_id,
            grievance_count=grievance_count,
            related_entity_ids=remaining_member_ids,
            payload={
                "grievance_count": grievance_count,
                "remaining_members": remaining_member_ids,
            },
        )


# ---------------------------------------------------------------------------
# Social Memory consequence events (TCK-20260619-E43E-CONSEQUENCE-EVENTS)
# ---------------------------------------------------------------------------

# Event kind string constants — importable directly for switch/match usage.
LEGENDARY_ARRIVAL: str = "LEGENDARY_ARRIVAL"
KNOWN_TRAITOR_SPOTTED: str = "KNOWN_TRAITOR_SPOTTED"
OLD_DEBT_COLLECTED: str = "OLD_DEBT_COLLECTED"


class LegendaryArrivalEvent(SimulationEvent):
    """Emitted when an entity with high cross-episode reputation (>= 0.9) enters
    a faction's territory.

    Logic ID: SOC-CROSS-EP-005 (LEGENDARY_ARRIVAL fires when faction_reputation["default"] >= 0.9)
    """
    hostility_score: float = 0.0
    episode_of_offense: int = 0
    event_type: str = LEGENDARY_ARRIVAL
    event_category: EventCategory = "social"
    severity: EventSeverity = "INFO"
    source_system: str = "social_consequence_evaluator"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data or not data["message"]:
            eid = data.get("entity_id")
            fid = data.get("faction_id")
            data["message"] = (
                f"Entity {eid} of legendary reputation has arrived in {fid} territory"
            )
        super().__init__(**data)


class KnownTraitorSpottedEvent(SimulationEvent):
    """Emitted when an entity flagged as a traitor (faction hostility >= 0.5) enters
    a hostile faction's territory.

    Logic ID: SOC-CROSS-EP-005 (KNOWN_TRAITOR_SPOTTED fires when entity_hostility >= 0.5)
    """
    hostility_score: float = 0.0
    episode_of_offense: int = 0
    event_type: str = KNOWN_TRAITOR_SPOTTED
    event_category: EventCategory = "social"
    severity: EventSeverity = "WARNING"
    source_system: str = "social_consequence_evaluator"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data or not data["message"]:
            eid = data.get("entity_id")
            fid = data.get("faction_id")
            score = data.get("hostility_score", 0.0)
            data["message"] = (
                f"Known traitor entity {eid} spotted in {fid} territory "
                f"(hostility={score:.2f})"
            )
        super().__init__(**data)


class OldDebtCollectedEvent(SimulationEvent):
    """Emitted when an entity meets another entity with whom it has a significant
    positive cross-episode relationship score (>= 0.5), representing a prior-episode
    social obligation being honoured.

    Logic ID: SOC-CROSS-EP-005 (OLD_DEBT_COLLECTED fires when relationship_score >= 0.5)
    """
    debtor_id: int = 0
    relationship_score: float = 0.0
    event_type: str = OLD_DEBT_COLLECTED
    event_category: EventCategory = "social"
    severity: EventSeverity = "INFO"
    source_system: str = "social_consequence_evaluator"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data or not data["message"]:
            eid = data.get("entity_id")
            did = data.get("debtor_id", 0)
            score = data.get("relationship_score", 0.0)
            data["message"] = (
                f"Entity {eid} collects old social debt from entity {did} "
                f"(bond={score:.2f})"
            )
        super().__init__(**data)
