from __future__ import annotations
import os
import json
import pytest
from unittest.mock import MagicMock, patch
from src.observability.reporting.retention import RetentionPolicy, RetentionManager
from src.observability.reporting.artifact_repository import RunManifest


def test_retention_policy_classification():
    policy = RetentionPolicy(normal_retention_days=7, protected_retention_days=30)
    
    # 1. Normal run
    m_normal = RunManifest(
        run_id="run-1",
        scenario_name="scenario",
        scenario_type="combat",
        seed=1,
        observability_mode="LIGHT",
        started_at="2026-05-20T00:00:00Z",
        ticks_requested=100,
        status="COMPLETED"
    )
    category, reason, days = policy.classify_run(m_normal, "some_dir")
    assert category == "recent_run"
    assert days == 7

    # 2. Failed run
    m_failed = RunManifest(
        run_id="run-2",
        scenario_name="scenario",
        scenario_type="combat",
        seed=1,
        observability_mode="LIGHT",
        started_at="2026-05-20T00:00:00Z",
        ticks_requested=100,
        status="FAILED"
    )
    category, reason, days = policy.classify_run(m_failed, "some_dir")
    assert category == "important_failed_run"
    assert days == 30


def test_retention_manager_generate_plan(tmp_path):
    # Setup standard mocked structure
    run_dir = os.path.join(str(tmp_path), "run-123")
    os.makedirs(run_dir)
    
    m_data = {
        "run_id": "run-123",
        "scenario_name": "scen",
        "scenario_type": "comb",
        "seed": 42,
        "observability_mode": "LIGHT",
        "started_at": "2020-05-20T00:00:00Z",  # extremely old, must expire
        "ticks_requested": 10,
        "ticks_completed": 10,
        "status": "COMPLETED",
        "artifact_schema_version": "observability_artifact_v1"
    }
    
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(m_data, f)

    with patch("src.observability.reporting.retention.RunArtifactRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.base_dir = str(tmp_path)
        
        # Mock read_manifest
        mock_manifest = RunManifest.model_validate(m_data)
        mock_repo.read_manifest.return_value = mock_manifest
        mock_repo_class.return_value = mock_repo
        
        manager = RetentionManager(repo=mock_repo)
        plan = manager.generate_cleanup_plan()
        
        assert plan["scanned_runs_count"] == 1
        assert len(plan["eligible_runs"]) == 1
        assert plan["eligible_runs"][0][0] == "run-123"
        assert plan["eligible_runs"][0][1]["expired"] is True


def test_retention_manager_execute_cleanup(tmp_path):
    run_dir = os.path.join(str(tmp_path), "run-old")
    os.makedirs(run_dir)
    
    m_data = {
        "run_id": "run-old",
        "scenario_name": "scen",
        "scenario_type": "comb",
        "seed": 42,
        "observability_mode": "LIGHT",
        "started_at": "2020-05-20T00:00:00Z",
        "ticks_requested": 10,
        "ticks_completed": 10,
        "status": "COMPLETED",
        "artifact_schema_version": "observability_artifact_v1"
    }
    
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(m_data, f)
        
    events_file = os.path.join(run_dir, "simulation_events.jsonl")
    with open(events_file, "w") as f:
        f.write("{}\n")

    with patch("src.observability.reporting.retention.RunArtifactRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.base_dir = str(tmp_path)
        mock_repo.read_manifest.return_value = RunManifest.model_validate(m_data)
        mock_repo_class.return_value = mock_repo
        
        manager = RetentionManager(repo=mock_repo)
        
        # Execute cleanup
        audit_entry = manager.execute_cleanup()
        assert audit_entry["purged_runs_count"] == 1
        assert audit_entry["deleted_files_count"] == 1
        
        # Telemetry should be deleted
        assert not os.path.exists(events_file)
        # Manifest should be updated with telemetry_pruned flag
        with open(os.path.join(run_dir, "run_manifest.json"), "r") as f:
            updated = json.load(f)
            assert updated.get("telemetry_pruned") is True
