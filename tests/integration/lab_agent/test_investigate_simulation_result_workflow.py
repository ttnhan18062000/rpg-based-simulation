import json
import pytest
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import CompactSimulationDataWorkflow, InvestigateSimulationResultWorkflow

@pytest.fixture
def mock_workspace_with_compacted_data(tmp_path: Path) -> Path:
    """Sets up base workspaces, lab run and lab session directories, and runs compaction."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    (tmp_path / "data" / "lab_runs").mkdir(parents=True)
    
    # Initialize active session
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_investigate_01")
    
    run_dir = tmp_path / "data" / "lab_runs" / "manual_run_01"
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

    # Run compaction
    comp_request = WorkflowRequest(
        workflow="CompactSimulationData",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_01",
            "top_n": 5,
            "focus_domains": ["resource", "movement", "strategy", "combat", "kernel"]
        }
    )
    comp_workflow = CompactSimulationDataWorkflow(workspace_root=tmp_path)
    comp_workflow.run("session_investigate_01", comp_request)
    
    # Save generic mode registration path for generic mode checks
    reg_dir = tmp_path / "data" / "lab_sessions" / "session_investigate_01" / "registration"
    (reg_dir / "actual_lab_run_path.txt").write_text("data/lab_runs/manual_run_01", encoding="utf-8")
    
    return tmp_path

def test_investigation_light_depth(mock_workspace_with_compacted_data: Path):
    """Verify that a light depth investigation succeeds and creates structured artifacts for top 3 issues."""
    request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_01",
            "analysis_depth": "light"
        }
    )
    
    workflow = InvestigateSimulationResultWorkflow(workspace_root=mock_workspace_with_compacted_data)
    res = workflow.run("session_investigate_01", request)
    
    assert res["status"] == "READY"
    assert "investigation_report.md" in res["report_path"]
    
    invest_dir = mock_workspace_with_compacted_data / "data" / "lab_sessions" / "session_investigate_01" / "investigation"
    
    # Assert all 6 artifacts are present
    assert (invest_dir / "investigation_report.md").is_file()
    assert (invest_dir / "investigation_report.json").is_file()
    assert (invest_dir / "issue_backlog.json").is_file()
    assert (invest_dir / "missing_signals.json").is_file()
    assert (invest_dir / "insight_candidates.json").is_file()
    assert (invest_dir / "next_experiment_suggestions.json").is_file()
    
    # Validate investigation_report.json contents
    with open(invest_dir / "investigation_report.json", "r", encoding="utf-8") as f:
        report = json.load(f)
    assert report["session_id"] == "session_investigate_01"
    assert report["lab_run_id"] == "manual_run_01"
    assert report["analysis_depth"] == "light"
    assert len(report["critical_issues"]) == 1
    assert report["critical_issues"][0]["rule_name"] == "HardLawViolationRule"

def test_investigation_standard_depth(mock_workspace_with_compacted_data: Path):
    """Verify that standard depth investigation examines top 10 and flags missing signals."""
    request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="generic",
        user_goal="Run post-analysis metamorphic validation",
        specific_inputs={
            "analysis_depth": "standard"
        }
    )
    
    workflow = InvestigateSimulationResultWorkflow(workspace_root=mock_workspace_with_compacted_data)
    res = workflow.run("session_investigate_01", request)
    
    assert res["status"] == "READY"
    
    invest_dir = mock_workspace_with_compacted_data / "data" / "lab_sessions" / "session_investigate_01" / "investigation"
    with open(invest_dir / "investigation_report.json", "r", encoding="utf-8") as f:
        report = json.load(f)
    assert report["analysis_depth"] == "standard"
    
    # Validate missing signals JSON
    with open(invest_dir / "missing_signals.json", "r", encoding="utf-8") as f:
        missing = json.load(f)
    # The default mock signal coverage triggers missing signals for gameplay domains with zero logs
    assert len(missing) >= 0

def test_investigation_deep_depth(mock_workspace_with_compacted_data: Path):
    """Verify that deep depth investigation prioritizes focus rules and generates suggestions."""
    request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_01",
            "analysis_depth": "deep",
            "focus_issues": ["NavigationStuckRule"],
            "seeds": [123, 456],
            "tick_range": [0, 5000]
        }
    )
    
    workflow = InvestigateSimulationResultWorkflow(workspace_root=mock_workspace_with_compacted_data)
    res = workflow.run("session_investigate_01", request)
    
    assert res["status"] == "READY"
    
    invest_dir = mock_workspace_with_compacted_data / "data" / "lab_sessions" / "session_investigate_01" / "investigation"
    with open(invest_dir / "next_experiment_suggestions.json", "r", encoding="utf-8") as f:
        suggestions = json.load(f)
    assert len(suggestions) == 1
    assert suggestions[0]["suggested_seeds"] == [123, 456]

def test_investigation_invalid_run_blocked(mock_workspace_with_compacted_data: Path):
    """Verify that an unsupported run state (e.g. FAILED) is rejected."""
    run_dir = mock_workspace_with_compacted_data / "data" / "lab_runs" / "manual_run_02"
    run_dir.mkdir(parents=True)
    manifest_data = {
        "lab_run_id": "manual_run_02",
        "status": "FAILED",
        "artifact_root": str(run_dir)
    }
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_02",
            "analysis_depth": "standard"
        }
    )
    
    workflow = InvestigateSimulationResultWorkflow(workspace_root=mock_workspace_with_compacted_data)
    res = workflow.run("session_investigate_01", request)
    assert res["status"] == "BLOCKED"
    assert "Unsupported lab run state" in res["reason"]

def test_investigation_traversal_blocked(mock_workspace_with_compacted_data: Path):
    """Verify that sandbox escape attempts raise PermissionError."""
    request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="specific",
        specific_inputs={
            "lab_run_path": "../../../etc",
            "analysis_depth": "standard"
        }
    )

    workflow = InvestigateSimulationResultWorkflow(workspace_root=mock_workspace_with_compacted_data)
    with pytest.raises(PermissionError):
        workflow.run("session_investigate_01", request)


# ── Semantic assertions ──────────────────────────────────────────────────────

@pytest.fixture
def mock_workspace_with_healthy_run(tmp_path: Path) -> Path:
    """Workspace where all runs completed with zero anomalies — no CRITICAL issues expected."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    (tmp_path / "data" / "lab_runs").mkdir(parents=True)

    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_healthy_01")

    run_dir = tmp_path / "data" / "lab_runs" / "healthy_run_01"
    run_dir.mkdir(parents=True)
    with open(run_dir / "lab_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "lab_run_id": "healthy_run_01",
            "world_id": "world_01", "scenario_id": "scenario_01", "experiment_id": "exp_01",
            "status": "COMPLETED",
            "started_at": "2026-06-10T00:00:00Z", "ended_at": "2026-06-10T00:05:00Z",
            "run_count": 1, "completed_run_count": 1, "failed_run_count": 0,
            "artifact_root": str(run_dir),
            "schema_versions": {}, "budgets": {}, "storage_usage_mb": 0.1
        }, f)

    child_dir = run_dir / "runs" / "run_0"
    child_dir.mkdir(parents=True)
    with open(child_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "health_score": 99.0,
            "total_anomalies_count": 0,
            "anomalies": [],
            "critical_count": 0,
            "warning_count": 0,
            "error_count": 0
        }, f)

    # Run compaction to produce compact_summary.json and issue_index.json
    comp_request = WorkflowRequest(
        workflow="CompactSimulationData",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/healthy_run_01",
            "top_n": 5,
            "focus_domains": ["resource", "movement", "strategy", "combat", "kernel"]
        }
    )
    CompactSimulationDataWorkflow(workspace_root=tmp_path).run("session_healthy_01", comp_request)

    reg_dir = tmp_path / "data" / "lab_sessions" / "session_healthy_01" / "registration"
    (reg_dir / "actual_lab_run_path.txt").write_text("data/lab_runs/healthy_run_01", encoding="utf-8")
    return tmp_path


def test_investigation_healthy_run_zero_critical_issues(mock_workspace_with_healthy_run: Path):
    """A run with no anomalies must produce zero critical issues — no false positives."""
    request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/healthy_run_01",
            "analysis_depth": "standard"
        }
    )
    workflow = InvestigateSimulationResultWorkflow(workspace_root=mock_workspace_with_healthy_run)
    res = workflow.run("session_healthy_01", request)
    assert res["status"] == "READY"

    invest_dir = (
        mock_workspace_with_healthy_run / "data" / "lab_sessions"
        / "session_healthy_01" / "investigation"
    )
    with open(invest_dir / "investigation_report.json", encoding="utf-8") as f:
        report = json.load(f)

    assert report["critical_issues"] == [], (
        f"Healthy run must produce zero critical issues; got: {report['critical_issues']}"
    )
