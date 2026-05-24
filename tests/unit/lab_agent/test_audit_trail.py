import pytest
from pathlib import Path
from src.lab.session import LabSessionStore
from src.lab.audit import LabAuditTrail

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Sets up active session directories."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_audit_01")
    return tmp_path

def test_audit_log_is_append_only(mock_workspace: Path):
    """Verify that event logs are successfully appended line by line."""
    trail = LabAuditTrail(workspace_root=mock_workspace)
    
    trail.log_event("session_audit_01", "workflow_started", {"workflow": "TestWorkflow"})
    trail.log_event("session_audit_01", "workflow_completed", {"workflow": "TestWorkflow"})
    
    # Read physically and check append order
    session_dir = mock_workspace / "data" / "lab_sessions" / "session_audit_01"
    audit_file = session_dir / "audit_log.jsonl"
    assert audit_file.is_file()
    
    events = trail.read_log("session_audit_01")
    assert len(events) == 2
    assert events[0]["event_type"] == "workflow_started"
    assert events[0]["details"]["workflow"] == "TestWorkflow"
    
    assert events[1]["event_type"] == "workflow_completed"
    assert events[1]["details"]["workflow"] == "TestWorkflow"
