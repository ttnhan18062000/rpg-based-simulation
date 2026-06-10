import json
import pytest
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import RegisterSimulationResultWorkflow

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Sets up base workspaces, lab run and lab session directories."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    (tmp_path / "data" / "lab_runs").mkdir(parents=True)
    
    # Initialize active session
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_reg_01")
    return tmp_path

def test_registration_complete_success(mock_workspace: Path):
    """Verify that a successful complete run registers and links successfully."""
    run_dir = mock_workspace / "data" / "lab_runs" / "manual_run_01"
    run_dir.mkdir(parents=True)
    
    # Write mock completed run manifest
    manifest_data = {
        "lab_run_id": "manual_run_01",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "COMPLETED",
        "started_at": "2026-05-23T12:00:00Z",
        "ended_at": "2026-05-23T13:00:00Z",
        "run_count": 2,
        "completed_run_count": 2,
        "failed_run_count": 0,
        "artifact_root": str(run_dir),
        "schema_versions": {"world": "worldspec.v1", "scenario": "scenariospec.v1"},
        "budgets": {"max_runtime_minutes": 60},
        "storage_usage_mb": 1.2
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    # Write child runs
    for i in range(2):
        child_dir = run_dir / "runs" / f"run_{i}"
        child_dir.mkdir(parents=True)
        with open(child_dir / "run_report.json", "w", encoding="utf-8") as f:
            json.dump({"run_id": f"run_{i}", "success": True}, f)
            
    # Run specific mode workflow
    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "data/lab_runs/manual_run_01"}
    )
    
    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_reg_01", request)
    
    assert res["status"] == "READY"
    assert res["classification"] == "COMPLETE"
    assert res["lab_run_id"] == "manual_run_01"
    
    # Verify registration folder files
    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_reg_01" / "registration"
    assert (reg_dir / "result_integrity_report.md").is_file()
    assert (reg_dir / "result_integrity_report.json").is_file()
    assert (reg_dir / "artifact_index.json").is_file()
    assert (reg_dir / "actual_lab_run_path.txt").is_file()
    
    # Verify linked_lab_runs in session manifest
    session_store = LabSessionStore(mock_workspace / "data" / "lab_sessions")
    session_manifest = session_store.load_session("session_reg_01")
    assert "manual_run_01" in session_manifest.linked_lab_runs

def test_registration_partial_run(mock_workspace: Path):
    """Verify that a run with missing child folders is marked PARTIAL."""
    run_dir = mock_workspace / "data" / "lab_runs" / "manual_run_02"
    run_dir.mkdir(parents=True)
    
    manifest_data = {
        "lab_run_id": "manual_run_02",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "COMPLETED",
        "started_at": "2026-05-23T12:00:00Z",
        "ended_at": None,
        "run_count": 3,
        "completed_run_count": 1,
        "failed_run_count": 0,
        "artifact_root": str(run_dir),
        "schema_versions": {},
        "budgets": {},
        "storage_usage_mb": 0.5
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    # Write only 1 child run instead of 3
    child_dir = run_dir / "runs" / "run_0"
    child_dir.mkdir(parents=True)
    with open(child_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump({"run_id": "run_0"}, f)
        
    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "data/lab_runs/manual_run_02"}
    )
    
    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_reg_01", request)
    
    assert res["status"] == "READY"
    assert res["classification"] == "PARTIAL"

def test_registration_failed_run(mock_workspace: Path):
    """Verify that a run whose manifest status is FAILED is marked FAILED."""
    run_dir = mock_workspace / "data" / "lab_runs" / "manual_run_03"
    run_dir.mkdir(parents=True)
    
    manifest_data = {
        "lab_run_id": "manual_run_03",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "FAILED",
        "started_at": "2026-05-23T12:00:00Z",
        "ended_at": "2026-05-23T12:30:00Z",
        "run_count": 2,
        "completed_run_count": 0,
        "failed_run_count": 2,
        "artifact_root": str(run_dir),
        "schema_versions": {},
        "budgets": {},
        "storage_usage_mb": 0.1
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "data/lab_runs/manual_run_03"}
    )
    
    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_reg_01", request)
    
    assert res["status"] == "READY"
    assert res["classification"] == "FAILED"

def test_registration_corrupted_manifest(mock_workspace: Path):
    """Verify that a corrupted or malformed run manifest blocks registration."""
    run_dir = mock_workspace / "data" / "lab_runs" / "manual_run_04"
    run_dir.mkdir(parents=True)
    
    # Write garbage content to manifest
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        f.write("{garbage_json...")
        
    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "data/lab_runs/manual_run_04"}
    )
    
    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_reg_01", request)
    
    assert res["status"] == "BLOCKED"
    assert res["reason"] is not None
    
    # Verify audit reports exist and describe the block
    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_reg_01" / "registration"
    with open(reg_dir / "result_integrity_report.json", "r", encoding="utf-8") as f:
        audit_rep = json.load(f)
        assert audit_rep["classification"] == "CORRUPTED"
        assert audit_rep["status"] == "BLOCKED"

def test_registration_generic_mode(mock_workspace: Path):
    """Verify that generic mode resolves the path via expected_output_paths.json."""
    support_dir = mock_workspace / "data" / "lab_sessions" / "session_reg_01" / "execution_support"
    support_dir.mkdir(parents=True, exist_ok=True)
    
    # Write mock expected output path descriptor
    expected_data = {
        "experiment_yaml": "data/lab_sessions/session_reg_01/generation/draft_specs/experiment.yaml",
        "output_directory": "data/lab_runs/auto_sweep_run_99",
        "command_script": "data/lab_sessions/session_reg_01/execution_support/execution_command.sh"
    }
    with open(support_dir / "expected_output_paths.json", "w", encoding="utf-8") as f:
        json.dump(expected_data, f)
        
    # Write actual run directory matching output_directory
    run_dir = mock_workspace / "data" / "lab_runs" / "auto_sweep_run_99"
    run_dir.mkdir(parents=True)
    
    manifest_data = {
        "lab_run_id": "auto_sweep_run_99",
        "world_id": "world_01",
        "scenario_id": "scenario_01",
        "experiment_id": "experiment_01",
        "status": "COMPLETED",
        "started_at": "2026-05-23T12:00:00Z",
        "run_count": 0,
        "artifact_root": str(run_dir),
        "schema_versions": {},
        "budgets": {},
        "storage_usage_mb": 0.1
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="generic",
        user_goal="register latest sweep"
    )
    
    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_reg_01", request)
    
    assert res["status"] == "READY"
    assert res["classification"] == "COMPLETE"
    assert res["lab_run_id"] == "auto_sweep_run_99"

def test_registration_traversal_blocked(mock_workspace: Path):
    """Verify that path traversal attempts raise PermissionError."""
    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "../../etc/shadow"}
    )

    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    with pytest.raises(PermissionError):
        workflow.run("session_reg_01", request)


# ── Semantic assertions ──────────────────────────────────────────────────────

def test_result_integrity_counts_reflect_manifest(mock_workspace: Path):
    """completed_run_count and failed_run_count in result_integrity_report.json
    must match the values declared in the lab_run_manifest."""
    run_dir = mock_workspace / "data" / "lab_runs" / "run_semantic_01"
    run_dir.mkdir(parents=True)
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "lab_run_id": "run_semantic_01",
            "world_id": "w1", "scenario_id": "s1", "experiment_id": "e1",
            "status": "COMPLETED",
            "started_at": "2026-06-10T00:00:00Z", "ended_at": "2026-06-10T00:05:00Z",
            "run_count": 3, "completed_run_count": 2, "failed_run_count": 1,
            "artifact_root": str(run_dir),
            "schema_versions": {}, "budgets": {}, "storage_usage_mb": 0.5
        }, f)
    for i in range(3):
        child_dir = run_dir / "runs" / f"run_{i}"
        child_dir.mkdir(parents=True)
        with open(child_dir / "run_report.json", "w", encoding="utf-8") as f:
            json.dump({"run_id": f"run_{i}"}, f)

    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "data/lab_runs/run_semantic_01"}
    )
    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_reg_01", request)
    assert res["status"] == "READY"

    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_reg_01" / "registration"
    with open(reg_dir / "result_integrity_report.json", encoding="utf-8") as f:
        report = json.load(f)

    assert report["completed_run_count"] == 2, (
        f"Expected completed_run_count=2, got {report['completed_run_count']}"
    )
    assert report["failed_run_count"] == 1, (
        f"Expected failed_run_count=1, got {report['failed_run_count']}"
    )
    assert report["run_count"] == 3


def test_artifact_index_contains_manifest_entry(mock_workspace: Path):
    """artifact_index.json must contain an entry for lab_run_manifest.json."""
    run_dir = mock_workspace / "data" / "lab_runs" / "run_semantic_02"
    run_dir.mkdir(parents=True)
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "lab_run_id": "run_semantic_02",
            "world_id": "w1", "scenario_id": "s1", "experiment_id": "e1",
            "status": "COMPLETED",
            "started_at": "2026-06-10T00:00:00Z", "ended_at": "2026-06-10T00:05:00Z",
            "run_count": 1, "completed_run_count": 1, "failed_run_count": 0,
            "artifact_root": str(run_dir),
            "schema_versions": {}, "budgets": {}, "storage_usage_mb": 0.1
        }, f)

    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "data/lab_runs/run_semantic_02"}
    )
    workflow = RegisterSimulationResultWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_reg_01", request)
    assert res["status"] == "READY"

    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_reg_01" / "registration"
    with open(reg_dir / "artifact_index.json", encoding="utf-8") as f:
        index = json.load(f)

    relative_paths = [entry["relative_path"] for entry in index]
    assert any("lab_run_manifest.json" in p for p in relative_paths), (
        f"artifact_index must include lab_run_manifest.json; paths found: {relative_paths}"
    )
