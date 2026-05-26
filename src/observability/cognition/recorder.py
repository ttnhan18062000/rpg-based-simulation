"""
Cognition Graph Snapshot Recorder and Capture Policy.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Dict, Set, List, Any, Optional

from src.core.state import AuthoritativeState, EntityState
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.systems.strategic_systems.cognition_export import CognitionGraphExporter
from src.observability.cognition.schema import build_snapshot_record

logger = logging.getLogger(__name__)


class CognitionCapturePolicy:
    """
    Governs when to capture cognition snapshots for entities.
    Prevents bloat by only capturing on anomaly triggers or state switches.
    """

    def __init__(self, selected_entity_ids: Optional[Set[int]] = None):
        # Programmatic selected/debug entity ids (e.g. HERO entities)
        self.selected_entity_ids = selected_entity_ids or set()
        # Track previous strategic states per entity to detect changes across ticks
        # {entity_id: {"project_id": ..., "objective_id": ..., "blockers": ..., "leads": ..., "concerns": ..., "overload": ...}}
        self._prev_states: Dict[int, Dict[str, Any]] = {}

    def should_capture(self, entity: EntityState, tick: int, reason: str) -> bool:
        """Determines if a snapshot should be taken based on ObservabilityMode rules."""
        mode = ObservabilityConfig.get_mode()
        if mode == ObservabilityMode.OFF:
            return False

        # Anomalies and boundary checkpoints are captured in all active modes
        if reason in ("ANOMALY_TRIGGERED", "CERTIFICATION_BOUNDARY", "EVIDENCE_PACK_REQUEST"):
            return True

        # In LIGHT/LONG_RUN modes, only anomalies are captured
        if mode in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
            return False

        # In DEBUG/CERTIFICATION modes, selected or debug entities capture state changes
        if mode in (ObservabilityMode.DEBUG, ObservabilityMode.CERTIFICATION):
            # If selected_entity_ids is empty, default to capturing all active entities
            if not self.selected_entity_ids or entity.id in self.selected_entity_ids:
                return True

        return False

    def detect_state_changes(self, entity: EntityState) -> List[str]:
        """
        Compares current strategic components with the previous tick.
        Returns a list of triggered reason strings (e.g. 'PROJECT_CHANGED').
        """
        strat = getattr(entity, "strategic", None)
        if strat is None:
            return []

        eid = entity.id
        current_project = strat.current_project_id
        current_objective = strat.current_objective_id
        current_overload = strat.primary_overload_source

        # Extract stable sets of blocker, lead, and concern IDs
        current_blockers = set(strat.blockers.keys())
        current_leads = set(strat.leads.keys())
        current_concerns = set(strat.concerns.keys())

        # If no baseline exists, initialize and return empty list
        if eid not in self._prev_states:
            self._prev_states[eid] = {
                "project_id": current_project,
                "objective_id": current_objective,
                "overload": current_overload,
                "blockers": current_blockers,
                "leads": current_leads,
                "concerns": current_concerns,
            }
            return []

        prev = self._prev_states[eid]
        reasons = []

        if current_project != prev["project_id"]:
            reasons.append("PROJECT_CHANGED")
        if current_objective != prev["objective_id"]:
            reasons.append("OBJECTIVE_CHANGED")
        if current_overload != prev["overload"]:
            reasons.append("OVERLOAD_CHANGED")
        if current_blockers != prev["blockers"]:
            reasons.append("BLOCKER_CHANGED")
        if current_leads != prev["leads"]:
            reasons.append("LEAD_CHANGED")
        if current_concerns != prev["concerns"]:
            reasons.append("CONCERN_CHANGED")

        # Update cache for next tick
        self._prev_states[eid] = {
            "project_id": current_project,
            "objective_id": current_objective,
            "overload": current_overload,
            "blockers": current_blockers,
            "leads": current_leads,
            "concerns": current_concerns,
        }

        return reasons


class ObservabilityCognitionRecorder:
    """
    Thread-safe post-commit recorder for cognition snapshots and diffs.
    Writes snap records to cognition_graph_snapshots.jsonl and diffs to cognition_graph_diffs.jsonl.
    Maps significant cognition changes into high-salience SimulationEvents registered post-commit.
    """

    def __init__(self, run_id: str, run_dir: Optional[str] = None):
        self.run_id = run_id
        self.run_dir = run_dir or f"data/runs/{run_id}"
        self.policy = CognitionCapturePolicy()
        self._snapshots_file = os.path.join(self.run_dir, "cognition_graph_snapshots.jsonl")
        self._diffs_file = os.path.join(self.run_dir, "cognition_graph_diffs.jsonl")

        # Track last snapshot per entity to compute incremental diffs
        self._last_snapshots: Dict[int, Dict[str, Any]] = {}

        # Stateful event mapper to preserve detour counts for loop detection
        from src.observability.cognition.event_mapper import CognitionEventMapper
        self.event_mapper = CognitionEventMapper()

    def record_tick(
        self,
        state: AuthoritativeState,
        tick: int,
        events: Optional[List[Any]] = None,
        event_recorder: Optional[Any] = None,
    ) -> None:
        """
        Evaluates and records snapshots/diffs for active strategic entities in the tick.
        Must run strictly post-commit with no state mutations.
        """
        mode = ObservabilityConfig.get_mode()
        if mode == ObservabilityMode.OFF:
            return

        # Ensure run directory exists
        os.makedirs(self.run_dir, exist_ok=True)

        # 1. Identify which entities have active anomaly triggers this tick
        anomaly_entities: Set[int] = set()
        trigger_meta: Dict[int, Dict[str, str]] = {}

        if events:
            for event in events:
                # Map standard anomalies to their entity ID
                is_anomaly = (
                    event.event_type in ("NavigationStuck", "QuestStalled", "ResourceProductionZero", "InvariantViolation")
                    or getattr(event, "event_category", "") == "anomaly"
                )
                if is_anomaly and getattr(event, "entity_id", None) is not None:
                    anomaly_entities.add(event.entity_id)
                    trigger_meta[event.entity_id] = {
                        "trigger_event_id": getattr(event, "event_id", None) or getattr(event, "id", None) or "",
                        "trigger_anomaly_id": event.event_type
                    }

        # 2. Iterate through all entities having a strategic component
        records_to_write = []
        diffs_to_write = []
        events_to_record = []

        for entity in state.entities.values():
            if getattr(entity, "strategic", None) is None:
                continue

            eid = entity.id

            # Detect any strategic change triggers
            change_reasons = self.policy.detect_state_changes(entity)

            # Gather all candidate reasons to evaluate for this entity
            reasons_to_eval = []
            if eid in anomaly_entities:
                reasons_to_eval.append("ANOMALY_TRIGGERED")

            # Add state change reasons if they occurred
            reasons_to_eval.extend(change_reasons)

            # Fallback debug reason if selected for debug mode and no changes occurred
            if not reasons_to_eval and mode == ObservabilityMode.DEBUG:
                reasons_to_eval.append("DEBUG_SELECTED_ENTITY")

            # Determine the primary reason to record (priority: Anomaly > Strategic changes > Debug)
            primary_reason = None
            for r in ("ANOMALY_TRIGGERED", "PROJECT_CHANGED", "OBJECTIVE_CHANGED", "BLOCKER_CHANGED", "LEAD_CHANGED", "CONCERN_CHANGED", "OVERLOAD_CHANGED", "DEBUG_SELECTED_ENTITY"):
                if r in reasons_to_eval:
                    primary_reason = r
                    break

            if not primary_reason:
                continue

            # Evaluate capture policy
            if self.policy.should_capture(entity, tick, primary_reason):
                # Export the read-only graph snapshot
                graph = CognitionGraphExporter.export(entity)

                # Prepare list of node and edge dictionaries conforming to schema
                nodes_list = []
                for n in graph.nodes:
                    nodes_list.append({
                        "node_id": n.id,
                        "kind": n.kind,
                        "label": n.label,
                        "metadata": n.attributes
                    })

                edges_list = []
                for e in graph.edges:
                    edges_list.append({
                        "source_id": e.source,
                        "target_id": e.target,
                        "kind": e.kind
                    })

                # Fetch extra details
                meta = trigger_meta.get(eid, {})
                curr_proj_id = graph.metadata.get("current_project")
                source_goal_score = None
                target_pos = None
                if curr_proj_id:
                    proj = entity.strategic.projects.get(curr_proj_id)
                    if proj:
                        source_goal_score = proj.score
                        if proj.objectives:
                            active_obj = next((o for o in proj.objectives if o.id == proj.active_objective_id), proj.objectives[0])
                            target_pos = list(active_obj.target_position) if active_obj.target_position else None

                resulting_action = entity.task.work_kind if entity.task else None
                
                curr_snapshot = build_snapshot_record(
                    run_id=self.run_id,
                    tick=tick,
                    entity_id=eid,
                    reason=primary_reason,
                    nodes=nodes_list,
                    edges=edges_list,
                    trigger_event_id=meta.get("trigger_event_id"),
                    trigger_anomaly_id=meta.get("trigger_anomaly_id"),
                    current_project_id=curr_proj_id,
                    current_objective_id=graph.metadata.get("current_objective"),
                    overload_source=graph.metadata.get("overload_source"),
                    source_goal_score=source_goal_score,
                    resulting_action=resulting_action,
                    target_pos=target_pos,
                )
                records_to_write.append(curr_snapshot)

                # Retrieve last snapshot to compute diff
                prev_snapshot = self._last_snapshots.get(eid)
                
                # Compute deterministic diff
                from src.observability.cognition.diff_builder import CognitionGraphDiffBuilder
                diff_rec = CognitionGraphDiffBuilder.compute_diff(
                    run_id=self.run_id,
                    tick=tick,
                    entity_id=eid,
                    reason=primary_reason,
                    prev_snapshot=prev_snapshot,
                    curr_snapshot=curr_snapshot
                )
                diffs_to_write.append(diff_rec)

                # Map diff to simulation events
                mapped = self.event_mapper.map_diff_to_events(diff_rec, prev_snapshot, curr_snapshot)
                events_to_record.extend(mapped)

                # Update snapshot history cache for subsequent diffing
                self._last_snapshots[eid] = curr_snapshot

        # Persist snapshots to file atomically
        if records_to_write:
            with open(self._snapshots_file, "a", encoding="utf-8") as f:
                for rec in records_to_write:
                    f.write(json.dumps(rec) + "\n")

        # Persist diffs to file atomically
        if diffs_to_write:
            with open(self._diffs_file, "a", encoding="utf-8") as f:
                for diff in diffs_to_write:
                    f.write(json.dumps(diff) + "\n")

        # Dispatch mapped simulation events post-commit
        if events_to_record and event_recorder:
            for ev in events_to_record:
                event_recorder.record(ev)
