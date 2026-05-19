from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.observability.events import SimulationEvent

class Anomaly(BaseModel):
    """Represents a detected behavioral or system anomaly in the simulation run."""
    anomaly_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    rule_name: str
    severity: str  # "WARNING", "ERROR", "CRITICAL"
    entity_id: Optional[int] = None
    tick_detected: int
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)

class AnomalyRule:
    """Base interface for post-run simulation diagnostic rules."""
    def evaluate(self, events: List[SimulationEvent]) -> List[Anomaly]:
        raise NotImplementedError

class HardLawViolationRule(AnomalyRule):
    """Flags any hard law violations logged during the simulation."""
    def evaluate(self, events: List[SimulationEvent]) -> List[Anomaly]:
        anomalies = []
        for ev in events:
            if ev.event_category == "hard_law" or ev.event_type == "InvariantViolation":
                anomalies.append(Anomaly(
                    rule_name="HardLawViolationRule",
                    severity="CRITICAL",
                    entity_id=ev.entity_id,
                    tick_detected=ev.tick,
                    message=f"Hard Law Violation detected: {ev.message}",
                    context=ev.payload
                ))
        return anomalies

class NavigationStuckRule(AnomalyRule):
    """Detects if an active entity's position is frozen over a long window of ticks."""
    def __init__(self, tick_threshold: int = 50) -> None:
        self.tick_threshold = tick_threshold

    def evaluate(self, events: List[SimulationEvent]) -> List[Anomaly]:
        anomalies = []
        # Group movement events by entity_id
        entity_movements: Dict[int, List[SimulationEvent]] = {}
        for ev in events:
            if ev.event_type == "movement" and ev.entity_id is not None:
                entity_movements.setdefault(ev.entity_id, []).append(ev)

        for eid, m_events in entity_movements.items():
            if len(m_events) < 2:
                continue
            # Sort by tick
            m_events.sort(key=lambda x: x.tick)
            
            consecutive_stuck_ticks = 0
            last_pos = None
            last_tick = None
            
            for ev in m_events:
                end_pos = ev.payload.get("end_pos") or getattr(ev, "end_pos", None)
                if last_pos is not None and last_pos == end_pos:
                    consecutive_stuck_ticks += (ev.tick - last_tick)
                    if consecutive_stuck_ticks >= self.tick_threshold:
                        anomalies.append(Anomaly(
                            rule_name="NavigationStuckRule",
                            severity="ERROR",
                            entity_id=eid,
                            tick_detected=ev.tick,
                            message=f"Entity {eid} stuck at position {end_pos} for {consecutive_stuck_ticks} ticks",
                            context={"position": end_pos, "stuck_duration_ticks": consecutive_stuck_ticks}
                        ))
                        # Reset to avoid flooding duplicated anomalies
                        consecutive_stuck_ticks = 0
                else:
                    consecutive_stuck_ticks = 0
                last_pos = end_pos
                last_tick = ev.tick
                
        return anomalies

class QuestStalledRule(AnomalyRule):
    """Detects quests that remain in-progress or started without completion for too long."""
    def __init__(self, tick_threshold: int = 100) -> None:
        self.tick_threshold = tick_threshold

    def evaluate(self, events: List[SimulationEvent]) -> List[Anomaly]:
        anomalies = []
        # Track quest lifecycles: quest_id -> {entity_id, started_tick, status, last_update_tick}
        quest_states: Dict[str, Dict[str, Any]] = {}
        
        for ev in events:
            if ev.event_category == "quest" or ev.event_type == "quest_event":
                qid = ev.payload.get("quest_id") or getattr(ev, "quest_id", None)
                status = ev.payload.get("status") or getattr(ev, "status", None)
                if not qid or not status:
                    continue
                    
                if status == "started":
                    quest_states[qid] = {
                        "entity_id": ev.entity_id,
                        "started_tick": ev.tick,
                        "last_update_tick": ev.tick,
                        "status": "started"
                    }
                elif qid in quest_states:
                    quest_states[qid]["status"] = status
                    quest_states[qid]["last_update_tick"] = ev.tick

        # Find stalled quests
        # Since we're analyzing post-run, the final tick is the max tick among all events
        if not events:
            return []
        final_tick = max(ev.tick for ev in events)
        
        for qid, qstate in quest_states.items():
            if qstate["status"] in ("started", "progress"):
                duration = final_tick - qstate["started_tick"]
                if duration >= self.tick_threshold:
                    anomalies.append(Anomaly(
                        rule_name="QuestStalledRule",
                        severity="WARNING",
                        entity_id=qstate["entity_id"],
                        tick_detected=final_tick,
                        message=f"Quest {qid} stalled in status {qstate['status']} for {duration} ticks",
                        context={"quest_id": qid, "status": qstate["status"], "duration_ticks": duration}
                    ))
        return anomalies

class CombatNeverEndsRule(AnomalyRule):
    """Detects infinite combat loops or combat stalling without conclusion."""
    def __init__(self, tick_threshold: int = 40) -> None:
        self.tick_threshold = tick_threshold

    def evaluate(self, events: List[SimulationEvent]) -> List[Anomaly]:
        anomalies = []
        # Track active combat engagements: sorted combat damage events per entity
        combat_events = [ev for ev in events if ev.event_category == "combat" or ev.event_type in ("combat_damage", "combat_kill")]
        combat_events.sort(key=lambda x: x.tick)

        # Track active combats: entity_id -> {start_tick, last_damage_tick}
        active_combats: Dict[int, Dict[str, Any]] = {}

        for ev in combat_events:
            eid = ev.entity_id
            if eid is None:
                continue

            if ev.event_type == "combat_damage":
                if eid not in active_combats:
                    active_combats[eid] = {
                        "start_tick": ev.tick,
                        "last_damage_tick": ev.tick
                    }
                else:
                    duration = ev.tick - active_combats[eid]["start_tick"]
                    active_combats[eid]["last_damage_tick"] = ev.tick
                    if duration >= self.tick_threshold:
                        anomalies.append(Anomaly(
                            rule_name="CombatNeverEndsRule",
                            severity="ERROR",
                            entity_id=eid,
                            tick_detected=ev.tick,
                            message=f"Entity {eid} engaged in continuous combat for {duration} ticks without resolution",
                            context={"start_tick": active_combats[eid]["start_tick"], "combat_duration_ticks": duration}
                        ))
                        # Reset start tick to prevent repeat anomalies every tick
                        active_combats[eid]["start_tick"] = ev.tick
            elif ev.event_type == "combat_kill":
                # Combat resolved
                if eid in active_combats:
                    del active_combats[eid]
                killer = ev.payload.get("killer_id") or getattr(ev, "killer_id", None)
                if killer in active_combats:
                    del active_combats[killer]

        return anomalies

class ResourceNodeCrowdingRule(AnomalyRule):
    """Detects spatial congestion where too many entities harvest the same node simultaneously."""
    def __init__(self, entity_limit: int = 4) -> None:
        self.entity_limit = entity_limit

    def evaluate(self, events: List[SimulationEvent]) -> List[Anomaly]:
        anomalies = []
        # Group resource harvest actions by tick and node/target
        harvest_ticks: Dict[int, Dict[str, List[int]]] = {}

        for ev in events:
            if ev.event_category == "resource" or ev.event_type == "gold_transaction":
                node_id = ev.payload.get("node_id") or ev.payload.get("target_id") or getattr(ev, "target_id", None)
                if node_id is not None and ev.entity_id is not None:
                    node_key = str(node_id)
                    harvest_ticks.setdefault(ev.tick, {}).setdefault(node_key, []).append(ev.entity_id)

        for tick, nodes in harvest_ticks.items():
            for node_id, entity_ids in nodes.items():
                unique_entities = list(set(entity_ids))
                if len(unique_entities) > self.entity_limit:
                    anomalies.append(Anomaly(
                        rule_name="ResourceNodeCrowdingRule",
                        severity="WARNING",
                        tick_detected=tick,
                        message=f"Resource node {node_id} crowded by {len(unique_entities)} entities simultaneously at tick {tick}",
                        context={"node_id": node_id, "entities_count": len(unique_entities), "entity_ids": unique_entities}
                    ))
        return anomalies
