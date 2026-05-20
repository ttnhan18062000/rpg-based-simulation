from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch
from src.observability.reporting.history_query import (
    HistoricalRunQueryService,
    HistoricalSweepQueryService,
    sanitize_id
)
from src.observability.reporting.artifact_repository import RunManifest
from src.observability.reporting.run_set_repository import SweepSummary


def test_sanitize_id_valid():
    assert sanitize_id("run-123_abc") == "run-123_abc"
    assert sanitize_id("sweep-5") == "sweep-5"


def test_sanitize_id_path_traversal_blocked():
    with pytest.raises(ValueError, match="Invalid identifier security warning"):
        sanitize_id("../../etc/passwd")

    with pytest.raises(ValueError, match="Invalid identifier security warning"):
        sanitize_id("runs/run-1")

    with pytest.raises(ValueError, match="Invalid identifier security warning"):
        sanitize_id("run-1; drop table runs;")


def test_historical_run_query_service():
    mock_run = RunManifest(
        run_id="run-1",
        scenario_name="scenario-1",
        scenario_type="combat",
        seed=1,
        observability_mode="LIGHT",
        started_at="2026-05-20T00:00:00Z",
        ticks_requested=100
    )
    
    mock_repo = MagicMock()
    mock_repo.read_manifest.return_value = mock_run
    mock_repo.list_runs.return_value = {"run-1": mock_run}
    
    service = HistoricalRunQueryService(repo=mock_repo)
    
    # Secure fetch
    manifest = service.get_run_manifest("run-1")
    assert manifest.run_id == "run-1"
    
    # Path traversal block in service
    with pytest.raises(ValueError):
        service.get_run_manifest("../run-1")
        
    # List historical runs
    runs = service.list_historical_runs(limit=10)
    assert len(runs) == 1
    assert runs[0].run_id == "run-1"


def test_historical_sweep_query_service():
    mock_sweep = SweepSummary(
        sweep_id="sweep-1",
        scenario_name="scenario-1",
        scenario_type="combat",
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        average_health_score=95.0,
        critical_run_count=0,
        warning_run_count=1
    )
    
    mock_repo = MagicMock()
    mock_repo.read_sweep_summary.return_value = mock_sweep
    mock_repo.list_sweeps.return_value = {"sweep-1": MagicMock(sweep_id="sweep-1")}
    
    service = HistoricalSweepQueryService(repo=mock_repo)
    
    summary = service.get_sweep_summary("sweep-1")
    assert summary.sweep_id == "sweep-1"
    
    with pytest.raises(ValueError):
        service.get_sweep_summary("../../sweep-1")
