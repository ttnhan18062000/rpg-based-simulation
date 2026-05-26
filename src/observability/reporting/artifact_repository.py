from __future__ import annotations
import os
import json
import shutil
from typing import Optional, Dict
from pydantic import BaseModel, Field

class RunManifest(BaseModel):
    run_id: str
    scenario_name: str
    scenario_type: str
    seed: int
    engine_version: str = "2.0.0"
    observability_version: str = "1.0.0"
    observability_mode: str
    started_at: str
    ended_at: Optional[str] = None
    ticks_requested: int
    ticks_completed: int = 0
    status: str = "CREATED"  # CREATED, RUNNING, COMPLETED, FAILED, ANALYZED
    artifact_schema_version: str = "observability_artifact_v1"
    failure_reason: Optional[str] = None

class RunArtifactRepository:
    def __init__(self, base_dir: str = "data/runs"):
        self.base_dir = os.path.abspath(base_dir)

    def create_run(self, run_id: str, manifest: RunManifest, overwrite: bool = False) -> None:
        """
        Creates the run directory and writes the initial manifest.
        Throws FileExistsError if the folder already exists and overwrite is False.
        """
        run_dir = os.path.join(self.base_dir, run_id)
        if os.path.exists(run_dir):
            if not overwrite:
                raise FileExistsError(f"Run directory already exists at: {run_dir}")
            else:
                shutil.rmtree(run_dir)
        
        os.makedirs(run_dir, exist_ok=True)
        manifest_path = self.resolve_path(run_id, "manifest")
        
        # Save manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

    def resolve_path(self, run_id: str, file_key: str) -> str:
        """
        Resolves the absolute path for standard run artifacts.
        """
        run_dir = os.path.join(self.base_dir, run_id)
        keys = {
            "manifest": "run_manifest.json",
            "events": "simulation_events.jsonl",
            "violations": "hard_law_violations.jsonl",
            "anomalies": "anomalies.json",
            "report_json": "run_report.json",
            "report_md": "run_report.md"
        }
        if file_key not in keys:
            raise KeyError(f"Unsupported file key: {file_key}")
        return os.path.join(run_dir, keys[file_key])

    def read_manifest(self, run_id: str) -> RunManifest:
        """
        Reads, parses, and validates the manifest from the run directory.
        Raises ValueError if the schema version is unsupported.
        """
        manifest_path = self.resolve_path(run_id, "manifest")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found for run_id: {run_id}")
            
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        manifest = RunManifest.model_validate(data)
        if manifest.artifact_schema_version != "observability_artifact_v1":
            raise ValueError(f"Unsupported artifact schema version: {manifest.artifact_schema_version}")
            
        return manifest

    def update_manifest(self, run_id: str, **kwargs) -> RunManifest:
        """
        Loads the manifest, applies changes, and saves it back atomically.
        """
        manifest = self.read_manifest(run_id)
        
        # Merge changes
        dumped = manifest.model_dump()
        for k, v in kwargs.items():
            if k in dumped:
                dumped[k] = v
                
        updated_manifest = RunManifest.model_validate(dumped)
        manifest_path = self.resolve_path(run_id, "manifest")
        
        # Write back
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(updated_manifest.model_dump_json(indent=2))
            
        return updated_manifest

    def list_runs(self) -> Dict[str, RunManifest]:
        """
        Scans base_dir and returns basic manifest summaries.
        """
        runs = {}
        if not os.path.exists(self.base_dir):
            return runs
            
        for run_id in os.listdir(self.base_dir):
            run_dir = os.path.join(self.base_dir, run_id)
            if os.path.isdir(run_dir):
                try:
                    manifest = self.read_manifest(run_id)
                    runs[run_id] = manifest
                except Exception:
                    # Ignore invalid or corrupted runs during listing
                    pass
        return runs
