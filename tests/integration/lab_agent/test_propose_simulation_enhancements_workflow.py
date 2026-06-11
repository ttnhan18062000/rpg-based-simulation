import json
import yaml
import pytest
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import (
    CompactSimulationDataWorkflow,
    InvestigateSimulationResultWorkflow,
    ProposeSimulationEnhancementsWorkflow
)

@pytest.fixture
def mock_workspace_with_investigation_data(tmp_path: Path) -> Path:
    """Sets up base workspaces, running compaction and investigation."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    (tmp_path / "data" / "lab_runs").mkdir(parents=True)
    
    # Initialize active session
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_enhance_01")
    
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
    comp_workflow.run("session_enhance_01", comp_request)
    
    # Run investigation
    invest_request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="specific",
        specific_inputs={
            "lab_run_path": "data/lab_runs/manual_run_01",
            "analysis_depth": "standard"
        }
    )
    invest_workflow = InvestigateSimulationResultWorkflow(workspace_root=tmp_path)
    invest_workflow.run("session_enhance_01", invest_request)
    
    return tmp_path

def test_enhancement_plan_and_patches_created(mock_workspace_with_investigation_data: Path):
    """Verify that the workflow generates the 5 output artifacts under enhancement/."""
    request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="generic",
        user_goal="Generate declarative metamorphic patch recommendations"
    )
    
    workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=mock_workspace_with_investigation_data)
    res = workflow.run("session_enhance_01", request)
    
    assert res["status"] == "READY"
    assert "enhancement_plan.md" in res["report_path"]
    
    enhance_dir = mock_workspace_with_investigation_data / "data" / "lab_sessions" / "session_enhance_01" / "enhancement"
    
    # Assert all 5 artifacts/directories are present
    assert (enhance_dir / "enhancement_plan.md").is_file()
    assert (enhance_dir / "proposed_patches").is_dir()
    assert (enhance_dir / "next_experiment_drafts").is_dir()
    assert (enhance_dir / "insight_candidates.json").is_file()
    assert (enhance_dir / "change_risk_report.json").is_file()
    
    # Check that proposed patches are generated and contain evidence
    patches = list((enhance_dir / "proposed_patches").glob("*.yaml"))
    assert len(patches) > 0
    for patch_file in patches:
        with open(patch_file, "r", encoding="utf-8") as f:
            patch = yaml.safe_load(f)
        assert "patch_id" in patch
        assert "evidence" in patch
        assert len(patch["evidence"]) > 0

def test_enhancement_forbidden_change_respected(mock_workspace_with_investigation_data: Path):
    """Verify that proposing a forbidden change type is rejected."""
    request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="specific",
        specific_inputs={
            "allowed_change_types": ["ScenarioSpec"],
            "forbidden_change_types": ["KnownIssues"]
        }
    )
    
    workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=mock_workspace_with_investigation_data)
    with pytest.raises(ValueError):
        workflow.run("session_enhance_01", request)

def test_enhancement_no_direct_mutation(mock_workspace_with_investigation_data: Path):
    """Verify that active repository spec files are NOT mutated or overwritten directly."""
    # Write a dummy target spec file that patches reference
    dummy_yaml = mock_workspace_with_investigation_data / "docs" / "mechanics" / "known_issues.yaml"
    dummy_yaml.parent.mkdir(parents=True, exist_ok=True)
    dummy_yaml.write_text("initial_state: true", encoding="utf-8")
    
    request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="generic",
        user_goal="Verify isolation protection and spec non-mutation"
    )
    
    workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=mock_workspace_with_investigation_data)
    workflow.run("session_enhance_01", request)
    
    # Verify that the active target yaml remains unmodified
    assert dummy_yaml.read_text(encoding="utf-8").strip() == "initial_state: true"

def test_enhancement_unsupported_patch_operation_rejected(mock_workspace_with_investigation_data: Path):
    """Verify that unsupported patch operations trigger ValueError."""
    request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="specific",
        specific_inputs={
            "manual_patches": [
                {
                    "patch_id": "test_invalid_op",
                    "target_type": "ScenarioSpec",
                    "target_file": "data/scenarios/scenario.yaml",
                    "operation": "delete", # Unsupported
                    "path": "required_signals",
                    "value": "Dummy",
                    "reason": "Testing invalid operation rejection",
                    "evidence": ["some_evidence"]
                }
            ]
        }
    )
    
    workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=mock_workspace_with_investigation_data)
    with pytest.raises(ValueError):
        workflow.run("session_enhance_01", request)

def test_enhancement_evidence_free_critical_rejected(mock_workspace_with_investigation_data: Path):
    """Verify that critical rule patches with missing evidence references trigger ValueError."""
    request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="specific",
        specific_inputs={
            "manual_patches": [
                {
                    "patch_id": "register_known_issue_empty_evidence",
                    "target_type": "KnownIssues",
                    "target_file": "docs/mechanics/known_issues.yaml",
                    "operation": "add",
                    "path": "known_issues.rules",
                    "value": "Dummy",
                    "reason": "Testing empty evidence validation",
                    "evidence": [] # Empty
                }
            ]
        }
    )

    workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=mock_workspace_with_investigation_data)
    with pytest.raises(ValueError):
        workflow.run("session_enhance_01", request)


# ── Semantic assertions ──────────────────────────────────────────────────────

def test_critical_issue_generates_known_issues_proposal(mock_workspace_with_investigation_data: Path):
    """A CRITICAL issue in issue_backlog must produce at least one KnownIssues patch proposal."""
    request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="generic",
        user_goal="Verify critical produces proposal"
    )
    workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=mock_workspace_with_investigation_data)
    res = workflow.run("session_enhance_01", request)
    assert res["status"] == "READY"

    enhance_dir = (
        mock_workspace_with_investigation_data / "data" / "lab_sessions"
        / "session_enhance_01" / "enhancement"
    )
    known_issues_patches = []
    for patch_file in (enhance_dir / "proposed_patches").glob("*.yaml"):
        patch = yaml.safe_load(patch_file.read_text(encoding="utf-8"))
        if patch.get("target_type") == "KnownIssues":
            known_issues_patches.append(patch)

    assert len(known_issues_patches) >= 1, (
        "CRITICAL HardLawViolationRule must produce at least one KnownIssues patch"
    )
    assert any(
        "HardLawViolationRule" in str(p.get("value", "")) or
        "HardLawViolationRule" in str(p.get("reason", ""))
        for p in known_issues_patches
    ), f"KnownIssues patch must reference HardLawViolationRule; found: {known_issues_patches}"


@pytest.fixture
def mock_workspace_warning_only(tmp_path: Path) -> Path:
    """Workspace where investigation found only WARNING-level issues — no CRITICAL."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_enhance_warn")

    invest_dir = (
        tmp_path / "data" / "lab_sessions" / "session_enhance_warn" / "investigation"
    )
    invest_dir.mkdir(parents=True, exist_ok=True)

    with open(invest_dir / "investigation_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "session_id": "session_enhance_warn",
            "lab_run_id": "run_warn",
            "analysis_depth": "standard",
            "critical_issues": [],
        }, f)
    with open(invest_dir / "issue_backlog.json", "w", encoding="utf-8") as f:
        json.dump([{
            "issue_id": "ISSUE-001",
            "rule_name": "EconInflation",
            "severity": "WARNING",
            "domain": "resource",
            "description": "Minor inflation drift",
            "frequency": 2,
            "affected_entities": [],
            "state": "OPEN"
        }], f)
    with open(invest_dir / "missing_signals.json", "w", encoding="utf-8") as f:
        json.dump([], f)
    return tmp_path


def test_warning_only_issue_no_known_issues_patch(mock_workspace_warning_only: Path):
    """WARNING-level issues must not auto-generate KnownIssues patches — only CRITICAL triggers them."""
    request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="generic",
        user_goal="Verify WARNING does not auto-propose"
    )
    workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=mock_workspace_warning_only)
    res = workflow.run("session_enhance_warn", request)
    assert res["status"] == "READY"

    enhance_dir = (
        mock_workspace_warning_only / "data" / "lab_sessions"
        / "session_enhance_warn" / "enhancement"
    )
    known_issues_patches = [
        f for f in (enhance_dir / "proposed_patches").glob("*.yaml")
        if yaml.safe_load(f.read_text(encoding="utf-8")).get("target_type") == "KnownIssues"
    ]
    assert len(known_issues_patches) == 0, (
        f"WARNING-only issues must not generate KnownIssues patches; found: {known_issues_patches}"
    )
