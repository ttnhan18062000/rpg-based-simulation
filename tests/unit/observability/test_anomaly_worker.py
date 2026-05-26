from __future__ import annotations
import os
import json
import pytest
from unittest.mock import MagicMock, patch
from src.observability.anomaly.worker import ExternalAnomalyWorker, WorkerStatus
from src.observability.anomaly.pipeline import AnalysisResult


def test_worker_status_model():
    status = WorkerStatus(worker_id="test-worker", mode="artifact", status="PENDING")
    assert status.worker_id == "test-worker"
    assert status.status == "PENDING"
    assert status.processed_events == 0
    
    # Dump check
    data = status.model_dump()
    assert data["worker_id"] == "test-worker"


def test_worker_status_persistence(tmp_path):
    with patch("src.observability.anomaly.worker.RunArtifactRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.base_dir = str(tmp_path)
        mock_repo_class.return_value = mock_repo
        
        worker = ExternalAnomalyWorker(worker_id="w-123", mode="artifact")
        worker.update_status(status="RUNNING", current_run_id="run-456", processed_events=10)
        
        # Ensure status file is created
        status_file = os.path.join(str(tmp_path), "workers", "w-123.json")
        assert os.path.exists(status_file)
        
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["worker_id"] == "w-123"
            assert data["status"] == "RUNNING"
            assert data["current_run_id"] == "run-456"
            assert data["processed_events"] == 10


def test_worker_analyze_run_success(tmp_path):
    mock_result = AnalysisResult(
        run_id="run-1",
        status="COMPLETED",
        anomaly_count=2,
        health_score=90.0
    )
    
    with patch("src.observability.anomaly.worker.RunArtifactRepository") as mock_repo_class, \
         patch("src.observability.anomaly.worker.AnalysisPipeline") as mock_pipeline_class:
        
        mock_repo = MagicMock()
        mock_repo.base_dir = str(tmp_path)
        # Mock resolve_path to return a non-existent path so no events are counted by default
        mock_repo.resolve_path.return_value = os.path.join(str(tmp_path), "non_existent_events.jsonl")
        mock_repo_class.return_value = mock_repo
        
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        worker = ExternalAnomalyWorker(worker_id="w-1", mode="artifact")
        res = worker.analyze_run("run-1", allow_partial=True)
        
        assert res.status == "COMPLETED"
        assert res.anomaly_count == 2
        assert worker.status_record.status == "COMPLETED"
        assert worker.status_record.anomaly_count == 2
