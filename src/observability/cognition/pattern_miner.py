"""
Cognition Pattern Miner for detecting strategic behavior anomalies across ticks and runs.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, List, Optional

from src.observability.cognition.feature_extractor import CognitionFeatureExtractor

logger = logging.getLogger(__name__)


class CognitionPatternMiner:
    """
    Analyzes strategic cognition features to detect 5 critical behavioral failure patterns.
    """

    DEFAULT_THRESHOLDS = {
        "project_churn": 3,
        "detour_loop": 2,
        "stale_blocker_age": 200,
        "lead_exhaustion_storm": 3,
        "strategic_overload": 3,
    }

    @classmethod
    def mine_patterns(
        cls,
        run_dir: str,
        spec_data: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs feature extraction over the run directory, applies pattern matching rules,
        persists matched patterns to cognition_patterns.json, and returns them.
        """
        spec = spec_data or {}
        run_id = spec.get("run_id") or os.path.basename(run_dir.rstrip("/")) or "unknown_run"
        seed = spec.get("seed", 0)
        scenario_name = spec.get("scenario") or spec.get("scenario_name") or ""
        scenario_type = spec.get("scenario_type") or ""

        # Extract features first
        features_map = CognitionFeatureExtractor.extract_features(run_dir, spec_data)
        if not features_map:
            # Write an empty JSON file to satisfy contract and avoid crash
            patterns_file = os.path.join(run_dir, "cognition_patterns.json")
            try:
                with open(patterns_file, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to write empty patterns file: {e}")
            return []

        # Resolve thresholds
        t = dict(cls.DEFAULT_THRESHOLDS)
        if thresholds:
            t.update(thresholds)

        mined_patterns: List[Dict[str, Any]] = []

        # Load raw snapshots/diffs for precise tick range finding
        snapshots_file = os.path.join(run_dir, "cognition_graph_snapshots.jsonl")
        snapshots: List[Dict[str, Any]] = []
        if os.path.exists(snapshots_file):
            try:
                with open(snapshots_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            snapshots.append(json.loads(line))
            except Exception:
                pass
        snapshots.sort(key=lambda x: x.get("tick", 0))

        # Evaluate rules for each strategic entity
        for entity_id, f in features_map.items():
            ent_snaps = [s for s in snapshots if s.get("entity_id") == entity_id]
            first_tick = ent_snaps[0].get("tick", 0) if ent_snaps else 0
            last_tick = ent_snaps[-1].get("tick", 0) if ent_snaps else 0

            # 1. ProjectChurn
            if f["project_switch_count"] >= t["project_churn"]:
                sev = "CRITICAL" if f["project_switch_count"] >= t["project_churn"] * 2 else "WARNING"
                mined_patterns.append({
                    "pattern_id": f"PAT-{run_id}-{entity_id}-CHURN",
                    "pattern_type": "ProjectChurn",
                    "severity": sev,
                    "affected_runs": [run_id],
                    "affected_entities": [entity_id],
                    "affected_seeds": [seed],
                    "tick_ranges": [[first_tick, last_tick]],
                    "evidence": {
                        "project_switch_count": f["project_switch_count"],
                        "message": f"Entity {entity_id} changed projects {f['project_switch_count']} times without completion.",
                    },
                    "suspected_subsystems": ["strategy_project_assignment", "actor_motivation_engine"],
                    "confidence": 0.85 if f["project_switch_count"] >= t["project_churn"] * 2 else 0.70,
                    "recommended_investigation": "Analyze motivation triggers and project completion criteria to find the root cause of project churning.",
                })

            # 2. DetourLoop
            if f["detour_created_count"] >= t["detour_loop"] and f["unresolved_blocker_count"] > 0:
                mined_patterns.append({
                    "pattern_id": f"PAT-{run_id}-{entity_id}-DETOUR_LOOP",
                    "pattern_type": "DetourLoop",
                    "severity": "CRITICAL",
                    "affected_runs": [run_id],
                    "affected_entities": [entity_id],
                    "affected_seeds": [seed],
                    "tick_ranges": [[first_tick, last_tick]],
                    "evidence": {
                        "detour_created_count": f["detour_created_count"],
                        "unresolved_blocker_count": f["unresolved_blocker_count"],
                        "message": f"Entity {entity_id} repeatedly created {f['detour_created_count']} detours while blocker remained active.",
                    },
                    "suspected_subsystems": ["strategy_detour_planner", "blocker_resolution_system"],
                    "confidence": 0.90,
                    "recommended_investigation": "Check if detour project goals are correctly matching blocker requirements, and trace why blocker clearance fails.",
                })

            # 3. StaleBlocker
            if f["max_blocker_age"] >= t["stale_blocker_age"] and f["unresolved_blocker_count"] > 0 and f["project_switch_count"] <= 1:
                # Find if any lead exists in latest snapshots
                leads_exist = False
                if ent_snaps:
                    leads_exist = any(
                        n.get("kind") == "lead"
                        for n in ent_snaps[-1].get("graph", {}).get("nodes", [])
                    )
                # Stale blocker is active blocker unresolved too long while leads exist (or lead exhaustion storm occurred)
                if leads_exist or f["lead_exhaustion_count"] > 0:
                    mined_patterns.append({
                        "pattern_id": f"PAT-{run_id}-{entity_id}-STALE_BLOCKER",
                        "pattern_type": "StaleBlocker",
                        "severity": "WARNING",
                        "affected_runs": [run_id],
                        "affected_entities": [entity_id],
                        "affected_seeds": [seed],
                        "tick_ranges": [[first_tick, last_tick]],
                        "evidence": {
                            "max_blocker_age": f["max_blocker_age"],
                            "message": f"Blocker unresolved for {f['max_blocker_age']} ticks while current project remains stalled.",
                        },
                        "suspected_subsystems": ["blocker_resolution_system", "agent_perception"],
                        "confidence": 0.80,
                        "recommended_investigation": "Verify blocker clearance triggers and verify why the entity lacks the capability to clear it.",
                    })

            # 4. LeadExhaustionStorm
            if f["lead_exhaustion_count"] >= t["lead_exhaustion_storm"]:
                mined_patterns.append({
                    "pattern_id": f"PAT-{run_id}-{entity_id}-EXHAUSTION_STORM",
                    "pattern_type": "LeadExhaustionStorm",
                    "severity": "WARNING",
                    "affected_runs": [run_id],
                    "affected_entities": [entity_id],
                    "affected_seeds": [seed],
                    "tick_ranges": [[first_tick, last_tick]],
                    "evidence": {
                        "lead_exhaustion_count": f["lead_exhaustion_count"],
                        "message": f"Entity {entity_id} experienced {f['lead_exhaustion_count']} lead exhaustions causing strategic stalls.",
                    },
                    "suspected_subsystems": ["lead_generation_system", "perception_sensor"],
                    "confidence": 0.85,
                    "recommended_investigation": "Check world state for available resources and verify if lead generation filters are overly restrictive.",
                })

            # 5. StrategicOverload
            if f["overload_count"] >= t["strategic_overload"]:
                mined_patterns.append({
                    "pattern_id": f"PAT-{run_id}-{entity_id}-OVERLOAD",
                    "pattern_type": "StrategicOverload",
                    "severity": "WARNING",
                    "affected_runs": [run_id],
                    "affected_entities": [entity_id],
                    "affected_seeds": [seed],
                    "tick_ranges": [[first_tick, last_tick]],
                    "evidence": {
                        "overload_count": f["overload_count"],
                        "message": f"Entity {entity_id} exceeded cognition bandwidth limits {f['overload_count']} times.",
                    },
                    "suspected_subsystems": ["strategy_bandwidth_enforcer", "cognitive_capacity_manager"],
                    "confidence": 0.90,
                    "recommended_investigation": "Review strategic limits and reduce the generation rate of incoming concerns/leads.",
                })

        # Save to cognition_patterns.json
        patterns_file = os.path.join(run_dir, "cognition_patterns.json")
        try:
            with open(patterns_file, "w", encoding="utf-8") as f:
                json.dump(mined_patterns, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write patterns file {patterns_file}: {e}")

        return mined_patterns
