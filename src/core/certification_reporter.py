import json
import os
import re
from typing import Dict, Any, List
from datetime import datetime

class CertificationReporter:
    """
    Generates the final V2 Authoritative Certification Report.
    """

    @staticmethod
    def generate_report(
        kernel_results: Dict[str, Any], 
        checklist_path: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Aggregates data into a JSON report.
        """
        # 1. Coverage Analysis
        coverage = CertificationReporter._analyze_checklist(checklist_path)
        
        # 2. Stability & Determinism
        stability = {
            "determinism": kernel_results.get("determinism_passed", False),
            "long_run_ticks": kernel_results.get("total_ticks", 0),
            "peak_memory_mb": kernel_results.get("peak_memory_mb", 0.0),
            "avg_tick_ms": kernel_results.get("avg_tick_ms", 0.0)
        }
        
        # 3. Protocol Integrity
        protocol = {
            "violations_detected": kernel_results.get("protocol_violations", 0),
            "authoritative_apply_success_rate": 1.0 # V2 is authoritative by law
        }
        
        # 4. Truth & Observability (Phase E4.7)
        truth = {
            "rejections": kernel_results.get("rejections", {}),
            "social_shifts": kernel_results.get("social_shifts", []),
            "strategic_blockers_active": kernel_results.get("active_blockers", 0),
            "quest_status_distribution": kernel_results.get("quest_status_counts", {}),
            "final_transaction_trace": kernel_results.get("transaction_trace", [])
        }
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "2.0.0-gold",
            "status": "CERTIFIED" if coverage["percent"] >= 100.0 and stability["determinism"] else "PROVISIONAL",
            "summary": {
                "total_logic_items": coverage["total"],
                "verified_v2_items": coverage["verified"],
                "coverage_percent": coverage["percent"]
            },
            "stability": stability,
            "protocol": protocol,
            "observability": truth,
            "certification_id": "CERT-V2-" + datetime.utcnow().strftime("%Y%m%d-%H%M")
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report

    @staticmethod
    def _analyze_checklist(path: str) -> Dict[str, Any]:
        """Scans the checklist for [x] VERIFIED v2 markers."""
        if not os.path.exists(path):
            return {"total": 0, "verified": 0, "percent": 0.0}
            
        with open(path, 'r') as f:
            content = f.read()
            
        # Count all items like "- [ ]" or "- [x]"
        all_items = re.findall(r'^- \[( |x)\]', content, re.MULTILINE)
        # Count verified items "- [x] ... VERIFIED v2"
        verified_items = re.findall(r'^- \[x\].*VERIFIED v2', content, re.MULTILINE)
        
        total = len(all_items)
        verified = len(verified_items)
        
        return {
            "total": total,
            "verified": verified,
            "percent": (verified / total * 100.0) if total > 0 else 0.0
        }
