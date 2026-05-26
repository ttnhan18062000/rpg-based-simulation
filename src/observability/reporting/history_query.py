from __future__ import annotations
import os
import json
import re
from typing import List, Dict, Any, Optional
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.run_set_repository import RunSetArtifactRepository, SweepSummary

# Alphanumeric check regex to protect against path traversal attacks (e.g. '../../etc/passwd')
ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


def sanitize_id(identifier: str) -> str:
    """
    Validates that the identifier contains only alphanumeric characters, underscores, or hyphens.
    Raises ValueError to block potential path traversal attempts.
    """
    if not identifier or not ID_PATTERN.match(identifier):
        raise ValueError(f"Invalid identifier security warning: '{identifier}'")
    return identifier


class HistoricalRunQueryService:
    """Provides secure, read-only queries of historical single-simulation run artifacts."""
    def __init__(self, repo: Optional[RunArtifactRepository] = None) -> None:
        self.repo = repo or RunArtifactRepository()

    def get_run_manifest(self, run_id: str) -> RunManifest:
        run_id = sanitize_id(run_id)
        return self.repo.read_manifest(run_id)

    def get_entity_snapshots(
        self, run_id: str, entity_id: str, page: int = 1, page_size: int = 20, full_graph: bool = False
    ) -> Dict[str, Any]:
        run_id = sanitize_id(run_id)
        entity_id = sanitize_id(entity_id)
        
        # Verify run manifest exists
        self.get_run_manifest(run_id)
        
        run_dir = os.path.join(self.repo.base_dir, run_id)
        snapshots_path = os.path.join(run_dir, "cognition_graph_snapshots.jsonl")
        
        if not os.path.exists(snapshots_path):
            raise FileNotFoundError(f"Cognition snapshots file not found for run: {run_id}")
            
        matching = []
        try:
            entity_id_int = int(entity_id)
        except ValueError:
            entity_id_int = None

        with open(snapshots_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if str(data.get("entity_id")) == entity_id or (entity_id_int is not None and data.get("entity_id") == entity_id_int):
                        if not full_graph:
                            data_stripped = data.copy()
                            data_stripped.pop("nodes", None)
                            data_stripped.pop("edges", None)
                            data_stripped["nodes_count"] = len(data.get("nodes", []))
                            data_stripped["edges_count"] = len(data.get("edges", []))
                            matching.append(data_stripped)
                        else:
                            matching.append(data)

        total = len(matching)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = matching[start:end]
        
        return {
            "snapshots": paginated,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_entity_diffs(self, run_id: str, entity_id: str) -> List[Dict[str, Any]]:
        run_id = sanitize_id(run_id)
        entity_id = sanitize_id(entity_id)
        
        # Verify run manifest exists
        self.get_run_manifest(run_id)
        
        run_dir = os.path.join(self.repo.base_dir, run_id)
        diffs_path = os.path.join(run_dir, "cognition_graph_diffs.jsonl")
        
        if not os.path.exists(diffs_path):
            raise FileNotFoundError(f"Cognition diffs file not found for run: {run_id}")
            
        matching = []
        try:
            entity_id_int = int(entity_id)
        except ValueError:
            entity_id_int = None

        with open(diffs_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if str(data.get("entity_id")) == entity_id or (entity_id_int is not None and data.get("entity_id") == entity_id_int):
                        matching.append(data)
                        
        return matching

    def get_entity_features(self, run_id: str, entity_id: str) -> List[Dict[str, Any]]:
        run_id = sanitize_id(run_id)
        entity_id = sanitize_id(entity_id)
        
        # Verify run manifest exists
        self.get_run_manifest(run_id)
        
        run_dir = os.path.join(self.repo.base_dir, run_id)
        features_path = os.path.join(run_dir, "cognition_features.jsonl")
        
        if not os.path.exists(features_path):
            raise FileNotFoundError(f"Cognition features file not found for run: {run_id}")
            
        matching = []
        try:
            entity_id_int = int(entity_id)
        except ValueError:
            entity_id_int = None

        with open(features_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if str(data.get("entity_id")) == entity_id or (entity_id_int is not None and data.get("entity_id") == entity_id_int):
                        matching.append(data)
                        
        return matching

    def get_run_patterns(self, run_id: str) -> List[Dict[str, Any]]:
        run_id = sanitize_id(run_id)
        
        # Verify run manifest exists
        self.get_run_manifest(run_id)
        
        run_dir = os.path.join(self.repo.base_dir, run_id)
        patterns_path = os.path.join(run_dir, "cognition_patterns.json")
        
        if not os.path.exists(patterns_path):
            raise FileNotFoundError(f"Cognition patterns file not found for run: {run_id}")
            
        with open(patterns_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_historical_runs(self, limit: int = 50, offset: int = 0) -> List[RunManifest]:
        """Lists historical runs with sorted pagination support."""
        runs_dict = self.repo.list_runs()
        sorted_runs = sorted(
            runs_dict.values(),
            key=lambda x: x.started_at,
            reverse=True
        )
        return sorted_runs[offset : offset + limit]


class HistoricalSweepQueryService:
    """Provides secure, read-only queries of historical multi-run scenario sweeps."""
    def __init__(self, repo: Optional[RunSetArtifactRepository] = None) -> None:
        self.repo = repo or RunSetArtifactRepository()

    def get_sweep_summary(self, sweep_id: str) -> SweepSummary:
        sweep_id = sanitize_id(sweep_id)
        return self.repo.read_sweep_summary(sweep_id)

    def list_historical_sweeps(self, limit: int = 50, offset: int = 0) -> List[Any]:
        """Lists historical sweeps with sorted pagination support."""
        sweeps_dict = self.repo.list_sweeps()
        sorted_sweeps = sorted(
            sweeps_dict.values(),
            key=lambda x: x.sweep_id,
            reverse=True
        )
        return sorted_sweeps[offset : offset + limit]
