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
    UpdateSimulationKnowledgeWorkflow,
    RevertSimulationKnowledgeWorkflow,
    LabKnowledgeRevertError,
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


def _sync_default(workspace: Path, decision_note: str = "Syncing verified anomalies"):
    """Runs UpdateSimulationKnowledgeWorkflow once with the default (approved) fixture inputs.

    The default `mock_workspace_for_knowledge` workspace already yields one insight, one
    KnownIssues patch, and four ScenarioSpec patches, so this exercises insights/known_issues/
    rules in a single sync without any patch-mutation boilerplate.
    """
    request = WorkflowRequest(
        workflow="UpdateSimulationKnowledge",
        mode="generic",
        user_goal="Sync for revert test setup",
        specific_inputs={
            "approved_by": "user_admin",
            "approval_recorded": True,
            "decision_note": decision_note,
        },
    )
    workflow = UpdateSimulationKnowledgeWorkflow(workspace_root=workspace)
    return workflow.run("session_know_01", request)


def test_files_written_includes_known_issues_and_rules_with_hashes(mock_workspace_for_knowledge: Path):
    """Step 1 payload-shape regression: files_written must list known_issues/rules paths with
    file_hashes, and knowledge_sync_result must echo the exact decision_log_entry dict."""
    from src.lab.audit import LabAuditTrail

    result = _sync_default(mock_workspace_for_knowledge)
    assert result["status"] == "SYNCED"

    trail = LabAuditTrail(mock_workspace_for_knowledge)
    events = trail.read_log("session_know_01")

    files_written = [e for e in events if e["event_type"] == "files_written"][-1]
    files = files_written["details"]["files"]
    assert "decisions/decision_log.jsonl" in files
    assert any(f.startswith("known_issues/") for f in files), files
    assert any(f.startswith("rules/") for f in files), files
    assert any(f.startswith("insights/") for f in files), files

    file_hashes = files_written["details"]["file_hashes"]
    for path in files:
        if path.startswith(("insights/", "known_issues/", "rules/")):
            assert path in file_hashes, f"{path} missing from file_hashes"
            assert len(file_hashes[path]) == 64, "sha256 hex digest must be 64 chars"

    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"
    dec_file = knowledge_dir / "decisions" / "decision_log.jsonl"
    dec_entry = json.loads(dec_file.read_text(encoding="utf-8").splitlines()[-1])

    sync_result = [e for e in events if e["event_type"] == "knowledge_sync_result"][-1]
    assert sync_result["details"]["decision_log_entry"] == dec_entry


def test_revert_function_exists_and_is_callable(mock_workspace_for_knowledge: Path):
    """AC1: a revert entrypoint exists that takes a session_id and returns without raising."""
    _sync_default(mock_workspace_for_knowledge)

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    result = revert_workflow.run("session_know_01")

    assert result["status"] == "REVERTED"
    assert result["session_id"] == "session_know_01"


def test_revert_removes_exact_files_written(mock_workspace_for_knowledge: Path):
    """AC2: revert removes exactly the files listed in files_written — no more, no less."""
    from src.lab.audit import LabAuditTrail

    _sync_default(mock_workspace_for_knowledge)

    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"
    sentinel = knowledge_dir / "insights" / "zzz_sentinel.json"
    sentinel.write_text("{}", encoding="utf-8")

    trail = LabAuditTrail(mock_workspace_for_knowledge)
    events = trail.read_log("session_know_01")
    files_written = [e for e in events if e["event_type"] == "files_written"][-1]
    target_files = [
        f for f in files_written["details"]["files"]
        if f != "decisions/decision_log.jsonl" and not Path(f).is_absolute()
    ]
    assert target_files, "expected at least one insight/known_issue/rule target file"

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    result = revert_workflow.run("session_know_01")

    assert result["status"] == "REVERTED"
    for rel_path in target_files:
        assert not (knowledge_dir / rel_path).is_file(), f"{rel_path} should have been removed"

    assert sentinel.is_file(), "unrelated sentinel file must survive revert untouched"

    report_glob = list(
        (mock_workspace_for_knowledge / "data" / "lab_sessions" / "session_know_01" / "enhancement").glob(
            "knowledge_update_report.md"
        )
    )
    assert report_glob, "report_path is explicitly out of scope and must not be removed by revert"


def test_revert_fixes_known_issues_and_rules_omission(mock_workspace_for_knowledge: Path):
    """Regression test for the investigation's 'New Finding': known_issues/rules files must be
    both recorded in files_written and actually deleted by revert, not just the insight file."""
    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"

    _sync_default(mock_workspace_for_knowledge)

    issue_files = list((knowledge_dir / "known_issues").glob("*.json"))
    rule_files = list((knowledge_dir / "rules").glob("*.json"))
    assert issue_files, "fixture must produce at least one known_issues file"
    assert rule_files, "fixture must produce at least one rules file"

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    result = revert_workflow.run("session_know_01")

    assert result["status"] == "REVERTED"
    for f in issue_files:
        assert not f.is_file(), f"known_issues file {f.name} must be removed by revert"
    for f in rule_files:
        assert not f.is_file(), f"rules file {f.name} must be removed by revert"


def test_revert_decision_log_removes_only_matching_line(mock_workspace_for_knowledge: Path):
    """AC2: revert removes exactly the one decision-log line belonging to the reverted sync,
    leaving other sessions' lines byte-for-byte intact (append-only, multi-session file)."""
    from src.lab.session import LabSessionStore

    _sync_default(mock_workspace_for_knowledge, decision_note="First session decision")

    # Simulate a second session's decision appended afterward, sharing the same file.
    session_store = LabSessionStore(mock_workspace_for_knowledge / "data" / "lab_sessions")
    session_store.create_session("session_know_02")
    decision_file = mock_workspace_for_knowledge / "data" / "lab_knowledge" / "decisions" / "decision_log.jsonl"
    other_entry = {
        "session_id": "session_know_02",
        "decision_note": "Second session decision",
        "approved_by": "user_other",
        "timestamp": "2026-07-05T00:00:00+00:00",
    }
    with open(decision_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(other_entry) + "\n")

    lines_before = decision_file.read_text(encoding="utf-8").splitlines()
    assert len(lines_before) == 2

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    result = revert_workflow.run("session_know_01")
    assert result["status"] == "REVERTED"

    lines_after = decision_file.read_text(encoding="utf-8").splitlines()
    assert len(lines_after) == 1
    remaining_entry = json.loads(lines_after[0])
    assert remaining_entry == other_entry, "the other session's line must survive byte-for-byte"


def test_revert_rejects_superseded_known_issue(mock_workspace_for_knowledge: Path):
    """AC3: reverting a sync whose known_issues file was silently overwritten by a later sync
    (no duplicate guard exists for known_issues/rules, unlike insights) must be rejected."""
    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"

    _sync_default(mock_workspace_for_knowledge)

    issue_files = list((knowledge_dir / "known_issues").glob("*.json"))
    assert issue_files, "fixture must produce a known_issues file"
    issue_file = issue_files[0]

    superseded_content = json.dumps({"issue_id": "SUPERSEDED", "status": "STORED"}, indent=2)
    issue_file.write_text(superseded_content, encoding="utf-8")

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    with pytest.raises(LabKnowledgeRevertError) as exc:
        revert_workflow.run("session_know_01")
    assert "modified by a later operation" in str(exc.value)

    # The superseding content must be untouched by the rejected revert attempt.
    assert issue_file.read_text(encoding="utf-8") == superseded_content


def test_revert_rejects_superseded_rule(mock_workspace_for_knowledge: Path):
    """AC3 mirror case: a ScenarioSpec/WorldSpec rules/*.json file silently overwritten by a
    later sync must also reject revert."""
    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"

    _sync_default(mock_workspace_for_knowledge)

    rule_files = list((knowledge_dir / "rules").glob("*.json"))
    assert rule_files, "fixture must produce a rules file"
    rule_file = rule_files[0]

    superseded_content = json.dumps({"patch_id": "SUPERSEDED", "target_type": "ScenarioSpec"}, indent=2)
    rule_file.write_text(superseded_content, encoding="utf-8")

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    with pytest.raises(LabKnowledgeRevertError) as exc:
        revert_workflow.run("session_know_01")
    assert "modified by a later operation" in str(exc.value)
    assert rule_file.read_text(encoding="utf-8") == superseded_content


def test_revert_rejection_does_not_log_false_success(mock_workspace_for_knowledge: Path):
    """AC4: a rejected (superseded) revert must never log a knowledge_reverted success event."""
    from src.lab.audit import LabAuditTrail

    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"
    _sync_default(mock_workspace_for_knowledge)

    issue_file = list((knowledge_dir / "known_issues").glob("*.json"))[0]
    issue_file.write_text(json.dumps({"issue_id": "SUPERSEDED"}), encoding="utf-8")

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    with pytest.raises(LabKnowledgeRevertError):
        revert_workflow.run("session_know_01")

    trail = LabAuditTrail(mock_workspace_for_knowledge)
    events = trail.read_log("session_know_01")
    assert not any(e["event_type"] == "knowledge_reverted" for e in events), (
        "a rejected revert must never log a knowledge_reverted success event"
    )


def test_revert_logs_audit_event(mock_workspace_for_knowledge: Path):
    """AC4: a successful revert is logged to audit_log.jsonl as a new 'knowledge_reverted' event
    naming the files actually removed."""
    from src.lab.audit import LabAuditTrail

    _sync_default(mock_workspace_for_knowledge)

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    result = revert_workflow.run("session_know_01")

    trail = LabAuditTrail(mock_workspace_for_knowledge)
    events = trail.read_log("session_know_01")
    reverted_events = [e for e in events if e["event_type"] == "knowledge_reverted"]
    assert reverted_events, "knowledge_reverted event must be written to audit trail"
    assert reverted_events[-1]["details"]["removed_files"] == result["removed_files"]


def test_revert_nothing_to_revert_for_no_insights_sync(mock_workspace_empty_insights: Path):
    """A NO_INSIGHTS sync wrote nothing, so revert must no-op cleanly rather than error."""
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
    assert res["status"] == "NO_INSIGHTS"

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_empty_insights)
    result = revert_workflow.run("session_know_01")

    assert result == {
        "status": "NOTHING_TO_REVERT",
        "session_id": "session_know_01",
        "removed_files": [],
    }


def test_revert_rejects_legacy_log_missing_hash_keys(mock_workspace_for_knowledge: Path):
    """Step 2b legacy-log guard: an audit_log.jsonl written before this ticket's Step 1 lands has
    files_written/knowledge_sync_result events without file_hashes/decision_log_entry — revert
    must raise LabKnowledgeRevertError instead of letting a bare KeyError propagate or attempting
    a best-effort partial revert."""
    from src.lab.session import LabSessionStore

    session_store = LabSessionStore(mock_workspace_for_knowledge / "data" / "lab_sessions")
    session_store.create_session("session_legacy_01")

    session_dir = mock_workspace_for_knowledge / "data" / "lab_sessions" / "session_legacy_01"
    audit_file = session_dir / "audit_log.jsonl"
    legacy_events = [
        {
            "timestamp": "2026-05-24T10:00:00Z",
            "event_type": "files_written",
            "details": {
                "files": [
                    "/abs/path/knowledge_update_report.md",
                    "decision_log.jsonl",
                    "insights/insight-legacy.json",
                ]
            },
        },
        {
            "timestamp": "2026-05-24T10:00:01Z",
            "event_type": "knowledge_sync_result",
            "details": {"status": "SYNCED", "synced_insights": 1, "synced_patches": 0},
        },
    ]
    with open(audit_file, "w", encoding="utf-8") as f:
        for event in legacy_events:
            f.write(json.dumps(event) + "\n")

    knowledge_dir = mock_workspace_for_knowledge / "data" / "lab_knowledge"
    insights_dir = knowledge_dir / "insights"
    insights_dir.mkdir(parents=True, exist_ok=True)
    legacy_insight = insights_dir / "insight-legacy.json"
    legacy_insight.write_text("{}", encoding="utf-8")

    revert_workflow = RevertSimulationKnowledgeWorkflow(workspace_root=mock_workspace_for_knowledge)
    with pytest.raises(LabKnowledgeRevertError) as exc:
        revert_workflow.run("session_legacy_01")
    assert "predates hash-tracking support" in str(exc.value)

    # No file may be touched by a rejected legacy-format revert.
    assert legacy_insight.is_file()
