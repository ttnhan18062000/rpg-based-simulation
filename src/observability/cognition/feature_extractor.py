"""
Cognition Feature Extractor for aggregating strategic metrics from cognition snapshots and diffs.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CognitionFeatureExtractor:
    """
    Extracts run-entity-level strategic features from cognition snapshot and diff logs.
    """

    @classmethod
    def extract_features(
        cls,
        run_dir: str,
        spec_data: Optional[Dict[str, Any]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Extracts strategic cognition features for each active strategic entity in the run.
        Returns a dictionary mapping entity_id to its feature record.
        """
        spec = spec_data or {}
        run_id = spec.get("run_id") or os.path.basename(run_dir.rstrip("/")) or "unknown_run"
        seed = spec.get("seed", 0)
        scenario_name = spec.get("scenario") or spec.get("scenario_name") or ""
        scenario_type = spec.get("scenario_type") or ""

        snapshots_file = os.path.join(run_dir, "cognition_graph_snapshots.jsonl")
        diffs_file = os.path.join(run_dir, "cognition_graph_diffs.jsonl")

        # 1. Clean support for runs with zero cognition logs without crashes
        if not os.path.exists(snapshots_file):
            logger.info(f"No cognition snapshots file found at {snapshots_file}. Returning empty features.")
            return {}

        # Load snapshots
        entity_snapshots: Dict[int, List[Dict[str, Any]]] = {}
        try:
            with open(snapshots_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        snap = json.loads(line)
                        eid = snap.get("entity_id")
                        if eid is not None:
                            entity_snapshots.setdefault(eid, []).append(snap)
                    except Exception as e:
                        logger.warning(f"Error parsing snapshot line: {e}")
        except Exception as e:
            logger.warning(f"Failed to read snapshots file {snapshots_file}: {e}")
            return {}

        if not entity_snapshots:
            return {}

        # Load diffs
        entity_diffs: Dict[int, List[Dict[str, Any]]] = {}
        if os.path.exists(diffs_file):
            try:
                with open(diffs_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            diff = json.loads(line)
                            eid = diff.get("entity_id")
                            if eid is not None:
                                entity_diffs.setdefault(eid, []).append(diff)
                        except Exception as e:
                            logger.warning(f"Error parsing diff line: {e}")
            except Exception as e:
                logger.warning(f"Failed to read diffs file {diffs_file}: {e}")

        features_by_entity: Dict[int, Dict[str, Any]] = {}

        # 2. Extract features per entity
        for entity_id, snapshots in entity_snapshots.items():
            # Sort snapshots and diffs by tick
            snapshots.sort(key=lambda x: x.get("tick", 0))
            diffs = entity_diffs.get(entity_id, [])
            diffs.sort(key=lambda x: x.get("tick", 0))

            snapshot_count = len(snapshots)
            diff_count = len(diffs)

            # Switch counts
            project_switch_count = sum(1 for d in diffs if d.get("current_project_changed"))
            objective_switch_count = sum(1 for d in diffs if d.get("current_objective_changed"))

            # Build maps for node kinds and labels
            node_kinds: Dict[str, str] = {}
            node_labels: Dict[str, str] = {}
            for snap in snapshots:
                for node in snap.get("graph", {}).get("nodes", []):
                    node_id = node.get("node_id")
                    if node_id:
                        node_kinds[node_id] = node.get("kind", "unknown")
                        node_labels[node_id] = node.get("label", "")

            # Count additions and resolutions
            blocker_add_count = 0
            blocker_resolve_count = 0
            detour_created_count = 0
            lead_exhaustion_count = 0
            concern_raise_count = 0
            hypothesis_change_count = 0

            for d in diffs:
                for nid in d.get("added_nodes", []):
                    kind = node_kinds.get(nid, "unknown")
                    if kind == "blocker":
                        blocker_add_count += 1
                    elif kind == "concern":
                        concern_raise_count += 1
                    elif kind == "hypothesis":
                        hypothesis_change_count += 1
                    elif kind == "project":
                        label = node_labels.get(nid, "")
                        if "detour" in label.lower() or "detour" in nid.lower():
                            detour_created_count += 1

                for nid in d.get("removed_nodes", []):
                    kind = node_kinds.get(nid, "unknown")
                    if kind == "blocker":
                        blocker_resolve_count += 1
                    elif kind == "lead":
                        lead_exhaustion_count += 1

            # Unresolved blockers in the latest snapshot
            latest_snap = snapshots[-1]
            unresolved_blockers = [
                n for n in latest_snap.get("graph", {}).get("nodes", [])
                if n.get("kind") == "blocker"
            ]
            unresolved_blocker_count = len(unresolved_blockers)

            # Overload count (snapshots with overload source)
            overload_count = sum(1 for s in snapshots if s.get("overload_source") is not None)

            # Latest project and objective
            latest_current_project = latest_snap.get("current_project_id")
            latest_current_objective = latest_snap.get("current_objective_id")

            # Max project age
            project_intervals: Dict[str, List[tuple[int, int]]] = {}
            current_proj = None
            start_tick = None
            for snap in snapshots:
                tick = snap.get("tick", 0)
                proj = snap.get("current_project_id")
                if proj != current_proj:
                    if current_proj is not None and start_tick is not None:
                        project_intervals.setdefault(current_proj, []).append((start_tick, tick))
                    current_proj = proj
                    start_tick = tick
            if current_proj is not None and start_tick is not None:
                project_intervals.setdefault(current_proj, []).append((start_tick, snapshots[-1].get("tick", start_tick)))

            max_project_age = 0
            for intervals in project_intervals.values():
                for start, end in intervals:
                    max_project_age = max(max_project_age, end - start)

            # Max blocker age
            blocker_presence: Dict[str, List[int]] = {}
            for snap in snapshots:
                tick = snap.get("tick", 0)
                for node in snap.get("graph", {}).get("nodes", []):
                    if node.get("kind") == "blocker":
                        blocker_presence.setdefault(node["node_id"], []).append(tick)

            max_blocker_age = 0
            latest_tick = snapshots[-1].get("tick", 0)
            for bid, ticks in blocker_presence.items():
                if not ticks:
                    continue
                start = ticks[0]
                is_unresolved = any(
                    n.get("node_id") == bid for n in latest_snap.get("graph", {}).get("nodes", [])
                )
                if is_unresolved:
                    end = latest_tick
                else:
                    end = ticks[-1]
                    for snap in snapshots:
                        if snap.get("tick", 0) > ticks[-1]:
                            end = snap.get("tick", 0)
                            break
                max_blocker_age = max(max_blocker_age, end - start)

            # Graph churn rate (project switches / elapsed ticks)
            first_tick = snapshots[0].get("tick", 0)
            elapsed = latest_tick - first_tick
            graph_churn_rate = 0.0
            if elapsed > 0:
                graph_churn_rate = float(project_switch_count) / elapsed

            features_by_entity[entity_id] = {
                "run_id": run_id,
                "seed": seed,
                "entity_id": entity_id,
                "scenario_name": scenario_name,
                "scenario_type": scenario_type,
                "snapshot_count": snapshot_count,
                "diff_count": diff_count,
                "project_switch_count": project_switch_count,
                "objective_switch_count": objective_switch_count,
                "blocker_add_count": blocker_add_count,
                "blocker_resolve_count": blocker_resolve_count,
                "unresolved_blocker_count": unresolved_blocker_count,
                "lead_exhaustion_count": lead_exhaustion_count,
                "concern_raise_count": concern_raise_count,
                "hypothesis_change_count": hypothesis_change_count,
                "detour_created_count": detour_created_count,
                "overload_count": overload_count,
                "max_project_age": max_project_age,
                "max_blocker_age": max_blocker_age,
                "graph_churn_rate": graph_churn_rate,
                "latest_current_project": latest_current_project,
                "latest_current_objective": latest_current_objective,
            }

        # Write to cognition_features.jsonl in run_dir
        features_file = os.path.join(run_dir, "cognition_features.jsonl")
        try:
            with open(features_file, "w", encoding="utf-8") as f:
                for record in features_by_entity.values():
                    f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write features file {features_file}: {e}")

        return features_by_entity
