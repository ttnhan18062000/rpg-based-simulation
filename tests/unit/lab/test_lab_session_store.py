import pytest
import json
from pathlib import Path
from src.lab.session import LabSessionManifest, LabSessionStore, LabSessionError

def test_create_session_success(tmp_path: Path):
    """Verify that a session is successfully initialized with directories and a manifest."""
    store = LabSessionStore(tmp_path)
    session_id = "session_0001"
    
    manifest = store.create_session(session_id)
    assert manifest.session_id == session_id
    assert manifest.status == "ACTIVE"
    assert manifest.current_stage == "GENERATION"
    assert manifest.approval_status["generation"] == "PENDING"
    
    session_dir = tmp_path / session_id
    assert session_dir.is_dir()
    assert (session_dir / "session_manifest.json").is_file()
    
    # Check that stage subfolders are created
    for sub_dir in store.STAGES.values():
        assert (session_dir / sub_dir).is_dir()
        
    # Check that nested subfolders are created
    assert (session_dir / "generation" / "draft_specs").is_dir()
    assert (session_dir / "generation" / "validation_reports").is_dir()
    assert (session_dir / "enhancement" / "proposed_patches").is_dir()
    assert (session_dir / "enhancement" / "next_experiment_drafts").is_dir()

def test_load_session_success(tmp_path: Path):
    """Verify loading a valid session manifest from disk."""
    store = LabSessionStore(tmp_path)
    session_id = "session_0002"
    
    # Create first
    created_manifest = store.create_session(session_id)
    
    # Load and compare
    loaded_manifest = store.load_session(session_id)
    assert loaded_manifest.session_id == session_id
    assert loaded_manifest.created_at == created_manifest.created_at
    assert loaded_manifest.status == "ACTIVE"

def test_save_session_success(tmp_path: Path):
    """Verify that updates to session manifests are saved and updated_at is refreshed."""
    store = LabSessionStore(tmp_path)
    session_id = "session_0003"
    
    manifest = store.create_session(session_id)
    original_updated_at = manifest.updated_at
    
    # Modify manifest fields
    manifest.status = "COMPLETED"
    manifest.current_stage = "EXECUTION_SUPPORT"
    manifest.approval_status["generation"] = "APPROVED"
    manifest.linked_lab_runs.append("combat_stress_run_01")
    
    import time
    time.sleep(0.01)  # Ensure updated_at timestamp moves
    store.save_session(manifest)
    
    # Reload and assert
    loaded = store.load_session(session_id)
    assert loaded.status == "COMPLETED"
    assert loaded.current_stage == "EXECUTION_SUPPORT"
    assert loaded.approval_status["generation"] == "APPROVED"
    assert loaded.linked_lab_runs == ["combat_stress_run_01"]
    assert loaded.updated_at != original_updated_at

def test_list_sessions(tmp_path: Path):
    """Verify that only directories containing a valid session manifest are listed."""
    store = LabSessionStore(tmp_path)
    
    assert store.list_sessions() == []
    
    # Create valid sessions
    store.create_session("session_abc")
    store.create_session("session_123")
    
    # Create arbitrary folder without manifest
    (tmp_path / "random_folder").mkdir()
    
    assert store.list_sessions() == ["session_123", "session_abc"]

def test_duplicate_session_fails(tmp_path: Path):
    """Verify creating a duplicate session ID raises an error."""
    store = LabSessionStore(tmp_path)
    session_id = "session_dup"
    
    store.create_session(session_id)
    with pytest.raises(LabSessionError) as excinfo:
        store.create_session(session_id)
    assert "already exists" in str(excinfo.value)

def test_missing_session_fails(tmp_path: Path):
    """Verify loading a non-existent session ID raises FileNotFoundError."""
    store = LabSessionStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.load_session("non_existent_session")

def test_invalid_session_id_fails(tmp_path: Path):
    """Verify that invalid/empty session IDs are strictly rejected."""
    store = LabSessionStore(tmp_path)
    
    invalid_ids = ["", "session/with/slashes", "session_id_with_$", "session space", None]
    for bad_id in invalid_ids:
        # None will raise a TypeError or LabSessionError depending on re.match
        with pytest.raises((LabSessionError, TypeError)):
            store.create_session(bad_id)

def test_path_traversal_blocked(tmp_path: Path):
    """Verify that path traversal in session IDs is strictly blocked."""
    store = LabSessionStore(tmp_path)
    
    traversal_ids = ["../escaped", "sub/../../escaped", "/absolute/escape", "invalid/path"]
    for bad_id in traversal_ids:
        with pytest.raises((PermissionError, LabSessionError)):
            store.resolve_session_dir(bad_id)

def test_manifest_corruption_fails(tmp_path: Path):
    """Verify that corrupted manifest JSON files raise a LabSessionError on load."""
    store = LabSessionStore(tmp_path)
    session_id = "session_corrupted"
    
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    
    # Write garbage content to manifest path
    manifest_path = session_dir / "session_manifest.json"
    with open(manifest_path, "w") as f:
        f.write("corrupted string { [ json")
        
    with pytest.raises(LabSessionError) as excinfo:
        store.load_session(session_id)
    assert "Failed to parse session manifest" in str(excinfo.value)

def test_get_stage_dir(tmp_path: Path):
    """Verify resolving stage directories safely, raising errors for unknown stages."""
    store = LabSessionStore(tmp_path)
    session_id = "session_stage_test"
    store.create_session(session_id)
    
    # Valid stages (case-insensitive)
    gen_path = store.get_stage_dir(session_id, "GENERATION")
    assert gen_path.name == "generation"
    assert gen_path.is_dir()
    
    exec_path = store.get_stage_dir(session_id, "execution_support")
    assert exec_path.name == "execution_support"
    assert exec_path.is_dir()
    
    # Invalid stage
    with pytest.raises(LabSessionError) as excinfo:
        store.get_stage_dir(session_id, "INVALID_STAGE")
    assert "Unknown or invalid workflow stage" in str(excinfo.value)
