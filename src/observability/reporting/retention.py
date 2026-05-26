from __future__ import annotations
import os
import json
import shutil
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple
from src.observability.reporting.artifact_repository import RunArtifactRepository

logger = logging.getLogger(__name__)


class RetentionPolicy:
    """
    Defines lifecycle rules and durations for various run outcome categories.
    Protects important/failed/critical runs longer than simple normal runs.
    """
    def __init__(
        self,
        normal_retention_days: int = 7,
        protected_retention_days: int = 30
    ) -> None:
        self.normal_retention_days = normal_retention_days
        self.protected_retention_days = protected_retention_days

    def classify_run(self, manifest: Any, base_dir: str) -> Tuple[str, str, int]:
        """
        Classifies a run's status and determines its retention duration.
        Returns: Tuple of (category, reason, retention_days)
        """
        run_id = manifest.run_id
        
        # Check if it is a source run for an active baseline
        # (For Phase 6, we keep all runs referenced as baselines or explicitly protected)
        is_baseline_source = getattr(manifest, "is_baseline_source", False)
        if is_baseline_source:
            return "baseline_source_run", "Referenced as baseline source", 365 * 10  # effectively permanent

        # Check for critical failures or failed gate status
        status = manifest.status.upper()
        
        # If anomalies.json exists, inspect it for critical anomalies
        anomalies_path = os.path.join(base_dir, run_id, "anomalies.json")
        has_critical_anomalies = False
        if os.path.exists(anomalies_path):
            try:
                with open(anomalies_path, "r", encoding="utf-8") as f:
                    anomalies = json.load(f)
                    if any(a.get("severity") == "CRITICAL" for a in anomalies):
                        has_critical_anomalies = True
            except Exception:
                pass

        if status == "FAILED" or has_critical_anomalies:
            return "important_failed_run", f"Failed outcome or critical anomalies", self.protected_retention_days

        return "recent_run", "Normal completed run", self.normal_retention_days


class RetentionManager:
    """
    Orchestrates the discovery, planning, and execution of observability data pruning.
    Acts defensively, executing deletions only upon explicit request.
    """
    def __init__(
        self,
        repo: Optional[RunArtifactRepository] = None,
        policy: Optional[RetentionPolicy] = None
    ) -> None:
        self.repo = repo or RunArtifactRepository()
        self.policy = policy or RetentionPolicy()

    def generate_cleanup_plan(self) -> Dict[str, Any]:
        """
        Scans all directories under the run repository and compares timestamps
        against retention policy thresholds. Generates a prunable catalog.
        """
        eligible_runs = []
        protected_runs = []
        now = datetime.now(timezone.utc)

        # List all run directories
        if not os.path.exists(self.repo.base_dir):
            return {
                "scanned_runs_count": 0,
                "eligible_runs": [],
                "protected_runs": []
            }

        scanned = 0
        for entry in os.listdir(self.repo.base_dir):
            run_dir = os.path.join(self.repo.base_dir, entry)
            if not os.path.isdir(run_dir) or entry == "workers" or entry == "exports":
                continue

            manifest_path = os.path.join(run_dir, "run_manifest.json")
            if not os.path.exists(manifest_path):
                # Corrupted run: classify as eligible for immediate safety pruning
                eligible_runs.append((
                    entry,
                    {
                        "reason": "Corrupted or missing run_manifest.json",
                        "files": ["* (full directory)"],
                        "expired": True
                    }
                ))
                continue

            try:
                scanned += 1
                manifest = self.repo.read_manifest(entry)
                category, reason, retention_days = self.policy.classify_run(manifest, self.repo.base_dir)

                # Parse creation timestamp
                timestamp_str = manifest.started_at
                # Support standard ISO format parsing
                try:
                    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except ValueError:
                    # Fallback to file creation time
                    dt = datetime.fromtimestamp(os.path.getctime(manifest_path), tz=timezone.utc)

                age_days = (now - dt).days
                is_expired = age_days >= retention_days

                details = {
                    "category": category,
                    "reason": f"{reason} (Age: {age_days}/{retention_days} days)",
                    "files": [
                        "simulation_events.jsonl",
                        "metric_windows.jsonl",
                        "hard_law_violations.jsonl"
                    ],
                    "expired": is_expired
                }

                if is_expired:
                    eligible_runs.append((entry, details))
                else:
                    protected_runs.append((entry, details))

            except Exception as e:
                logger.error(f"Error evaluating retention for run {entry}: {e}")
                eligible_runs.append((
                    entry,
                    {
                        "reason": f"Evaluation error: {e}",
                        "files": ["* (full directory)"],
                        "expired": True
                    }
                ))

        return {
            "scanned_runs_count": scanned,
            "eligible_runs": eligible_runs,
            "protected_runs": protected_runs
        }

    def execute_cleanup(self) -> Dict[str, Any]:
        """
        Executes actual filesystem purging for all expired runs.
        Writes a tracking logs manifest at data/runs/cleanup_log.json.
        """
        plan = self.generate_cleanup_plan()
        deleted_files_count = 0
        purged_runs_count = 0
        purged_runs_list = []

        for run_id, details in plan["eligible_runs"]:
            run_dir = os.path.join(self.repo.base_dir, run_id)
            if not os.path.exists(run_dir):
                continue

            try:
                # If fully corrupted, delete the entire directory
                if "full directory" in details["reason"] or details["reason"].startswith("Evaluation error"):
                    shutil.rmtree(run_dir)
                    purged_runs_count += 1
                    deleted_files_count += 1
                    purged_runs_list.append(run_id)
                else:
                    # Delete heavy raw logging telemetry but preserve the high-level report and manifest
                    for fname in details["files"]:
                        fpath = os.path.join(run_dir, fname)
                        if os.path.exists(fpath):
                            os.remove(fpath)
                            deleted_files_count += 1
                    
                    purged_runs_count += 1
                    purged_runs_list.append(run_id)

                    # Update manifest to record that raw telemetry has been pruned
                    manifest_path = os.path.join(run_dir, "run_manifest.json")
                    if os.path.exists(manifest_path):
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            mdata = json.load(f)
                        mdata["telemetry_pruned"] = True
                        mdata["pruned_at"] = datetime.now(timezone.utc).isoformat()
                        with open(manifest_path, "w", encoding="utf-8") as f:
                            json.dump(mdata, f, indent=2)

            except Exception as e:
                logger.error(f"Failed to execute cleanup for run {run_id}: {e}")

        # Record standard audit logs
        log_dir = self.repo.base_dir
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "cleanup_log.json")
        
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "purged_runs_count": purged_runs_count,
            "deleted_files_count": deleted_files_count,
            "purged_runs": purged_runs_list
        }

        try:
            audit_log = []
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    audit_log = json.load(f)
                    if not isinstance(audit_log, list):
                        audit_log = []
            audit_log.append(audit_entry)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(audit_log, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write retention cleanup log: {e}")

        return audit_entry
