import json
import logging
from pathlib import Path
from typing import Optional, Any

from src.lab.results import RegisterSimulationResultResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.request import WorkflowRequest
from src.lab.store import LabResultStore
from src.lab.schema import LabRunManifest
from src.lab.audit import LabAuditTrail
from src.lab.workflows._path_safety import safe_path_resolution

logger = logging.getLogger(__name__)

class RegisterSimulationResultWorkflow:
    """
    M98 Workflow: After manual sweep run completes, registers, catalogs,
    and indexes completed scorecards into session-scoped files.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()

        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        lab_runs_dir = self.workspace_root / "data" / "lab_runs"
        self.result_store = LabResultStore(lab_runs_dir)

    def run(self, session_id: str, request: WorkflowRequest) -> RegisterSimulationResultResult:
        logger.info(f"Running RegisterSimulationResultWorkflow for session '{session_id}'")

        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)
        manifest.current_stage = "REGISTRATION"
        self.session_store.save_session(manifest)
        trail = LabAuditTrail(self.workspace_root)
        trail.log_event(session_id, "workflow_started", {"workflow": "RegisterSimulationResult"})

        reg_dir = self.session_store.get_stage_dir(session_id, "REGISTRATION")
        reg_dir.mkdir(parents=True, exist_ok=True)

        # 2. Resolve run path safely
        if request.mode == "specific":
            lab_run_path_str = request.specific_inputs.get("lab_run_path")
            if not lab_run_path_str:
                raise ValueError("lab_run_path must be supplied in specific mode.")
        else:
            # Generic mode: load from expected_output_paths.json
            support_dir = self.session_store.get_stage_dir(session_id, "EXECUTION_SUPPORT")
            expected_paths_file = support_dir / "expected_output_paths.json"
            if not expected_paths_file.is_file():
                err_msg = "Expected output paths file not found. Prepare the execution support first."
                self._write_integrity_report(reg_dir, "MISSING", err_msg)
                return {"status": "BLOCKED", "reason": err_msg}
            try:
                with open(expected_paths_file, "r", encoding="utf-8") as f:
                    expected_paths = json.load(f)
                lab_run_path_str = expected_paths.get("output_directory")
            except Exception as e:
                err_msg = f"Failed to load expected output paths: {e}"
                self._write_integrity_report(reg_dir, "CORRUPTED", err_msg)
                return {"status": "BLOCKED", "reason": err_msg}

        # Safe resolution preventing traversal escapes
        resolved_run_path = safe_path_resolution(self.workspace_root, lab_run_path_str)

        # 3. Analyze Completeness / Classifications
        classification = "COMPLETE"
        reason = ""
        run_manifest = None

        if not resolved_run_path.is_dir():
            classification = "MISSING"
            reason = f"Simulation output directory does not exist at '{lab_run_path_str}'"
        else:
            manifest_file = resolved_run_path / "lab_run_manifest.json"
            if not manifest_file.is_file():
                classification = "CORRUPTED"
                reason = "Simulation manifest file 'lab_run_manifest.json' is missing in output directory."
            else:
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest_data = json.load(f)
                    run_manifest = LabRunManifest(**manifest_data)
                except Exception as e:
                    classification = "CORRUPTED"
                    reason = f"Malformed run manifest file: {e}"

                if classification == "COMPLETE" and run_manifest:
                    if run_manifest.status == "FAILED":
                        classification = "FAILED"
                        reason = "Simulation sweep completed but manifest status is explicitly FAILED."
                    else:
                        # Check partial run completeness
                        # Ensure we count individual run reports under runs/
                        runs_dir = resolved_run_path / "runs"
                        actual_run_count = 0
                        if runs_dir.is_dir():
                            for child in runs_dir.iterdir():
                                if child.is_dir() and (child / "run_report.json").is_file():
                                    actual_run_count += 1

                        expected_run_count = run_manifest.run_count
                        if actual_run_count < expected_run_count:
                            classification = "PARTIAL"
                            reason = f"Run count mismatch. Expected {expected_run_count} runs, but found only {actual_run_count} completed child run folders."

        # If blocked (MISSING or CORRUPTED)
        if classification in ("MISSING", "CORRUPTED"):
            self._write_integrity_report(reg_dir, classification, reason)
            return {"status": "BLOCKED", "reason": reason}

        # 4. Link run path inside session manifest
        run_id_val = run_manifest.lab_run_id if run_manifest else resolved_run_path.name
        manifest.linked_lab_runs = list(set(manifest.linked_lab_runs + [run_id_val]))
        self.session_store.save_session(manifest)

        # Write actual_lab_run_path.txt
        (reg_dir / "actual_lab_run_path.txt").write_text(str(resolved_run_path), encoding="utf-8")

        # 5. Build Artifact Index containing sizes and paths
        artifact_list = []
        for file_path in resolved_run_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(resolved_run_path)
                file_size = file_path.stat().st_size
                artifact_list.append({
                    "relative_path": str(rel_path),
                    "size_bytes": file_size
                })

        with open(reg_dir / "artifact_index.json", "w", encoding="utf-8") as f:
            json.dump(artifact_list, f, indent=2)

        # 6. Generate json and markdown reports
        compact_summary = {
            "lab_run_id": run_id_val,
            "classification": classification,
            "reason": reason or "Integrity checks passed completely.",
            "world_id": run_manifest.world_id if run_manifest else "unknown",
            "scenario_id": run_manifest.scenario_id if run_manifest else "unknown",
            "experiment_id": run_manifest.experiment_id if run_manifest else "unknown",
            "storage_usage_mb": run_manifest.storage_usage_mb if run_manifest else 0.0,
            "run_count": run_manifest.run_count if run_manifest else 0,
            "completed_run_count": run_manifest.completed_run_count if run_manifest else 0,
            "failed_run_count": run_manifest.failed_run_count if run_manifest else 0
        }
        with open(reg_dir / "result_integrity_report.json", "w", encoding="utf-8") as f:
            json.dump(compact_summary, f, indent=2)

        # MD Report
        report_md = self._format_integrity_report_md(
            session_id=session_id,
            classification=classification,
            reason=reason,
            summary=compact_summary,
            artifacts=artifact_list
        )
        (reg_dir / "result_integrity_report.md").write_text(report_md, encoding="utf-8")

        # Also register via result store rebuild index to update central indexes
        try:
            self.result_store.rebuild_index()
        except Exception as e:
            logger.warning(f"Rebuild index failed during registration: {e}")

        trail.log_event(session_id, "workflow_completed", {"workflow": "RegisterSimulationResult"})
        return {
            "status": "READY",
            "classification": classification,
            "lab_run_id": run_id_val,
            "report_path": str(reg_dir / "result_integrity_report.md")
        }

    def _write_integrity_report(self, reg_dir: Path, classification: str, reason: str) -> None:
        """Writes failure/blocked integrity report JSON and MD files."""
        blocked_json = {
            "classification": classification,
            "status": "BLOCKED",
            "reason": reason
        }
        with open(reg_dir / "result_integrity_report.json", "w", encoding="utf-8") as f:
            json.dump(blocked_json, f, indent=2)

        blocked_md = f"""# Result Integrity Audit Blocked

Your manual simulation run result registration has been **blocked** due to structural check errors:

## Audit Status: `{classification}`
> [!CAUTION]
> **Reason**: {reason}

## Recommended Actions
1. Verify that your manual execution script successfully finished writing all log data.
2. Confirm the directory includes a valid, parseable `lab_run_manifest.json` descriptor file.
"""
        (reg_dir / "result_integrity_report.md").write_text(blocked_md, encoding="utf-8")

    def _format_integrity_report_md(self, session_id: str, classification: str, reason: str, summary: dict[str, Any], artifacts: list[dict[str, Any]]) -> str:
        """Generates premium registration audit summary report."""
        status_symbol = "✅ COMPLETE"
        alert_symbol = "[!NOTE]\nAll structural integrity and seed coverage validation checks passed flawlessly."
        if classification == "PARTIAL":
            status_symbol = "⚠️ PARTIAL"
            alert_symbol = "[!WARNING]\nSome child run subdirectories or diagnostic reports are missing. Proceed with caution."
        elif classification == "FAILED":
            status_symbol = "❌ FAILED"
            alert_symbol = "[!CAUTION]\nSimulation sweep completed with explicit internal execution failures reported."

        artifact_rows = []
        for art in sorted(artifacts, key=lambda x: x["relative_path"])[:20]:
            size_kb = art["size_bytes"] / 1024.0
            artifact_rows.append(f"| `{art['relative_path']}` | {size_kb:.2f} KB |")

        limit_note = "\n*(Showing first 20 artifacts. Refer to artifact_index.json for the full list)*" if len(artifacts) > 20 else ""

        return f"""# Simulation Sweep Result Integrity Audit

This report contains the compliance scorecard for your manual execution registration audit.

## Staging Registry
- **Lab Session**: `{session_id}`
- **Sweep Run ID**: `{summary["lab_run_id"]}`
- **Audit Outcome**: `{status_symbol}`

> {alert_symbol}
{f"> **Details**: {reason}" if reason else ""}

---

## Specification Map
| Specification | Linked Alphanumeric ID |
| :--- | :--- |
| **World ID** | `{summary["world_id"]}` |
| **Scenario ID** | `{summary["scenario_id"]}` |
| **Experiment ID** | `{summary["experiment_id"]}` |

## Run Statistics
- **Expected Sweep Runs**: `{summary["run_count"]}`
- **Completed Child Runs**: `{summary["completed_run_count"]}`
- **Failed Child Runs**: `{summary["failed_run_count"]}`
- **Calculated Disk Footprint**: `{summary["storage_usage_mb"]:.3f} MB`

---

## Artifact Inventory Index
| Relative Artifact Path | Size |
| :--- | :--- |
{chr(10).join(artifact_rows)}{limit_note}

---

## Next Steps
To run post-analysis, metamorphic balance reviews, and print diagnostic reports, trigger the Investigation workflow:
```bash
rpg-workflow-investigate --session-id "{session_id}"
```
"""
