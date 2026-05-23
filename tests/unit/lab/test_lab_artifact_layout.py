# Compliance IDs: LABRUN-TEST-003, LABRUN-TEST-004
import pytest
import json
from pathlib import Path
from src.lab.schema import LabRunManifest, InvalidLabRunManifestError
from src.lab.repository import LabRunRepository, LabRunRepositoryError

@pytest.fixture
def base_manifest():
    return LabRunManifest(
        lab_run_id="labrun_2026_001",
        world_id="world_01",
        scenario_id="scenario_01",
        experiment_id="exp_01",
        status="CREATED",
        started_at="2026-05-23T12:00:00Z",
        artifact_root="",
        schema_versions={"world": "worldspec.v1"}
    )


def test_create_and_load_lab_run(tmp_path: Path, base_manifest: LabRunManifest):
    """Verify that a lab run layout is initialized and manifest is compiled correctly."""
    repo = LabRunRepository(tmp_path)
    
    # Initialize lab run directory
    run_dir = repo.create_lab_run(base_manifest)
    assert run_dir.exists()
    assert (run_dir / "lab_run_manifest.json").is_file()
    
    # Assert all target subdirectories exist
    for sub in ["world", "scenario", "experiment", "runs", "analysis", "logs"]:
        assert (run_dir / sub).is_dir()
        
    # Load and assert equality
    loaded = repo.load_lab_run("labrun_2026_001")
    assert loaded.lab_run_id == "labrun_2026_001"
    assert loaded.status == "CREATED"
    assert loaded.artifact_root == str(run_dir)


def test_path_traversal_detection(tmp_path: Path, base_manifest: LabRunManifest):
    """Verify that invalid or relative traversal IDs are blocked immediately."""
    repo = LabRunRepository(tmp_path)
    
    # Traversal IDs
    traversal_ids = ["../escaped", "sub/../../escaped", "/absolute/escape"]
    for run_id in traversal_ids:
        with pytest.raises(LabRunRepositoryError) as exc_info:
            repo._resolve_run_dir(run_id)
        assert "traversal" in str(exc_info.value).lower() or "invalid lab_run_id" in str(exc_info.value).lower()


def test_accidental_overwrite_protection(tmp_path: Path, base_manifest: LabRunManifest):
    """Verify that attempting to create an existing lab run raises FileExistsError."""
    repo = LabRunRepository(tmp_path)
    
    # Create it once
    repo.create_lab_run(base_manifest)
    
    # Try creating it again
    with pytest.raises(FileExistsError):
        repo.create_lab_run(base_manifest)


def test_save_and_rebuild_index(tmp_path: Path, base_manifest: LabRunManifest):
    """Verify that modifications compile down to the central aggregation manifest."""
    repo = LabRunRepository(tmp_path)
    repo.create_lab_run(base_manifest)
    
    # Load, modify, and save
    manifest = repo.load_lab_run("labrun_2026_001")
    manifest.status = "RUNNING"
    manifest.run_count = 10
    manifest.completed_run_count = 4
    repo.save_lab_run(manifest)
    
    # Re-load from repo
    reloaded = repo.load_lab_run("labrun_2026_001")
    assert reloaded.status == "RUNNING"
    assert reloaded.run_count == 10
    assert reloaded.completed_run_count == 4
    
    # Check index aggregated values
    index = repo.get_index()
    assert "labrun_2026_001" in index
    record = index["labrun_2026_001"]
    assert record["status"] == "RUNNING"
    assert record["run_count"] == 10
    assert record["completed_run_count"] == 4
