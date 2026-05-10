import os
import json
import pytest
from pathlib import Path
from src.engine.replay_sink import ReplaySink

def test_integrity_atomic_manifest_write(tmp_path):
    """
    M7 Law: Manifest updates MUST be atomic (write-then-rename).
    """
    sink = ReplaySink(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    temp_path = tmp_path / "manifest.json.tmp"
    
    # Initial write
    initial_data = {"status": "START"}
    sink.write_manifest(initial_data)
    
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        assert json.load(f)["status"] == "START"
        
    # Second write
    updated_data = {"status": "SUCCESS"}
    sink.write_manifest(updated_data)
    
    # Verify it updated
    with open(manifest_path, "r") as f:
        assert json.load(f)["status"] == "SUCCESS"
        
    # Verify temp file is GONE (cleanup)
    assert not temp_path.exists()

def test_manifest_corrupt_prevention(tmp_path, monkeypatch):
    """
    Verify that if the rename fails, the old manifest is preserved.
    """
    sink = ReplaySink(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    
    initial_data = {"status": "AUTH_TRUTH"}
    sink.write_manifest(initial_data)
    
    # Mock os.replace to fail
    def mock_replace(src, dst):
        raise OSError("Disk full or permission denied")
        
    monkeypatch.setattr(os, "replace", mock_replace)
    
    # Try to write new data
    new_data = {"status": "CORRUPTED_INTENT"}
    success = sink.write_manifest(new_data)
    
    assert success is False
    # Authoritative Law: The old manifest must remain intact
    with open(manifest_path, "r") as f:
        assert json.load(f)["status"] == "AUTH_TRUTH"
