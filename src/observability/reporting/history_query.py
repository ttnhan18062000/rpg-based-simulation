from __future__ import annotations
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
