import json
import pytest
from pathlib import Path
from src.lab.session import LabSessionStore
from src.lab.audit import LabApprovalGate

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Sets up active session directories."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_gate_01")
    return tmp_path

def test_approval_record_is_written(mock_workspace: Path):
    """Verify that a valid approval record is serialized correctly."""
    gate = LabApprovalGate(workspace_root=mock_workspace)
    
    record = gate.record_approval(
        session_id="session_gate_01",
        stage="GENERATION",
        approved_artifacts=["generation/draft_specs/world.yaml"],
        approved_by="test_user",
        notes="All verified"
    )
    
    assert record["approval_id"] == "approval_0001"
    assert record["stage"] == "GENERATION"
    assert "generation/draft_specs/world.yaml" in record["approved_artifacts"]
    assert record["approved_by"] == "test_user"
    assert record["notes"] == "All verified"
    
    # Assert physical file exists and parses correctly
    session_dir = mock_workspace / "data" / "lab_sessions" / "session_gate_01"
    record_file = session_dir / "generation" / "approval_0001.json"
    assert record_file.is_file()
    
    with open(record_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["approval_id"] == "approval_0001"
    assert data["approved_by"] == "test_user"

def test_approval_unsafe_path_rejected(mock_workspace: Path):
    """Verify that approval records cannot reference unsafe paths."""
    gate = LabApprovalGate(workspace_root=mock_workspace)
    
    with pytest.raises(ValueError) as exc:
        gate.record_approval(
            session_id="session_gate_01",
            stage="GENERATION",
            approved_artifacts=["../../outside_sandbox.yaml"],
            approved_by="test_user"
        )
    assert "unsafe traversal" in str(exc.value)

def test_approval_gate_status_checking(mock_workspace: Path):
    """Verify check_approval matches manifest approval status correctly."""
    gate = LabApprovalGate(workspace_root=mock_workspace)
    
    assert not gate.check_approval("session_gate_01", "generation")
    
    gate.record_approval(
        session_id="session_gate_01",
        stage="GENERATION",
        approved_artifacts=["generation/draft_specs/world.yaml"],
        approved_by="test_user"
    )
    
    assert gate.check_approval("session_gate_01", "generation")
