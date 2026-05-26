import json
import pytest
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import CompactSimulationDataWorkflow

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Sets up base workspaces, lab run and lab session directories."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    (tmp_path / "data" / "lab_runs").mkdir(parents=True)
    
    # Initialize active session
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_compact_01")
    return tmp_path

def test_compaction_complete_success(mock_workspace: Path):
    """Verify that a successful complete sweep is compacted correctly into all digest files."""
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
        "schema_versions": {},
        "budgets": {},
        "storage_usage_mb": 1.2
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    # Write child run 0 report
    child_0_dir = run_dir / "runs" / "run_0"
    child_0_dir.mkdir(parents=True)
    child_0_report = {
        "health_score": 95.0,
        "total_anomalies_count": 1,
        "anomalies": [
            {
                "rule_name": "HardLawViolationRule",
                "severity": "CRITICAL",
                "entity_id": 42,
                "tick_detected": 100,
                "message": "Critical hard law violation at tick 100"
            }
        ],
        "rule_execution": [
            {"rule_id": "HardLawViolationRule", "status": "TRIGGERED"}
        ],
        "critical_count": 1,
        "warning_count": 0,
        "error_count": 0
    }
    with open(child_0_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump(child_0_report, f)

    # Write child run 1 report
    child_1_dir = run_dir / "runs" / "run_1"
    child_1_dir.mkdir(parents=True)
    child_1_report = {
        "health_score": 80.0,
        "total_anomalies_count": 2,
        "anomalies": [
            {
                "rule_name": "NavigationStuckRule",
                "severity": "WARNING",
                "entity_id": 42,
                "tick_detected": 200,
                "message": "Navigation stuck at tick 200"
            },
            {
                "rule_name": "NavigationStuckRule",
                "severity": "ERROR",
                "entity_id": 99,
                "tick_detected": 220,
                "message": "Navigation stuck at tick 220"
            }
        ],
        "rule_execution": [
            {"rule_id": "NavigationStuckRule", "status": "TRIGGERED"}
        ],
        "critical_count": 0,
        "warning_count": 1,
        "error_count": 1
    }
    with open(child_1_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump(child_1_report, f)
            
    # Run specific mode compaction workflow
    request = WorkflowRequest(
        workflow="CompactSimulationData",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_01",
            "top_n": 5,
            "focus_domains": ["resource", "movement", "strategy", "combat", "kernel"]
        }
    )
    
    workflow = CompactSimulationDataWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_compact_01", request)
    
    assert res["status"] == "READY"
    assert "compact_summary.md" in res["report_path"]
    
    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_compact_01" / "registration"
    
    # Assert all files are present
    assert (reg_dir / "compact_summary.json").is_file()
    assert (reg_dir / "compact_summary.md").is_file()
    assert (reg_dir / "issue_index.json").is_file()
    assert (reg_dir / "evidence_pack_index.json").is_file()
    assert (reg_dir / "metric_digest.json").is_file()
    assert (reg_dir / "entity_hotspots.json").is_file()
    assert (reg_dir / "signal_coverage.json").is_file()

    # Verify Issue Index contents
    with open(reg_dir / "issue_index.json", "r", encoding="utf-8") as f:
        issues = json.load(f)
    assert len(issues) == 2
    # NavigationStuckRule has count 2, HardLawViolationRule has count 1
    assert issues[0]["rule_name"] == "NavigationStuckRule"
    assert issues[0]["count"] == 2
    assert issues[0]["severity"] == "ERROR"
    assert issues[0]["tick_range"] == [200, 220]
    assert issues[0]["affected_entities"] == [42, 99]

    assert issues[1]["rule_name"] == "HardLawViolationRule"
    assert issues[1]["count"] == 1
    assert issues[1]["severity"] == "CRITICAL"
    assert issues[1]["tick_range"] == [100, 100]
    assert issues[1]["affected_entities"] == [42]

    # Verify Hotspots contents
    with open(reg_dir / "entity_hotspots.json", "r", encoding="utf-8") as f:
        hotspots = json.load(f)
    assert len(hotspots) == 2
    assert hotspots[0]["entity_id"] == 42
    assert hotspots[0]["anomaly_count"] == 2
    assert "HardLawViolationRule" in hotspots[0]["issue_types"]
    assert "NavigationStuckRule" in hotspots[0]["issue_types"]

    assert hotspots[1]["entity_id"] == 99
    assert hotspots[1]["anomaly_count"] == 1

    # Verify Metric Digest contents
    with open(reg_dir / "metric_digest.json", "r", encoding="utf-8") as f:
        digest = json.load(f)
    assert digest["avg_health_score"] == 87.5
    assert digest["min_health_score"] == 80.0
    assert digest["max_health_score"] == 95.0
    assert digest["total_criticals"] == 1
    assert digest["total_errors"] == 1
    assert digest["total_warnings"] == 1
    assert digest["tick_max"] == 220

    # Verify Signal Coverage contents
    with open(reg_dir / "signal_coverage.json", "r", encoding="utf-8") as f:
        coverage = json.load(f)
    # Check that movement is covered and HIGH_FOCUS
    movement_cov = next(c for c in coverage if c["domain"] == "movement")
    assert movement_cov["covered"] is True
    assert movement_cov["total_anomalies"] == 2
    assert movement_cov["focus_status"] == "HIGH_FOCUS"

    # Check strategy is FOCUS but has 0 anomalies
    strat_cov = next(c for c in coverage if c["domain"] == "strategy")
    assert strat_cov["covered"] is False
    assert strat_cov["total_anomalies"] == 0
    assert strat_cov["focus_status"] == "FOCUS"

def test_compaction_top_n_respected(mock_workspace: Path):
    """Verify that the top_n limit limits issues, hotspots, and evidence lists to the cap."""
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
        "run_count": 1,
        "completed_run_count": 1,
        "failed_run_count": 0,
        "artifact_root": str(run_dir),
        "schema_versions": {},
        "budgets": {},
        "storage_usage_mb": 0.5
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    child_dir = run_dir / "runs" / "run_0"
    child_dir.mkdir(parents=True)
    child_report = {
        "health_score": 95.0,
        "total_anomalies_count": 2,
        "anomalies": [
            {
                "rule_name": "HardLawViolationRule",
                "severity": "CRITICAL",
                "entity_id": 42,
                "tick_detected": 100,
                "message": "Critical violation 1"
            },
            {
                "rule_name": "NavigationStuckRule",
                "severity": "WARNING",
                "entity_id": 99,
                "tick_detected": 200,
                "message": "Warning navigation stuck"
            }
        ],
        "rule_execution": [],
        "critical_count": 1,
        "warning_count": 1,
        "error_count": 0
    }
    with open(child_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump(child_report, f)

    # Run specific compaction workflow with top_n = 1
    request = WorkflowRequest(
        workflow="CompactSimulationData",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_01",
            "top_n": 1,
            "focus_domains": ["kernel"]
        }
    )
    
    workflow = CompactSimulationDataWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_compact_01", request)
    assert res["status"] == "READY"
    
    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_compact_01" / "registration"
    
    with open(reg_dir / "issue_index.json", "r", encoding="utf-8") as f:
        issues = json.load(f)
    assert len(issues) == 1  # Capped at top_n=1

    with open(reg_dir / "entity_hotspots.json", "r", encoding="utf-8") as f:
        hotspots = json.load(f)
    assert len(hotspots) == 1  # Capped at top_n=1

def test_compaction_focus_domains(mock_workspace: Path):
    """Verify that domain coverage focuses status on movement while kernel is NONE when not specified."""
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
        "ended_at": None,
        "run_count": 1,
        "completed_run_count": 1,
        "failed_run_count": 0,
        "artifact_root": str(run_dir),
        "schema_versions": {},
        "budgets": {},
        "storage_usage_mb": 0.5
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    child_dir = run_dir / "runs" / "run_0"
    child_dir.mkdir(parents=True)
    child_report = {
        "health_score": 95.0,
        "total_anomalies_count": 1,
        "anomalies": [
            {
                "rule_name": "NavigationStuckRule",
                "severity": "WARNING",
                "entity_id": 42,
                "tick_detected": 100,
                "message": "Warning navigation stuck"
            }
        ],
        "rule_execution": [],
        "critical_count": 0,
        "warning_count": 1,
        "error_count": 0
    }
    with open(child_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump(child_report, f)

    # Run specific compaction workflow focusing on "movement" and "strategy" (kernel not in focus)
    request = WorkflowRequest(
        workflow="CompactSimulationData",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_01",
            "top_n": 5,
            "focus_domains": ["movement", "strategy"]
        }
    )
    
    workflow = CompactSimulationDataWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_compact_01", request)
    assert res["status"] == "READY"
    
    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_compact_01" / "registration"
    
    with open(reg_dir / "signal_coverage.json", "r", encoding="utf-8") as f:
        coverage = json.load(f)
        
    move = next(c for c in coverage if c["domain"] == "movement")
    assert move["focus_status"] == "HIGH_FOCUS"
    
    strat = next(c for c in coverage if c["domain"] == "strategy")
    assert strat["focus_status"] == "FOCUS"
    
    kernel = next(c for c in coverage if c["domain"] == "kernel")
    assert kernel["focus_status"] == "NONE"

def test_compaction_generic_mode(mock_workspace: Path):
    """Verify that generic mode resolves the run path automatically from registered path file."""
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
        "ended_at": None,
        "run_count": 1,
        "completed_run_count": 1,
        "failed_run_count": 0,
        "artifact_root": str(run_dir),
        "schema_versions": {},
        "budgets": {},
        "storage_usage_mb": 0.5
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    child_dir = run_dir / "runs" / "run_0"
    child_dir.mkdir(parents=True)
    child_report = {
        "health_score": 95.0,
        "total_anomalies_count": 0,
        "anomalies": [],
        "rule_execution": [],
        "critical_count": 0,
        "warning_count": 0,
        "error_count": 0
    }
    with open(child_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump(child_report, f)

    # Register the run path in generic mode stage file
    reg_dir = mock_workspace / "data" / "lab_sessions" / "session_compact_01" / "registration"
    reg_dir.mkdir(parents=True, exist_ok=True)
    (reg_dir / "actual_lab_run_path.txt").write_text("data/lab_runs/manual_run_01", encoding="utf-8")

    # Run generic compaction workflow
    request = WorkflowRequest(
        workflow="CompactSimulationData",
        mode="generic",
        user_goal="Compact recent simulation results"
    )
    
    workflow = CompactSimulationDataWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_compact_01", request)
    assert res["status"] == "READY"
    assert (reg_dir / "compact_summary.json").is_file()

def test_compaction_traversal_blocked(mock_workspace: Path):
    """Verify that trying to break out of the workspace sandbox is strictly blocked."""
    request = WorkflowRequest(
        workflow="CompactSimulationData",
        mode="specific",
        specific_inputs={
            "lab_run_path": "../../../etc"
        }
    )
    workflow = CompactSimulationDataWorkflow(workspace_root=mock_workspace)
    with pytest.raises(PermissionError):
        workflow.run("session_compact_01", request)
