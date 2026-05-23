# Compliance IDs: OBS-PH9-M51
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataCompletenessAuditor:
    """Audits experiment directories for schema alignment, corrupted payloads, and missing run telemetry."""
    
    @classmethod
    def audit_completeness(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        manifest_file = os.path.join(experiment_dir, "experiment_manifest.json")
        if not os.path.exists(manifest_file):
            raise FileNotFoundError(f"Experiment manifest not found at: {manifest_file}")
            
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        run_ids = manifest.get("run_ids", [])
        
        runs_classification = {}
        missing_runs = []
        corrupted_runs = []
        schema_mismatches = []
        valid_runs = []
        
        for run_id in run_ids:
            run_dir = os.path.join(experiment_dir, "runs", run_id)
            
            if not os.path.exists(run_dir):
                runs_classification[run_id] = "INVALID_MISSING_ARTIFACTS"
                missing_runs.append(run_id)
                continue
                
            manifest_path = os.path.join(run_dir, "run_manifest.json")
            if not os.path.exists(manifest_path):
                runs_classification[run_id] = "INVALID_MISSING_ARTIFACTS"
                missing_runs.append(run_id)
                continue
                
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
            except Exception:
                runs_classification[run_id] = "INVALID_CORRUPTED_ARTIFACT"
                corrupted_runs.append(run_id)
                continue
                
            # Verify schema compatibility
            schema_version = manifest_data.get("schema_version", "unknown")
            if schema_version != "run_manifest_v1" and schema_version != "unknown":
                runs_classification[run_id] = "INVALID_SCHEMA_MISMATCH"
                schema_mismatches.append(run_id)
                continue
                
            # Check completeness of metrics and events
            metrics_path = os.path.join(run_dir, "metric_windows.jsonl")
            events_path = os.path.join(run_dir, "simulation_events.jsonl")
            
            has_metrics = os.path.exists(metrics_path) and os.path.getsize(metrics_path) > 0
            has_events = os.path.exists(events_path) and os.path.getsize(events_path) > 0
            
            if not has_metrics or not has_events:
                runs_classification[run_id] = "VALID_PARTIAL"
            else:
                runs_classification[run_id] = "VALID_FOR_MINING"
                
            valid_runs.append(run_id)
            
        total_runs = len(run_ids)
        quality_score = (len(valid_runs) / total_runs * 100.0) if total_runs > 0 else 100.0
        
        report = {
            "experiment_id": experiment_id,
            "total_runs": total_runs,
            "valid_run_count": len(valid_runs),
            "missing_run_count": len(missing_runs),
            "corrupted_run_count": len(corrupted_runs),
            "schema_mismatch_count": len(schema_mismatches),
            "quality_score": quality_score,
            "runs_classification": runs_classification,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save audit report to workspace
        report_path = os.path.join(experiment_dir, "data_quality_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        # Also write markdown version
        cls._write_markdown_report(report, os.path.join(experiment_dir, "data_quality_report.md"))
        
        return report
        
    @classmethod
    def _write_markdown_report(cls, report: Dict[str, Any], path: str) -> None:
        md = f"""# Data Quality Audit Report

**Experiment ID**: `{report["experiment_id"]}`
**Audit Timestamp**: `{report["created_at"]}`
**Overall Telemetry Quality Score**: `{report["quality_score"]:.2f}%`

---

## Metric Breakdown
*   **Total Expected Runs**: {report["total_runs"]}
*   **Valid Runs**: {report["valid_run_count"]}
*   **Missing Telemetry Folders**: {report["missing_run_count"]}
*   **Corrupted Run Manifests**: {report["corrupted_run_count"]}
*   **Schema version mismatches**: {report["schema_mismatch_count"]}

---

## Validity Classification Map
"""
        for r_id, cls_label in list(report["runs_classification"].items())[:20]:
            md += f"*   `{r_id}`: **{cls_label}**\n"
        if len(report["runs_classification"]) > 20:
            md += f"*   *... and {len(report['runs_classification']) - 20} more run classifications.*"
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)


class DeterminismAuditor:
    """Audits repeat runs of identical seeds to identify state drift and trace structural divergence coordinates."""
    
    @classmethod
    def audit_determinism(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        manifest_file = os.path.join(experiment_dir, "experiment_manifest.json")
        if not os.path.exists(manifest_file):
            raise FileNotFoundError(f"Experiment manifest not found at: {manifest_file}")
            
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        run_ids = manifest.get("run_ids", [])
        
        # Group runs by seed
        runs_by_seed = {}
        matrix_file = os.path.join(experiment_dir, "run_matrix.jsonl")
        if os.path.exists(matrix_file):
            try:
                with open(matrix_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        spec = json.loads(line)
                        seed = spec["seed"]
                        r_id = spec["run_id"]
                        if r_id in run_ids:
                            runs_by_seed.setdefault(seed, []).append(r_id)
            except Exception as e:
                logger.warning(f"Error loading seeds from matrix: {e}")
                
        determinism_failures = []
        divergence_reports = []
        
        evaluated_groups_with_hashes = 0
        total_hashes_found = 0
        
        for seed, group_runs in runs_by_seed.items():
            if len(group_runs) < 2:
                continue
                
            # Fetch final state hashes
            hashes = {}
            for r_id in group_runs:
                manifest_path = os.path.join(experiment_dir, "runs", r_id, "run_manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            m_data = json.load(f)
                            h = m_data.get("final_state_hash") or m_data.get("state_hash")
                            if h:
                                hashes[r_id] = h
                    except Exception:
                        pass
            
            if len(hashes) >= 2:
                evaluated_groups_with_hashes += 1
            total_hashes_found += len(hashes)
                        
            # Detect divergence
            unique_hashes = set(hashes.values())
            if len(unique_hashes) > 1:
                # Confirmed nondeterminism! Tracing earliest divergence tick
                divergence_tick = cls._find_earliest_divergence(experiment_dir, group_runs)
                
                determinism_failures.append({
                    "seed": seed,
                    "runs_evaluated": list(hashes.keys()),
                    "unique_hashes": list(unique_hashes),
                    "earliest_divergence_tick": divergence_tick
                })
                
        verdict = "DETERMINISTIC"
        if evaluated_groups_with_hashes == 0 or total_hashes_found == 0:
            verdict = "INSUFFICIENT_DATA"
        elif determinism_failures:
            verdict = "CONFIRMED_NONDETERMINISM"
            
        report = {
            "experiment_id": experiment_id,
            "verdict": verdict,
            "seed_count_evaluated": len(runs_by_seed),
            "determinism_failures": determinism_failures,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save JSON
        with open(os.path.join(experiment_dir, "determinism_audit.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        # Write Markdown
        cls._write_markdown_report(report, os.path.join(experiment_dir, "determinism_audit.md"))
        
        return report
        
    @classmethod
    def _find_earliest_divergence(cls, experiment_dir: str, runs: List[str]) -> Optional[int]:
        """Compares event logs tick-by-tick across runs to pin the exact tick of logical divergence."""
        events_by_run = {}
        for r_id in runs:
            events_file = os.path.join(experiment_dir, "runs", r_id, "simulation_events.jsonl")
            if os.path.exists(events_file):
                events = []
                try:
                    with open(events_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                events.append(json.loads(line))
                    events_by_run[r_id] = events
                except Exception:
                    pass
                    
        if len(events_by_run) < 2:
            return None
            
        # Match events tick by tick
        min_len = min(len(evs) for evs in events_by_run.values())
        run_ids_list = list(events_by_run.keys())
        
        for idx in range(min_len):
            # Compare the event signatures at this index
            signatures = {}
            for r_id in run_ids_list:
                e = events_by_run[r_id][idx]
                # Compare critical keys (tick, event_type, entity_id, resources)
                sig = (
                    e.get("tick", 0),
                    e.get("event_type", "none"),
                    e.get("entity_id"),
                    str(e.get("payload", {}))
                )
                signatures[r_id] = sig
                
            if len(set(signatures.values())) > 1:
                # First mismatched event signature! Returns the tick coordinate
                first_mismatched_run = run_ids_list[0]
                return events_by_run[first_mismatched_run][idx].get("tick", idx)
                
        return None
        
    @classmethod
    def _write_markdown_report(cls, report: Dict[str, Any], path: str) -> None:
        md = f"""# Determinism Audit Report

**Experiment ID**: `{report["experiment_id"]}`
**Audit Verdict**: **{report["verdict"]}**
**Seeds Evaluated**: {report["seed_count_evaluated"]}
**Timestamp**: `{report["created_at"]}`

---

"""
        if report["verdict"] == "DETERMINISTIC":
            md += "### ✅ Determinism Confirmed\nAll duplicate seed simulation runs generated identical state hashes. The engine is verified 100% deterministic.\n"
        else:
            md += "### 🚨 Nondeterminism Detected\n"
            for f in report["determinism_failures"]:
                md += f"""#### Seed {f["seed"]}
*   **Runs Evaluated**: {", ".join([f"`{r}`" for r in f["runs_evaluated"]])}
*   **Earliest Divergence Tick**: **Tick {f["earliest_divergence_tick"]}**
*   **State Hashes**:
"""
                for h in f["unique_hashes"]:
                    md += f"    *   `{h}`\n"
                    
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
