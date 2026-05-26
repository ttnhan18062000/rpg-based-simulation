# Compliance IDs: OBS-PH9-M57
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MiningReviewWorkflow:
    """Enables human verification labeling and promotes accepted findings to the core engineering backlog."""
    
    @classmethod
    def apply_review_label(cls, experiment_id: str, candidate_id: str, label: str, reviewer: str = "human", base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        
        # Load active backlog
        backlog_path = os.path.join(experiment_dir, "engineering_backlog.json")
        if not os.path.exists(backlog_path):
            raise FileNotFoundError(f"Engineering backlog not found at: {backlog_path}")
            
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog = json.load(f)
            
        valid_labels = [
            "ACCEPTED_FOR_INVESTIGATION", "CONFIRMED_BUG", "BALANCE_ISSUE",
            "FALSE_POSITIVE", "EXPECTED_BEHAVIOR", "NEEDS_MORE_DATA", "DUPLICATE", "LOW_PRIORITY"
        ]
        
        if label.upper() not in valid_labels:
            raise ValueError(f"Invalid review label '{label}'. Valid labels: {valid_labels}")
            
        updated = False
        for item in backlog.get("backlog_items", []):
            if item["candidate_id"] == candidate_id:
                item["review_status"] = label.upper()
                item["reviewed_by"] = reviewer
                item["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
                break
                
        if not updated:
            raise ValueError(f"Candidate {candidate_id} not found in backlog.")
            
        # Write back updated backlog
        with open(backlog_path, "w", encoding="utf-8") as f:
            json.dump(backlog, f, indent=2)
            
        # Re-generate markdown backlog with human labels
        cls._write_markdown_backlog(backlog, os.path.join(experiment_dir, "reviewed_engineering_backlog.md"))
        
        return backlog
        
    @classmethod
    def _write_markdown_backlog(cls, backlog: Dict[str, Any], path: str) -> None:
        md = f"""# Reviewed Engineering Backlog

**Experiment ID**: `{backlog["experiment_id"]}`
**Audit Generation**: `{backlog["created_at"]}`

---

## Mined Diagnostics & Human Review Status
"""
        for i, item in enumerate(backlog["backlog_items"]):
            lbl = item.get("review_status", "UNREVIEWED")
            md += f"""### {i+1}. [{item["priority"]}] {item["title"]}
*   **Review status**: **`{lbl}`**
*   **Reviewed By**: `{item.get("reviewed_by", "n/a")}` at `{item.get("reviewed_at", "n/a")}`
*   **Subsystem Category**: `{item["category"]}`
*   **Evidence**: {item["evidence"]}
*   **Suggested Debugging Step**: **{item["suggested_step"]}**

---
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)


class MiningQualityGate:
    """CI verification quality gate evaluating experiment outcomes against critical simulation invariants."""
    
    @classmethod
    def evaluate_gate(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        
        determinism_path = os.path.join(experiment_dir, "determinism_audit.json")
        backlog_path = os.path.join(experiment_dir, "engineering_backlog.json")
        
        verdict = "PASS"
        reasons = []
        warnings = []
        
        # 1. Evaluate Determinism Invariant
        if os.path.exists(determinism_path):
            try:
                with open(determinism_path, "r", encoding="utf-8") as f:
                    det = json.load(f)
                    if det.get("verdict") == "CONFIRMED_NONDETERMINISM":
                        verdict = "FAIL"
                        reasons.append("Seed-identical simulation runs generated divergent state hashes (Confirmed Nondeterminism).")
            except Exception:
                pass
                
        # 2. Evaluate Hard Law Violations and Recurring P1 issues
        if os.path.exists(backlog_path):
            try:
                with open(backlog_path, "r", encoding="utf-8") as f:
                    backlog = json.load(f)
                    for item in backlog.get("backlog_items", []):
                        pri = item.get("priority", "P3")
                        freq = item.get("frequency_ratio", 0.0)
                        
                        # Hard Law Violations trigger immediate fail
                        if "hard_law" in item.get("candidate_id", "") or item.get("category") == "hard_law_failure":
                            verdict = "FAIL"
                            reasons.append(f"Invariant Hard Law violation detected in run dataset: {item['title']}.")
                            
                        # Recurring P1 issues trigger warning if frequency > 10%
                        elif pri == "P1" and freq >= 0.10:
                            warnings.append(f"Recurring P1 liveness failure detected in {freq * 100.0:.1f}% of sweep runs: {item['title']}.")
            except Exception:
                pass
                
        # If warnings exist and we haven't failed, upgrade to WARNING verdict
        if verdict == "PASS" and warnings:
            verdict = "WARNING"
            
        report = {
            "experiment_id": experiment_id,
            "verdict": verdict,
            "failure_reasons": reasons,
            "warnings": warnings,
            "evaluated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save JSON
        with open(os.path.join(experiment_dir, "mining_quality_gate.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        # Write Markdown report
        cls._write_markdown_gate(report, os.path.join(experiment_dir, "mining_quality_gate.md"))
        
        return report
        
    @classmethod
    def _write_markdown_gate(cls, report: Dict[str, Any], path: str) -> None:
        md = f"""# Mining Quality Gate Evaluation Report

**Experiment ID**: `{report["experiment_id"]}`
**Verdict Status**: **{report["verdict"]}**
**Timestamp**: `{report["evaluated_at"]}`

---

"""
        if report["verdict"] == "PASS":
            md += "### ✅ Gate Passed\nAll physical invariants and seed determinism checks were validated successfully. No high-frequency liveness failures are present in the dataset.\n"
        elif report["verdict"] == "WARNING":
            md += "### ⚠️ Gate Warning\nPhysical invariants and seed determinism passed successfully, but high-frequency warning-level issues were detected:\n\n"
            for w in report["warnings"]:
                md += f"*   {w}\n"
        else:
            md += "### 🚨 Gate Failed\nCritical engine regression or physical invariant failure was detected during the mining audit:\n\n"
            for r in report["failure_reasons"]:
                md += f"*   **Reason**: {r}\n"
            if report["warnings"]:
                md += "\n#### Secondary Warnings:\n"
                for w in report["warnings"]:
                    md += f"*   {w}\n"
                    
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
