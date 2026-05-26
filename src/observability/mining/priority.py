# Compliance IDs: OBS-PH9-M53
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PriorityScorer:
    """Calculates prioritized score rankings for investigation candidates based on frequency, severity, and blast radius."""
    
    @classmethod
    def calculate_priority(cls, candidate: Dict[str, Any]) -> str:
        category = candidate.get("category", "unknown")
        severity = candidate.get("severity", "warning").lower()
        frequency_ratio = candidate.get("frequency_ratio", 0.0)
        
        # P0 Correctness, determinism, invariant corruption
        if category == "determinism_failure" or category == "hard_law_failure" or severity == "critical":
            return "P0"
            
        # P1 Repeated liveness or collapse failures
        if frequency_ratio >= 0.20 and (severity == "warning" or "stuck" in category or "stall" in category):
            return "P1"
            
        # P2 General balance issues across multiple seeds
        if frequency_ratio >= 0.05:
            return "P2"
            
        # P3 Rare anomalies or weak signals
        if frequency_ratio > 0.0:
            return "P3"
            
        # P4 Interesting stories
        return "P4"


class EngineeringBacklogGenerator:
    """Ranks mined pattern candidates and compiles a structured developer action catalog."""
    
    @classmethod
    def generate_backlog(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        
        # Load quality and determinism reports to capture P0 failures
        determinism_file = os.path.join(experiment_dir, "determinism_audit.json")
        quality_file = os.path.join(experiment_dir, "data_quality_report.json")
        patterns_file = os.path.join(experiment_dir, "pattern_mining_report.json")
        
        candidates = []
        
        # 1. Check determinism failure
        if os.path.exists(determinism_file):
            try:
                with open(determinism_file, "r", encoding="utf-8") as f:
                    det = json.load(f)
                    if det.get("verdict") == "CONFIRMED_NONDETERMINISM":
                        for fail in det.get("determinism_failures", []):
                            seed = fail.get("seed")
                            candidates.append({
                                "candidate_id": f"det_fail_seed_{seed}",
                                "category": "determinism_failure",
                                "title": f"Nondeterminism Divergence in Seed {seed}",
                                "severity": "critical",
                                "frequency_ratio": 1.0,
                                "affected_runs": fail.get("runs_evaluated", []),
                                "affected_seeds": [seed],
                                "reproduction_seed": seed,
                                "tick_window": f"Divergence detected at Tick {fail.get('earliest_divergence_tick')}",
                                "evidence": f"Unique state hashes generated: {', '.join(fail.get('unique_hashes', []))}",
                                "suggested_step": "Inspect shared state mutations, unordered dict iterations, or thread safety in Kernel ticks."
                            })
            except Exception as e:
                logger.warning(f"Error parsing determinism backlog candidates: {e}")
                
        # 2. Check pattern anomalies
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    patterns = json.load(f)
                    total_runs = len(patterns.get("outlier_runs", []))
                    if total_runs == 0:
                        total_runs = 100 # Fallback
                        
                    for rec in patterns.get("recurring_anomalies", []):
                        rule_id = rec.get("rule_id", "unknown")
                        count = rec.get("occurrence_count", 0)
                        affected = rec.get("affected_runs", 0)
                        freq = affected / total_runs
                        
                        # Generate specific debug suggestion based on rule name
                        step = "Perform trace analysis of the affected entities or subsystems."
                        if "stuck" in rule_id.lower() or "navigation" in rule_id.lower():
                            step = "Check pathfinding node validity, regional boundary thresholds, or obstacle congestion weights."
                        elif "economy" in rule_id.lower() or "price" in rule_id.lower():
                            step = "Check resource transaction tax, merchant shop reserves, or item depletion ratios."
                        elif "quest" in rule_id.lower():
                            step = "Check blacksmith progression conditions or reward delivery inventory slots."
                            
                        candidates.append({
                            "candidate_id": f"anomaly_pattern_{rule_id}",
                            "category": "balance_issue" if "balance" in rule_id.lower() else "liveness_failure",
                            "title": f"Recurring Anomaly Rule: {rule_id}",
                            "severity": rec.get("severity", "warning"),
                            "frequency_ratio": freq,
                            "affected_runs": [],  # Filled in by evidence pack builder
                            "affected_seeds": [],
                            "reproduction_seed": None,
                            "tick_window": "Varying windows",
                            "evidence": f"Triggered {count} times across {affected} seeds.",
                            "suggested_step": step
                        })
            except Exception as e:
                logger.warning(f"Error parsing anomaly backlog candidates: {e}")
                
        # Score priority on all candidates
        for c in candidates:
            c["priority"] = PriorityScorer.calculate_priority(c)
            
        # Sort backlog: P0 first, then P1, P2, P3, P4
        pri_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        candidates.sort(key=lambda x: (pri_order.get(x["priority"], 5), -x["frequency_ratio"]))
        
        backlog = {
            "experiment_id": experiment_id,
            "backlog_items": candidates,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save JSON
        with open(os.path.join(experiment_dir, "engineering_backlog.json"), "w", encoding="utf-8") as f:
            json.dump(backlog, f, indent=2)
            
        # Save MD
        cls._write_markdown_backlog(backlog, os.path.join(experiment_dir, "engineering_backlog.md"))
        
        return backlog
        
    @classmethod
    def _write_markdown_backlog(cls, backlog: Dict[str, Any], path: str) -> None:
        md = f"""# Engineering Backlog

**Experiment ID**: `{backlog["experiment_id"]}`
**Generated**: `{backlog["created_at"]}`

---

## Ranked Debugging Backlog
"""
        for i, item in enumerate(backlog["backlog_items"][:10]):
            md += f"""### {i+1}. [{item["priority"]}] {item["title"]}
*   **Subsystem Category**: `{item["category"]}`
*   **Evidence Summary**: {item["evidence"]}
*   **Earliest Divergence Tick / Window**: {item["tick_window"]}
*   **Suggested Debugging Step**: **{item["suggested_step"]}**
*   **Best Reproduction Seed**: `{item["reproduction_seed"] or "Run sweeps to identify worst"}`

---
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
