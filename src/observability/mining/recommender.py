# Compliance IDs: OBS-PH9-M56
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class InstrumentationGapDetector:
    """Identifies missing telemetry spans or signal gaps in collected run events."""
    
    @classmethod
    def detect_gaps(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> List[Dict[str, Any]]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        backlog_path = os.path.join(experiment_dir, "engineering_backlog.json")
        
        gaps = []
        if not os.path.exists(backlog_path):
            return gaps
            
        try:
            with open(backlog_path, "r", encoding="utf-8") as f:
                backlog = json.load(f)
                
            for item in backlog.get("backlog_items", []):
                category = item.get("category", "")
                rule_id = item.get("candidate_id", "")
                
                # Check for known instrumentation gaps
                if "quest" in rule_id.lower() or category == "quest":
                    gaps.append({
                        "issue": item["title"],
                        "missing_data": "quest_objective_progress_delta",
                        "recommended_instrumentation": "Emit QuestStepProgressEvent detailing active inventory slot states at tick boundary."
                    })
                elif "navigation" in rule_id.lower() or "stuck" in rule_id.lower():
                    gaps.append({
                        "issue": item["title"],
                        "missing_data": "collision_congested_node_coordinate",
                        "recommended_instrumentation": "Emit PathfindingRecalculationEvent when path score recalculation exceeds 3 ticks."
                    })
                elif "economy" in rule_id.lower() or "freeze" in rule_id.lower():
                    gaps.append({
                        "issue": item["title"],
                        "missing_data": "merchant_transaction_rejection_reason",
                        "recommended_instrumentation": "Add merchant_gold_balance and shop_transaction_rejections metrics to tick windows."
                    })
        except Exception as e:
            logger.warning(f"Error executing InstrumentationGapDetector: {e}")
            
        return gaps


class NextExperimentRecommender:
    """Formulates next experiment specifications based on structural data completeness and diagnostic outcomes."""
    
    @classmethod
    def recommend_next(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        
        gaps = InstrumentationGapDetector.detect_gaps(experiment_id, base_dir)
        
        # Formulate next concrete experiment recommendations
        recommendations = []
        
        # Check if we had determinism failures
        det_audit_path = os.path.join(experiment_dir, "determinism_audit.json")
        if os.path.exists(det_audit_path):
            try:
                with open(det_audit_path, "r", encoding="utf-8") as f:
                    det = json.load(f)
                    if det.get("verdict") == "CONFIRMED_NONDETERMINISM":
                        for fail in det.get("determinism_failures", []):
                            seed = fail.get("seed")
                            recommendations.append({
                                "experiment_type": "same_seed_repeat",
                                "purpose": "Isolate earliest divergence coordinate for seed-specific nondeterminism",
                                "parameters": {
                                    "seeds": [seed],
                                    "repeat_count": 20,
                                    "observability_profile": "full",
                                    "ticks": 2000
                                }
                            })
            except Exception:
                pass
                
        # General sweep optimization recommendation
        recommendations.append({
            "experiment_type": "multi_seed_sweep",
            "purpose": "Verify resource conservation across high-density regions",
            "parameters": {
                "scenario_name": "RESOURCE_ECONOMY_1000",
                "seeds": [100, 200, 300, 400],
                "ticks": 10000,
                "observability_profile": "light"
            }
        })
        
        report = {
            "experiment_id": experiment_id,
            "detected_gaps": gaps,
            "recommended_experiments": recommendations,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save JSON
        with open(os.path.join(experiment_dir, "next_experiment_suggestions.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        # Write Markdown report
        cls._write_markdown_report(report, os.path.join(experiment_dir, "next_experiment_report.md"))
        
        return report
        
    @classmethod
    def _write_markdown_report(cls, report: Dict[str, Any], path: str) -> None:
        md = f"""# Next Experiments & Instrumentation Recommendations

**Experiment ID**: `{report["experiment_id"]}`
**Timestamp**: `{report["created_at"]}`

---

## 🔍 Telemetry Instrumentation Gaps
"""
        if not report["detected_gaps"]:
            md += "*   No severe instrumentation gaps detected. The current metric/event coverage is sufficient.\n"
        else:
            for g in report["detected_gaps"]:
                md += f"""### Issue: {g["issue"]}
*   **Missing Telemetry Data**: `{g["missing_data"]}`
*   **Suggested Action**: {g["recommended_instrumentation"]}

"""
                
        md += "\n## 🧪 Recommended Follow-up Experiments\n"
        for r in report["recommended_experiments"]:
            md += f"""### Mode: `{r["experiment_type"]}`
*   **Purpose**: {r["purpose"]}
*   **Parameters**:
    *   Seeds: `{r["parameters"].get("seeds")}`
    *   Ticks: `{r["parameters"].get("ticks")}`
    *   Observability Mode: `{r["parameters"].get("observability_profile")}`

"""
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
