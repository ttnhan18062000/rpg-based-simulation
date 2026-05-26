# Compliance IDs: LABRUN-TEST-001, LABRUN-TEST-002
import pytest
from pydantic import ValidationError
from src.lab.schema import LabRunManifest, InvalidLabRunManifestError

def test_valid_manifest_loads():
    """Verify that a compliant manifest loads and parses correctly."""
    data = {
        "lab_run_id": "labrun_2026_001",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "CREATED",
        "started_at": "2026-05-23T12:00:00Z",
        "ended_at": None,
        "run_count": 5,
        "completed_run_count": 0,
        "failed_run_count": 0,
        "artifact_root": "/data/lab_runs/labrun_2026_001",
        "schema_versions": {"world": "worldspec.v1", "scenario": "scenariospec.v1"},
        "budgets": {"max_runtime_minutes": 60},
        "storage_usage_mb": 0.0
    }
    
    manifest = LabRunManifest(**data)
    assert manifest.lab_run_id == "labrun_2026_001"
    assert manifest.status == "CREATED"
    assert manifest.run_count == 5
    assert manifest.completed_run_count == 0
    assert manifest.storage_usage_mb == 0.0
    assert manifest.schema_versions["world"] == "worldspec.v1"


def test_invalid_status_rejected():
    """Verify that unsupported status values raise ValidationError."""
    data = {
        "lab_run_id": "labrun_01",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "INVALID_STATE_MODE",
        "started_at": "2026-05-23T12:00:00Z",
        "artifact_root": "/path"
    }
    with pytest.raises(ValidationError) as exc_info:
        LabRunManifest(**data)
    assert "status" in str(exc_info.value)


def test_negative_counts_rejected():
    """Verify that negative run counts or disk footprints are blocked."""
    data = {
        "lab_run_id": "labrun_01",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "CREATED",
        "started_at": "2026-05-23T12:00:00Z",
        "run_count": -5,
        "artifact_root": "/path"
    }
    with pytest.raises(ValidationError) as exc_info:
        LabRunManifest(**data)
    assert "run_count" in str(exc_info.value)


def test_invalid_id_format_rejected():
    """Verify that identifiers with spaces or special traversal characters are rejected."""
    data = {
        "lab_run_id": "labrun/../escape",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "CREATED",
        "started_at": "2026-05-23T12:00:00Z",
        "artifact_root": "/path"
    }
    with pytest.raises(ValidationError) as exc_info:
        LabRunManifest(**data)
    assert "lab_run_id" in str(exc_info.value)
