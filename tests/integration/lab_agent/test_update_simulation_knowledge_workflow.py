import json
import time
import yaml
import pytest
from datetime import datetime, timezone
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import (
    CompactSimulationDataWorkflow,
    InvestigateSimulationResultWorkflow,
    ProposeSimulationEnhancementsWorkflow,
    UpdateSimulationKnowledgeWorkflow
)

def _build_knowledge_workspace(tmp_path: Path) -> Path:
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


@pytest.fixture
def mock_workspace_for_knowledge(tmp_path: Path) -> Path:
    return _build_knowledge_workspace(tmp_path)


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
    
    assert res["status"] == "SYNCED", f"Expected SYNCED, got {res['status']}"
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


@pytest.fixture
def mock_workspace_empty_insights(mock_workspace_for_knowledge: Path) -> Path:
    """Same as mock_workspace_for_knowledge but with all insight/patch candidates cleared."""
    enhance_dir = (
        mock_workspace_for_knowledge / "data" / "lab_sessions" / "session_know_01" / "enhancement"
    )
    with open(enhance_dir / "insight_candidates.json", "w", encoding="utf-8") as f:
        json.dump([], f)
    patches_dir = enhance_dir / "proposed_patches"
    if patches_dir.is_dir():
        import shutil
        shutil.rmtree(patches_dir)
        patches_dir.mkdir()
    return mock_workspace_for_knowledge


def test_approved_with_no_insights_returns_no_insights(mock_workspace_empty_insights: Path):
    """Approved run with no insight candidates must return NO_INSIGHTS, not BLOCKED or READY."""
    request = WorkflowRequest(
        workflow="UpdateSimulationKnowledge",
        mode="generic",
        user_goal="Sync with empty insight set",
        specific_inputs={
            "approved_by": "user_admin",
            "approval_recorded": True,
            "decision_note": "No new insights this cycle",
        },
    )
    workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=mock_workspace_empty_insights)
    res = workflow.run("session_know_01", request)

    assert res["status"] == "NO_INSIGHTS", (
        f"Approved run with no insights must return NO_INSIGHTS, got {res['status']}"
    )
    assert res["synced_count"] == 0

    # Audit trail must record the sync result
    from src.lab.audit import LabAuditTrail
    trail = LabAuditTrail(mock_workspace_empty_insights)
    events = trail.read_log("session_know_01")
    sync_events = [e for e in events if e["event_type"] == "knowledge_sync_result"]
    assert sync_events, "knowledge_sync_result event must be written to audit trail"
    assert sync_events[-1]["details"]["status"] == "NO_INSIGHTS"
    assert sync_events[-1]["details"]["synced_insights"] == 0


def test_approved_with_insights_not_blocked(mock_workspace_for_knowledge: Path):
    """Approved run with real insights must return SYNCED, not BLOCKED, not READY, not NO_INSIGHTS."""
    request = WorkflowRequest(
        workflow="UpdateSimulationKnowledge",
        mode="generic",
        user_goal="Sync with approved insights",
        specific_inputs={
            "approved_by": "user_admin",
            "approval_recorded": True,
            "decision_note": "Syncing verified anomalies",
        },
    )
    workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    res = workflow.run("session_know_01", request)

    assert res["status"] == "SYNCED", (
        f"Approved non-empty insight set must return SYNCED, got {res['status']}"
    )
    assert res["status"] != "BLOCKED", "BLOCKED must never be the result of an approved sync"
    assert res["synced_count"] >= 1

    # Audit trail must record the sync result with correct counts
    from src.lab.audit import LabAuditTrail
    trail = LabAuditTrail(mock_workspace_for_knowledge)
    events = trail.read_log("session_know_01")
    sync_events = [e for e in events if e["event_type"] == "knowledge_sync_result"]
    assert sync_events, "knowledge_sync_result event must be written to audit trail"
    assert sync_events[-1]["details"]["status"] == "SYNCED"
    assert sync_events[-1]["details"]["synced_insights"] >= 1


def test_knowledge_timestamps_are_dynamic(tmp_path_factory):
    """Verify insight created_at and decision log timestamp are generated live per run.

    Regression test for the hardcoded "2026-05-24T10:00:00Z" literal: runs the
    workflow twice against independent workspaces with a real time gap between
    them and asserts both timestamp fields are parseable, close to "now" at
    write time, and differ between the two runs.
    """
    request_kwargs = {
        "workflow": "UpdateSimulationKnowledge",
        "mode": "generic",
        "user_goal": "Verify timestamps reflect actual run time",
        "specific_inputs": {
            "approved_by": "user_admin",
            "approval_recorded": True,
            "decision_note": "Checking dynamic timestamps",
        },
    }

    def run_once(tag: str):
        workspace = _build_knowledge_workspace(tmp_path_factory.mktemp(tag))
        workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=workspace)
        before = datetime.now(timezone.utc)
        result = workflow.run("session_know_01", WorkflowRequest(**request_kwargs))
        after = datetime.now(timezone.utc)
        assert result["status"] == "SYNCED"

        knowledge_dir = workspace / "data" / "lab_knowledge"
        insight_file = next((knowledge_dir / "insights").glob("*.json"))
        with open(insight_file, "r", encoding="utf-8") as f:
            insight = json.load(f)

        dec_file = knowledge_dir / "decisions" / "decision_log.jsonl"
        with open(dec_file, "r", encoding="utf-8") as f:
            decision = json.loads(f.readlines()[-1])

        for field, raw in (("created_at", insight["created_at"]), ("timestamp", decision["timestamp"])):
            assert raw != "2026-05-24T10:00:00Z", f"{field} must not be the hardcoded literal"
            parsed = datetime.fromisoformat(raw)
            assert before <= parsed <= after, f"{field} {raw!r} is not within the run's execution window"

        return insight["created_at"], decision["timestamp"]

    created_at_1, timestamp_1 = run_once("know_ts_1")
    time.sleep(0.05)
    created_at_2, timestamp_2 = run_once("know_ts_2")

    assert created_at_1 != created_at_2, "created_at must differ across separate runs"
    assert timestamp_1 != timestamp_2, "decision log timestamp must differ across separate runs"
