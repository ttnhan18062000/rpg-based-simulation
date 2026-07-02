from __future__ import annotations
import os
import shutil
import pytest
from datetime import datetime, timezone
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest

@pytest.fixture
def base_dir(tmp_path):
    path = tmp_path / "test_runs"
    yield str(path)
    if path.exists():
        shutil.rmtree(path)

def test_run_manifest_serialization():
    manifest = RunManifest(
        run_id="run_test",
        scenario_name="test_scenario",
        scenario_type="combat_sandbox",
        seed=42,
        observability_mode="LIGHT",
        started_at="2026-05-19T00:00:00Z",
        ticks_requested=100
    )
    dumped = manifest.model_dump()
    assert dumped["run_id"] == "run_test"
    assert dumped["engine_version"] == "2.0.0"
    assert dumped["artifact_schema_version"] == "observability_artifact_v1"

def test_repository_creation_and_overwrite(base_dir):
    repo = RunArtifactRepository(base_dir=base_dir)
    manifest = RunManifest(
        run_id="run_1",
        scenario_name="scenario_1",
        scenario_type="mixed_sandbox",
        seed=1,
        observability_mode="LIGHT",
        started_at="2026-05-19T00:00:00Z",
        ticks_requested=50
    )

    repo.create_run("run_1", manifest)
    
    run_dir = os.path.join(base_dir, "run_1")
    assert os.path.exists(run_dir)
    assert os.path.exists(repo.resolve_path("run_1", "manifest"))
    
    # Overwrite guard: should raise FileExistsError
    with pytest.raises(FileExistsError):
        repo.create_run("run_1", manifest)
        
    # Overwrite explicitly enabled
    repo.create_run("run_1", manifest, overwrite=True)
    assert os.path.exists(run_dir)

def test_manifest_lifecycle_updates(base_dir):
    repo = RunArtifactRepository(base_dir=base_dir)
    manifest = RunManifest(
        run_id="run_2",
        scenario_name="scenario_2",
        scenario_type="mixed_sandbox",
        seed=2,
        observability_mode="LIGHT",
        started_at="2026-05-19T00:00:00Z",
        ticks_requested=50
    )

    repo.create_run("run_2", manifest)
    
    # Read manifest
    read_manifest = repo.read_manifest("run_2")
    assert read_manifest.status == "CREATED"
    
    # Update manifest
    updated = repo.update_manifest(
        "run_2",
        status="RUNNING",
        ticks_completed=10,
        ended_at="2026-05-19T01:00:00Z"
    )
    assert updated.status == "RUNNING"
    assert updated.ticks_completed == 10
    assert updated.ended_at == "2026-05-19T01:00:00Z"
    
    # Verify persistence
    read_again = repo.read_manifest("run_2")
    assert read_again.status == "RUNNING"
    assert read_again.ticks_completed == 10

def test_schema_version_validation(base_dir):
    repo = RunArtifactRepository(base_dir=base_dir)
    manifest = RunManifest(
        run_id="run_3",
        scenario_name="scenario_3",
        scenario_type="mixed_sandbox",
        seed=3,
        observability_mode="LIGHT",
        started_at="2026-05-19T00:00:00Z",
        ticks_requested=50
    )
    repo.create_run("run_3", manifest)
    
    # Forcing invalid schema version into manifest file
    manifest_path = repo.resolve_path("run_3", "manifest")
    with open(manifest_path, "r", encoding="utf-8") as f:
        import json
        data = json.load(f)
    data["artifact_schema_version"] = "observability_artifact_v99"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    # Read should raise ValueError
    with pytest.raises(ValueError, match="Unsupported artifact schema version"):
        repo.read_manifest("run_3")

def test_run_manifest_world_id_default():
    """RunManifest without world_id must serialize world_id as 'unknown'."""
    manifest = RunManifest(
        run_id="run_wid_default",
        scenario_name="cli_default",
        scenario_type="mixed_sandbox",
        seed=0,
        observability_mode="LIGHT",
        started_at="2026-06-27T00:00:00Z",
        ticks_requested=10
    )
    dumped = manifest.model_dump()
    assert "world_id" in dumped
    assert dumped["world_id"] == "unknown"


def test_run_manifest_world_id_explicit():
    """RunManifest with world_id='dungeon_crawl' must round-trip that value."""
    manifest = RunManifest(
        run_id="run_wid_explicit",
        scenario_name="cli_default",
        scenario_type="mixed_sandbox",
        seed=0,
        observability_mode="LIGHT",
        started_at="2026-06-27T00:00:00Z",
        ticks_requested=10,
        world_id="dungeon_crawl"
    )
    dumped = manifest.model_dump()
    assert dumped["world_id"] == "dungeon_crawl"


def test_manifest_world_id_persists_via_repo(base_dir):
    """world_id must survive a write/read round-trip through RunArtifactRepository."""
    repo = RunArtifactRepository(base_dir=base_dir)
    manifest = RunManifest(
        run_id="run_wid_repo",
        scenario_name="cli_default",
        scenario_type="mixed_sandbox",
        seed=0,
        observability_mode="LIGHT",
        started_at="2026-06-27T00:00:00Z",
        ticks_requested=10,
        world_id="urban_political"
    )
    repo.create_run("run_wid_repo", manifest)
    read_back = repo.read_manifest("run_wid_repo")
    assert read_back.world_id == "urban_political"


def test_list_runs(base_dir):
    repo = RunArtifactRepository(base_dir=base_dir)
    manifest_1 = RunManifest(
        run_id="run_list_1", scenario_name="s", scenario_type="t", seed=1,
        observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z", ticks_requested=10
    )
    manifest_2 = RunManifest(
        run_id="run_list_2", scenario_name="s", scenario_type="t", seed=2,
        observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z", ticks_requested=10
    )
    repo.create_run("run_list_1", manifest_1)
    repo.create_run("run_list_2", manifest_2)
    
    runs = repo.list_runs()
    assert "run_list_1" in runs
    assert "run_list_2" in runs
    assert len(runs) == 2
