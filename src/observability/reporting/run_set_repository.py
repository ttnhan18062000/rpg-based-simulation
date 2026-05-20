# Compliance IDs: OBS-041, OBS-042, OBS-043
from __future__ import annotations

import os
import json
import shutil
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from src.observability.sweeper import RunSetManifest


class RunIndexRecord(BaseModel):
    """Metadata representing indexing information for a single run inside a sweep."""
    sweep_id: str
    run_id: str
    seed: int
    scenario_name: str
    scenario_type: str
    status: str
    ticks_completed: int
    health_score: float
    critical_count: int
    warning_count: int
    hard_law_violation_count: int
    artifact_path: str


class SweepSummary(BaseModel):
    """Aggregated stats and metrics summarizing outcomes across an entire sweep set."""
    sweep_id: str
    scenario_name: str
    scenario_type: str
    total_runs: int
    completed_runs: int
    failed_runs: int
    average_health_score: float
    critical_run_count: int
    warning_run_count: int
    worst_run_id: Optional[str] = None
    best_run_id: Optional[str] = None
    most_common_anomaly_rule_ids: Dict[str, int] = Field(default_factory=dict)


class RunSetArtifactRepository:
    """Repository managing reading, writing, and listing of multi-run sweep artifacts."""

    def __init__(self, base_dir: str = "data/run_sets"):
        self.base_dir = os.path.abspath(base_dir)

    def resolve_path(self, sweep_id: str, file_key: str) -> str:
        """Resolves the absolute path for sweep-level artifacts."""
        sweep_dir = os.path.join(self.base_dir, sweep_id)
        keys = {
            "manifest": "run_set_manifest.json",
            "index": "run_index.jsonl",
            "summary": "sweep_summary.json"
        }
        if file_key not in keys:
            raise KeyError(f"Unsupported file key: {file_key}")
        return os.path.join(sweep_dir, keys[file_key])

    def create_sweep(self, sweep_id: str, manifest: RunSetManifest, overwrite: bool = False) -> None:
        """Creates the sweep directory and writes the initial run set manifest."""
        sweep_dir = os.path.join(self.base_dir, sweep_id)
        if os.path.exists(sweep_dir):
            if not overwrite:
                raise FileExistsError(f"Sweep directory already exists at: {sweep_dir}")
            else:
                shutil.rmtree(sweep_dir)

        os.makedirs(sweep_dir, exist_ok=True)
        manifest_path = self.resolve_path(sweep_id, "manifest")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

    def write_run_index(self, sweep_id: str, records: List[RunIndexRecord]) -> None:
        """Writes line-separated JSON records to run_index.jsonl."""
        index_path = self.resolve_path(sweep_id, "index")
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(record.model_dump_json() + "\n")

    def read_run_index(self, sweep_id: str) -> List[RunIndexRecord]:
        """Reads and parses run_index.jsonl from a sweep folder."""
        index_path = self.resolve_path(sweep_id, "index")
        if not os.path.exists(index_path):
            return []

        records = []
        with open(index_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(RunIndexRecord.model_validate(json.loads(line)))
        return records

    def write_sweep_summary(self, sweep_id: str, summary: SweepSummary) -> None:
        """Writes the aggregate sweep summary to sweep_summary.json."""
        summary_path = self.resolve_path(sweep_id, "summary")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))

    def read_sweep_summary(self, sweep_id: str) -> SweepSummary:
        """Reads and parses sweep_summary.json from a sweep folder."""
        summary_path = self.resolve_path(sweep_id, "summary")
        if not os.path.exists(summary_path):
            raise FileNotFoundError(f"Sweep summary not found for sweep_id: {sweep_id}")

        with open(summary_path, "r", encoding="utf-8") as f:
            return SweepSummary.model_validate(json.load(f))

    def list_sweeps(self) -> Dict[str, RunSetManifest]:
        """Scans base_dir and returns basic sweep manifest summaries."""
        sweeps = {}
        if not os.path.exists(self.base_dir):
            return sweeps

        for sweep_id in os.listdir(self.base_dir):
            sweep_dir = os.path.join(self.base_dir, sweep_id)
            if os.path.isdir(sweep_dir):
                manifest_path = os.path.join(sweep_dir, "run_set_manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            sweeps[sweep_id] = RunSetManifest.model_validate(json.load(f))
                    except Exception:
                        pass
        return sweeps
