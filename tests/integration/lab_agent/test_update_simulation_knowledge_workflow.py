import json
import yaml
import pytest
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import (
    CompactSimulationDataWorkflow,
    InvestigateSimulationResultWorkflow,
    ProposeSimulationEnhancementsWorkflow,
    UpdateSimulationKnowledgeWorkflow
)

@pytest.fixture
def mock_workspace_for_knowledge(tmp_path: Path) -> Path:
    """Sets up a complete session stage with investigation and enhancement results."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    (tmp_path / "data" / "lab_runs").mkdir(parents=True)
    
    # Initialize active session
    session_store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    session_store.create_session("session_know_01")
    
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
    comp_workflow.run("session_know_01", comp_request)
    
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
    invest_workflow.run("session_know_01", invest_request)

    # Run enhancement
    enhance_request = WorkflowRequest(
        workflow="ProposeSimulationEnhancements",
        mode="generic",
        user_goal="Generate proposals"
    )
    enhance_workflow = ProposeSimulationEnhancementsWorkflow(workspace_root=tmp_path)
    enhance_workflow.run("session_know_01", enhance_request)
    
    return tmp_path

def test_knowledge_update_success(mock_workspace_for_knowledge: Path):
    """Verify that approved insights, known issues, and decisions are successfully stored."""
    request = WorkflowRequest(
        workflow="UpdateSimulationKnowledge",
        mode="generic",
        user_goal="Verify successful database synchronization",
        specific_inputs={
            "approved_by": "user_admin",
            "approval_recorded": True,
            "decision_note": "Syncing all verified anomalies for manual_run_01"
        }
    )
    
    workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    res = workflow.run("session_know_01", request)
    
    assert res["status"] == "READY"
    assert "knowledge_update_report.md" in res["report_path"]
    
    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"
    
    # Check insight is stored and evidence is preserved
    insights = list((knowledge_dir / "insights").glob("*.json"))
    assert len(insights) > 0
    for ins_file in insights:
        with open(ins_file, "r", encoding="utf-8") as f:
            ins = json.load(f)
        assert ins["status"] == "APPROVED"
        assert ins["insight_id"].startswith("INSIGHT-")
        assert len(ins["evidence_refs"]) > 0
        
    # Check known issue is stored
    issues = list((knowledge_dir / "known_issues").glob("*.json"))
    assert len(issues) > 0
    for iss_file in issues:
        with open(iss_file, "r", encoding="utf-8") as f:
            issue = json.load(f)
        assert issue["status"] == "STORED"
        
    # Check decision log is appended
    dec_file = knowledge_dir / "decisions" / "decision_log.jsonl"
    assert dec_file.is_file()
    with open(dec_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
    dec_entry = json.loads(lines[0])
    assert dec_entry["session_id"] == "session_know_01"
    assert dec_entry["decision_note"] == "Syncing all verified anomalies for manual_run_01"
    assert dec_entry["approved_by"] == "user_admin"

def test_knowledge_unapproved_rejected(mock_workspace_for_knowledge: Path):
    """Verify that running without an approval marker is strictly rejected."""
    request = WorkflowRequest(
        workflow="UpdateSimulationKnowledge",
        mode="generic",
        user_goal="Verify unapproved updates are rejected",
        specific_inputs={
            # approved_by and approval_recorded missing/omitted
            "decision_note": "Syncing unapproved changes"
        }
    )
    
    workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    with pytest.raises(ValueError) as exc:
        workflow.run("session_know_01", request)
    assert "Explicit user approval is required" in str(exc.value)

def test_knowledge_duplicate_insight_rejected(mock_workspace_for_knowledge: Path):
    """Verify that duplicate insight registration is detected and rejected."""
    # Write a duplicate insight file beforehand to simulate prior sync
    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"
    insights_dir = knowledge_dir / "insights"
    insights_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the staged insight to get its exact ID
    enhance_dir = mock_workspace_for_knowledge / "data" / "lab_sessions" / "session_know_01" / "enhancement"
    with open(enhance_dir / "insight_candidates.json", "r", encoding="utf-8") as f:
        candidates = json.load(f)
    dup_id = candidates[0]["insight_id"].lower()
    
    (insights_dir / f"{dup_id}.json").write_text("{}", encoding="utf-8")
    
    request = WorkflowRequest(
        workflow="UpdateSimulationKnowledge",
        mode="generic",
        user_goal="Verify duplicate insights are rejected",
        specific_inputs={
            "approved_by": "user_admin",
            "approval_recorded": True
        }
    )
    
    workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    with pytest.raises(ValueError) as exc:
        workflow.run("session_know_01", request)
    assert "Duplicate insight registration detected" in str(exc.value)

def test_knowledge_anti_misdirection_rules(mock_workspace_for_knowledge: Path):
    """Verify that updating rules/principles requires approved_by string marker."""
    # Omit approved_by string but set approval_recorded boolean
    request = WorkflowRequest(
        workflow="UpdateSimulationKnowledge",
        mode="generic",
        user_goal="Verify anti-misdirection safeguards block unapproved spec updates",
        specific_inputs={
            "approval_recorded": True # Boolean set but string approved_by is missing
        }
    )
    
    # Modify proposed patch to trigger rule/spec update
    enhance_dir = mock_workspace_for_knowledge / "data" / "lab_sessions" / "session_know_01" / "enhancement"
    patch_file = list((enhance_dir / "proposed_patches").glob("*.yaml"))[0]
    with open(patch_file, "r", encoding="utf-8") as f:
        patch_data = yaml.safe_load(f)
    patch_data["target_type"] = "ScenarioSpec" # Triggers rulebook/principles sync
    with open(patch_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(patch_data, f)
        
    workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    with pytest.raises(ValueError) as exc:
        workflow.run("session_know_01", request)
    assert "Workflow cannot update rules/principles without a valid approval marker" in str(exc.value)
