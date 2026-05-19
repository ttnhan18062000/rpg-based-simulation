from __future__ import annotations
import uuid
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from src.observability.anomaly.rules_engine import AnomalyRecord

if TYPE_CHECKING:
    from src.observability.anomaly.pipeline import AnalysisContext

INVESTIGATION_HINTS = {
    "HardLawViolationDetected": [
        "Check authoritative sovereignty checks in regional move logic.",
        "Check actor state validation to ensure sleeping actors do not execute tick behaviors.",
        "Verify state serialization path for deep-copy invariance."
    ],
    "NavigationStuckBasic": [
        "Verify pathfinding obstacle map boundaries and tile legality.",
        "Verify tile occupancy limits to detect grid crowding.",
        "Check target actor reachability and stale coordinates.",
        "Ensure action movement cooldown ticks are not infinite."
    ],
    "QuestStalledBasic": [
        "Verify task delivery location reachability for quest completion.",
        "Check inventory constraints preventing delivery steps.",
        "Check reward dispenser logic to ensure quest lifecycle state transition."
    ],
    "ResourceProductionZero": [
        "Verify resource node active status and regeneration rates.",
        "Check harvester task assignment logic and travel times.",
        "Ensure storage capacity or shop returns do not block production loops."
    ],
    "GovernorDegradedTooLong": [
        "Check resource allocation rates and budget pressures.",
        "Verify actor behavior state queues under survival mode.",
        "Monitor system performance ticks for memory/load regressions."
    ]
}

class EvidenceBuilder:
    """
    Enriches raw anomalies with compact, JSON-serializable context payloads.
    """
    @staticmethod
    def build_evidence(anomaly: AnomalyRecord, context: AnalysisContext) -> Dict[str, Any]:
        """
        Builds and returns a compact, JSON-serializable evidence context payload.
        """
        # Determine source artifact
        source_artifact = "simulation_events.jsonl"
        details: Any = {}

        if anomaly.rule_id == "HardLawViolationDetected":
            source_artifact = "hard_law_violations.jsonl"
            # Find matching raw violations
            matches = []
            for v in context.hard_law_violations:
                v_tick = v.get("tick", 0)
                if anomaly.tick_start <= v_tick <= anomaly.tick_end:
                    matches.append(v)
            details = {"violations": matches[:5]}

        elif anomaly.rule_id == "NavigationStuckBasic":
            source_artifact = "simulation_events.jsonl"
            # Find matching NavigationStuck events
            matches = []
            for ev in context.events:
                if ev.event_type == "NavigationStuck" and ev.tick >= anomaly.tick_start and ev.tick <= anomaly.tick_end:
                    # check affected entities
                    if any(eid in anomaly.affected_entity_ids for eid in [ev.entity_id] if eid is not None):
                        matches.append({
                            "tick": ev.tick,
                            "entity_id": ev.entity_id,
                            "message": ev.message,
                            "payload": ev.payload
                        })
            details = {"stuck_events": matches[:5]}

        elif anomaly.rule_id == "QuestStalledBasic":
            source_artifact = "simulation_events.jsonl"
            # Find matching quest events
            matches = []
            for ev in context.events:
                if ev.event_type in ["QuestStarted", "QuestCompleted", "QuestRewardDelivered"]:
                    q_id = ev.quest_id
                    if q_id in anomaly.affected_quest_ids:
                        matches.append({
                            "tick": ev.tick,
                            "event_type": ev.event_type,
                            "entity_id": ev.entity_id,
                            "quest_id": q_id,
                            "message": ev.message
                        })
            details = {"quest_events": matches[:5]}

        elif anomaly.rule_id == "ResourceProductionZero":
            source_artifact = "metric_windows.jsonl"
            # Extract zero production windows
            matches = []
            for w in context.metric_windows:
                if w.window_start_tick >= anomaly.tick_start and w.window_end_tick <= anomaly.tick_end:
                    matches.append({
                        "window_start_tick": w.window_start_tick,
                        "window_end_tick": w.window_end_tick,
                        "gold_total_avg": w.gold_total_avg
                    })
            details = {"metric_windows": matches[:5]}

        elif anomaly.rule_id == "GovernorDegradedTooLong":
            source_artifact = "metric_windows.jsonl"
            # Extract degraded mode windows
            matches = []
            for w in context.metric_windows:
                if w.window_start_tick >= anomaly.tick_start and w.window_end_tick <= anomaly.tick_end:
                    matches.append({
                        "window_start_tick": w.window_start_tick,
                        "window_end_tick": w.window_end_tick,
                        "governor_mode_dominant": w.governor_mode_dominant
                    })
            details = {"metric_windows": matches[:5]}

        else:
            # Fallback event match
            matches = []
            for ev in context.events:
                if ev.tick >= anomaly.tick_start and ev.tick <= anomaly.tick_end:
                    if anomaly.affected_entity_ids and ev.entity_id in anomaly.affected_entity_ids:
                        matches.append({
                            "tick": ev.tick,
                            "event_type": ev.event_type,
                            "message": ev.message
                        })
            details = {"events": matches[:5]}

        return {
            "source_artifact": source_artifact,
            "tick_range": [anomaly.tick_start, anomaly.tick_end],
            "affected_ids": {
                "entities": anomaly.affected_entity_ids,
                "regions": anomaly.affected_region_ids,
                "resources": anomaly.affected_resource_ids,
                "quests": anomaly.affected_quest_ids
            },
            "details": details
        }

class AnomalyCluster(BaseModel):
    """
    Groups highly similar anomalies together deterministically to prevent reporting noise.
    """
    cluster_id: str
    rule_id: str
    severity: str
    region_id: Optional[str] = None
    resource_id: Optional[str] = None
    quest_id: Optional[str] = None
    affected_entity_ids: List[int] = Field(default_factory=list)
    tick_start: int
    tick_end: int
    evidence_samples: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_causes: List[str] = Field(default_factory=list)
    anomalies: List[AnomalyRecord] = Field(default_factory=list)

class TriageEngine:
    """
    Performs deterministic post-run clustering and triage analysis on simulation anomalies.
    """
    @staticmethod
    def cluster_anomalies(anomalies: List[AnomalyRecord]) -> List[AnomalyCluster]:
        """
        Clusters a flat list of anomalies by rule ID, severity, spatial/quest context, and overlapping tick bounds.
        """
        clusters: List[AnomalyCluster] = []
        for anomaly in anomalies:
            merged = False
            anomaly_region = anomaly.affected_region_ids[0] if anomaly.affected_region_ids else None
            anomaly_resource = anomaly.affected_resource_ids[0] if anomaly.affected_resource_ids else None
            anomaly_quest = anomaly.affected_quest_ids[0] if anomaly.affected_quest_ids else None

            for cluster in clusters:
                if cluster.rule_id != anomaly.rule_id:
                    continue
                if cluster.severity != anomaly.severity:
                    continue
                if cluster.region_id != anomaly_region:
                    continue
                if cluster.resource_id != anomaly_resource:
                    continue
                if cluster.quest_id != anomaly_quest:
                    continue

                # Check overlapping/intersecting tick range
                overlap = max(cluster.tick_start, anomaly.tick_start) <= min(cluster.tick_end, anomaly.tick_end)
                if overlap:
                    cluster.anomalies.append(anomaly)
                    cluster.tick_start = min(cluster.tick_start, anomaly.tick_start)
                    cluster.tick_end = max(cluster.tick_end, anomaly.tick_end)

                    for eid in anomaly.affected_entity_ids:
                        if eid not in cluster.affected_entity_ids:
                            cluster.affected_entity_ids.append(eid)

                    for cause in anomaly.suggested_causes:
                        if cause not in cluster.suggested_causes:
                            cluster.suggested_causes.append(cause)

                    if anomaly.evidence and len(cluster.evidence_samples) < 5:
                        cluster.evidence_samples.append(anomaly.evidence)

                    merged = True
                    break

            if not merged:
                evidence_samples = [anomaly.evidence] if anomaly.evidence else []
                new_cluster = AnomalyCluster(
                    cluster_id=f"cluster_{uuid.uuid4().hex[:8]}",
                    rule_id=anomaly.rule_id,
                    severity=anomaly.severity,
                    region_id=anomaly_region,
                    resource_id=anomaly_resource,
                    quest_id=anomaly_quest,
                    affected_entity_ids=list(anomaly.affected_entity_ids),
                    tick_start=anomaly.tick_start,
                    tick_end=anomaly.tick_end,
                    evidence_samples=evidence_samples,
                    suggested_causes=list(anomaly.suggested_causes),
                    anomalies=[anomaly]
                )
                clusters.append(new_cluster)

        # Sort clusters deterministically: severity (CRITICAL first, then ERROR, WARNING), rule_id, then tick_start
        severity_order = {"CRITICAL": 0, "ERROR": 1, "WARNING": 2}
        clusters.sort(key=lambda c: (severity_order.get(c.severity, 3), c.rule_id, c.tick_start))
        return clusters

class InvestigationHint:
    """
    Retrieves static/dynamic developer troubleshooting checklists for specific rule definitions.
    """
    @staticmethod
    def get_hints(rule_id: str) -> List[str]:
        return INVESTIGATION_HINTS.get(rule_id, ["Analyze corresponding anomaly event trails and metrics logs."])
