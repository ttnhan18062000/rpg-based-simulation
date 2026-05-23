import json
import re
from pathlib import Path
from datetime import datetime, timezone
from src.lab.schema import LabRunManifest, InvalidLabRunManifestError

class LabResultStoreError(Exception):
    """Base exception for LabResultStore operations."""
    pass

class LabResultStore:
    """
    File-based store for managing, loading, listing, and indexing completed 
    Scenario Lab executions and their associated diagnostic scorecards and reports.
    """
    def __init__(self, lab_runs_dir: str | Path):
        self.lab_runs_dir = Path(lab_runs_dir).resolve()
        self.index_path = self.lab_runs_dir / "lab_index.json"

    def _validate_lab_run_id(self, lab_run_id: str) -> None:
        """Enforces safe identifier formats to prevent directory traversal or malformed input."""
        if not lab_run_id:
            raise LabResultStoreError("lab_run_id cannot be empty")
        if not re.match(r"^[a-zA-Z0-9_-]+$", lab_run_id):
            raise LabResultStoreError(
                f"Invalid lab_run_id: '{lab_run_id}'. Must be alphanumeric plus hyphens/underscores."
            )

    def _resolve_run_dir(self, lab_run_id: str) -> Path:
        """Safely resolves run directory, preventing any path traversal escapes."""
        self._validate_lab_run_id(lab_run_id)
        resolved = (self.lab_runs_dir / lab_run_id).resolve()
        try:
            if not resolved.is_relative_to(self.lab_runs_dir) or resolved == self.lab_runs_dir:
                raise PermissionError(
                    f"Path traversal detected or invalid access outside base directory: '{lab_run_id}'"
                )
        except ValueError as e:
            raise PermissionError(
                f"Path traversal attempt blocked: '{lab_run_id}' is outside '{self.lab_runs_dir}': {e}"
            ) from e
        return resolved

    def list_lab_runs(self) -> list[str]:
        """Scans the lab runs base directory and lists all valid lab run IDs."""
        if not self.lab_runs_dir.is_dir():
            return []
        
        run_ids = []
        for child in self.lab_runs_dir.iterdir():
            if child.is_dir():
                manifest_path = child / "lab_run_manifest.json"
                if manifest_path.is_file():
                    try:
                        self._validate_lab_run_id(child.name)
                        run_ids.append(child.name)
                    except LabResultStoreError:
                        continue
        return sorted(run_ids)

    def load_lab_run_manifest(self, lab_run_id: str) -> LabRunManifest:
        """Loads the LabRunManifest Pydantic model for the specified lab_run_id."""
        run_dir = self._resolve_run_dir(lab_run_id)
        manifest_path = run_dir / "lab_run_manifest.json"
        
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Lab run directory not found: '{lab_run_id}'")
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Lab run manifest not found: '{manifest_path}'")
            
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return LabRunManifest(**data)
        except Exception as e:
            raise LabResultStoreError(f"Failed to load or parse manifest: {e}") from e

    def load_lab_summary(self, lab_run_id: str) -> dict:
        """Loads the aggregated lab_summary.json data for the specified lab_run_id."""
        run_dir = self._resolve_run_dir(lab_run_id)
        summary_path = run_dir / "lab_summary.json"
        
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Lab run directory not found: '{lab_run_id}'")
        if not summary_path.is_file():
            raise FileNotFoundError(f"Lab summary file not found: '{summary_path}'")
            
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise LabResultStoreError(f"Failed to load or parse lab summary: {e}") from e

    def load_run_report(self, lab_run_id: str, run_id: str) -> dict:
        """Loads a specific child run report (run_report.json) within the sweep directory."""
        run_dir = self._resolve_run_dir(lab_run_id)
        # Avoid path traversal inside the run_id parameter
        if not re.match(r"^[a-zA-Z0-9_-]+$", run_id):
            raise LabResultStoreError(f"Invalid child run ID: '{run_id}'")
            
        report_path = run_dir / "runs" / run_id / "run_report.json"
        if not report_path.is_file():
            raise FileNotFoundError(f"Child run report not found: '{report_path}'")
            
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise LabResultStoreError(f"Failed to load child run report: {e}") from e

    def load_validation_reports(self, lab_run_id: str) -> dict:
        """Loads both scenario and experiment validation reports if available."""
        run_dir = self._resolve_run_dir(lab_run_id)
        scenario_report_path = run_dir / "scenario" / "scenario_validation_report.json"
        experiment_report_path = run_dir / "experiment" / "experiment_validation_report.json"
        
        result = {}
        if scenario_report_path.is_file():
            try:
                with open(scenario_report_path, "r", encoding="utf-8") as f:
                    result["scenario"] = json.load(f)
            except Exception as e:
                raise LabResultStoreError(f"Failed to parse scenario validation report: {e}") from e
        else:
            result["scenario"] = None

        if experiment_report_path.is_file():
            try:
                with open(experiment_report_path, "r", encoding="utf-8") as f:
                    result["experiment"] = json.load(f)
            except Exception as e:
                raise LabResultStoreError(f"Failed to parse experiment validation report: {e}") from e
        else:
            result["experiment"] = None

        if result["scenario"] is None and result["experiment"] is None:
            raise FileNotFoundError(f"No validation reports found for lab run '{lab_run_id}'")
            
        return result

    def load_compile_report(self, lab_run_id: str) -> dict:
        """Loads the world compilation report (world_compile_report.json) if available."""
        run_dir = self._resolve_run_dir(lab_run_id)
        compile_report_path = run_dir / "world" / "world_compile_report.json"
        
        if not compile_report_path.is_file():
            raise FileNotFoundError(f"Compile report not found: '{compile_report_path}'")
            
        try:
            with open(compile_report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise LabResultStoreError(f"Failed to load compile report: {e}") from e

    def rebuild_index(self) -> None:
        """
        Scans all directories, parses manifests, and compiles the central lab_index.json
        with specific metadata matching the index record structure.
        """
        self.lab_runs_dir.mkdir(parents=True, exist_ok=True)
        run_ids = self.list_lab_runs()
        index_data = {}
        
        for run_id in run_ids:
            try:
                manifest = self.load_lab_run_manifest(run_id)
                summary_file = self._resolve_run_dir(run_id) / "lab_summary.json"
                summary_path_str = str(summary_file) if summary_file.is_file() else None
                
                index_data[run_id] = {
                    "lab_run_id": run_id,
                    "world_id": manifest.world_id,
                    "scenario_id": manifest.scenario_id,
                    "experiment_id": manifest.experiment_id,
                    "status": manifest.status,
                    "started_at": manifest.started_at,
                    "ended_at": manifest.ended_at,
                    "run_count": manifest.run_count,
                    "storage_usage_mb": manifest.storage_usage_mb,
                    "summary_path": summary_path_str
                }
            except Exception:
                # Log or handle corrupted directories gracefully
                continue

        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            raise LabResultStoreError(f"Failed to write central lab index: {e}") from e

    def get_index(self) -> dict:
        """Loads and returns the central lab index dictionary, rebuilding if missing."""
        if not self.index_path.is_file():
            self.rebuild_index()
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self.rebuild_index()
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
