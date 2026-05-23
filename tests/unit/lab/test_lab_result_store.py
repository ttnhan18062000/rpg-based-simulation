import pytest
import json
import os
from pathlib import Path
from src.lab.schema import LabRunManifest
from src.lab.store import LabResultStore, LabResultStoreError

@pytest.fixture
def sample_manifest():
    return LabRunManifest(
        lab_run_id="labrun_2026_test",
        world_id="test_world",
        scenario_id="test_scenario",
        experiment_id="test_exp",
        status="COMPLETED",
        started_at="2026-05-23T12:00:00Z",
        ended_at="2026-05-23T12:05:00Z",
        run_count=5,
        completed_run_count=5,
        failed_run_count=0,
        artifact_root="",
        storage_usage_mb=0.123,
        schema_versions={"world": "worldspec.v1"}
    )

def test_list_lab_runs(tmp_path: Path, sample_manifest: LabRunManifest):
    """Verify that lab result store successfully lists directories containing a manifest."""
    store = LabResultStore(tmp_path)
    
    # Empty dir
    assert store.list_lab_runs() == []
    
    # Create valid run directory structure
    run_dir = tmp_path / "labrun_2026_test"
    run_dir.mkdir()
    
    # No manifest yet
    assert store.list_lab_runs() == []
    
    # Write manifest
    with open(run_dir / "lab_run_manifest.json", "w") as f:
        json.dump(sample_manifest.model_dump(), f)
        
    # Valid layout
    assert store.list_lab_runs() == ["labrun_2026_test"]
    
    # Another directory without manifest should be skipped
    (tmp_path / "another_folder").mkdir()
    assert store.list_lab_runs() == ["labrun_2026_test"]

def test_path_traversal_blocked(tmp_path: Path):
    """Verify that path traversal in lab run IDs is strictly blocked."""
    store = LabResultStore(tmp_path)
    
    traversal_ids = ["../escaped", "sub/../../escaped", "/absolute/escape", "invalid/path", ""]
    for run_id in traversal_ids:
        with pytest.raises((PermissionError, LabResultStoreError)):
            store.load_lab_run_manifest(run_id)

def test_load_manifest_and_summary(tmp_path: Path, sample_manifest: LabRunManifest):
    """Verify that manifests and lab summaries are loaded correctly, handling missing files cleanly."""
    store = LabResultStore(tmp_path)
    run_id = "labrun_2026_test"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    
    # Missing manifest should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        store.load_lab_run_manifest(run_id)
        
    # Write manifest
    with open(run_dir / "lab_run_manifest.json", "w") as f:
        json.dump(sample_manifest.model_dump(), f)
        
    loaded_manifest = store.load_lab_run_manifest(run_id)
    assert loaded_manifest.lab_run_id == run_id
    assert loaded_manifest.status == "COMPLETED"
    
    # Missing summary should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        store.load_lab_summary(run_id)
        
    # Write summary
    summary_data = {"average_health_score": 85.5, "critical_count_total": 0}
    with open(run_dir / "lab_summary.json", "w") as f:
        json.dump(summary_data, f)
        
    loaded_summary = store.load_lab_summary(run_id)
    assert loaded_summary["average_health_score"] == 85.5
    assert loaded_summary["critical_count_total"] == 0

def test_load_run_report(tmp_path: Path):
    """Verify that specific child run reports are loaded correctly under isolated directories."""
    store = LabResultStore(tmp_path)
    run_id = "labrun_2026_test"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    
    # Create runs structure
    runs_dir = run_dir / "runs" / "run_seed_42"
    runs_dir.mkdir(parents=True)
    
    # Missing report
    with pytest.raises(FileNotFoundError):
        store.load_run_report(run_id, "run_seed_42")
        
    # Bad child run ID pattern
    with pytest.raises(LabResultStoreError):
        store.load_run_report(run_id, "../escaped_seed")
        
    # Write child report
    report_data = {"health_score": 90.0, "anomalies": []}
    with open(runs_dir / "run_report.json", "w") as f:
        json.dump(report_data, f)
        
    loaded = store.load_run_report(run_id, "run_seed_42")
    assert loaded["health_score"] == 90.0

def test_load_validation_and_compile_reports(tmp_path: Path):
    """Verify loading world compile reports and scenario/experiment validation reports."""
    store = LabResultStore(tmp_path)
    run_id = "labrun_2026_test"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    
    # Subdirectories
    world_dir = run_dir / "world"
    scenario_dir = run_dir / "scenario"
    experiment_dir = run_dir / "experiment"
    
    world_dir.mkdir()
    scenario_dir.mkdir()
    experiment_dir.mkdir()
    
    # Missing compile report
    with pytest.raises(FileNotFoundError):
        store.load_compile_report(run_id)
        
    # Missing validation reports (raises FileNotFoundError when both are missing)
    with pytest.raises(FileNotFoundError):
        store.load_validation_reports(run_id)
        
    # Write compile report
    compile_data = {"world_id": "test_world", "state_hash": "abc123hash"}
    with open(world_dir / "world_compile_report.json", "w") as f:
        json.dump(compile_data, f)
        
    loaded_compile = store.load_compile_report(run_id)
    assert loaded_compile["state_hash"] == "abc123hash"
    
    # Write validation reports
    scen_val = {"scenario_id": "test_scenario", "valid": True}
    exp_val = {"experiment_id": "test_exp", "valid": True}
    
    with open(scenario_dir / "scenario_validation_report.json", "w") as f:
        json.dump(scen_val, f)
    with open(experiment_dir / "experiment_validation_report.json", "w") as f:
        json.dump(exp_val, f)
        
    val_reports = store.load_validation_reports(run_id)
    assert val_reports["scenario"]["scenario_id"] == "test_scenario"
    assert val_reports["experiment"]["experiment_id"] == "test_exp"

def test_rebuild_index_and_get_index(tmp_path: Path, sample_manifest: LabRunManifest):
    """Verify that rebuilding and fetching central lab run indexes outputs precise keys."""
    store = LabResultStore(tmp_path)
    run_id = "labrun_2026_test"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    
    # Write manifest and summary
    with open(run_dir / "lab_run_manifest.json", "w") as f:
        json.dump(sample_manifest.model_dump(), f)
    with open(run_dir / "lab_summary.json", "w") as f:
        json.dump({"average_health_score": 95.0}, f)
        
    # Get index (should rebuild automatically)
    index = store.get_index()
    assert run_id in index
    
    record = index[run_id]
    assert record["lab_run_id"] == run_id
    assert record["world_id"] == "test_world"
    assert record["scenario_id"] == "test_scenario"
    assert record["experiment_id"] == "test_exp"
    assert record["status"] == "COMPLETED"
    assert record["run_count"] == 5
    assert record["storage_usage_mb"] == 0.123
    assert record["summary_path"] is not None
    assert "lab_summary.json" in record["summary_path"]
