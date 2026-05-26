import json
import pytest
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.context import ContextPackBuilder

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Sets up a comprehensive mocked project workspace hierarchy for builder testing."""
    # Docs folder
    docs_dir = tmp_path / "docs" / "mechanics"
    docs_dir.mkdir(parents=True)
    
    # Write worldbuilding rules
    (docs_dir / "worldbuilding_rules.md").write_text("Rule 1: Resources must balance.\nRule 2: Workers require housing.", encoding="utf-8")
    (docs_dir / "testing_principles.md").write_text("Principle 1: Metamorphic checks.", encoding="utf-8")
    (docs_dir / "investigation_rules.md").write_text("Rule: Check for resource death rates.", encoding="utf-8")
    
    # Write known issues list
    known_issues = [
        {"id": "ISS-001", "title": "Economy Inflation", "description": "Gold piles up", "domain": "economy", "tags": ["economy", "stress"]},
        {"id": "ISS-002", "title": "Pathing Bottleneck", "description": "Workers get stuck", "domain": "movement", "tags": ["movement", "astar"]}
    ]
    with open(docs_dir / "known_issues.json", "w", encoding="utf-8") as f:
        json.dump(known_issues, f)

    # Data folder
    data_dir = tmp_path / "data"
    (data_dir / "worlds").mkdir(parents=True)
    (data_dir / "scenarios").mkdir(parents=True)
    (data_dir / "experiments").mkdir(parents=True)
    (data_dir / "runs").mkdir(parents=True)
    (data_dir / "issues").mkdir(parents=True)

    # Write indexes
    with open(data_dir / "worlds" / "world_index.json", "w", encoding="utf-8") as f:
        json.dump({"world_valley": {"size": "medium"}}, f)
    with open(data_dir / "scenarios" / "scenario_index.json", "w", encoding="utf-8") as f:
        json.dump({"scenario_harvest": {"workers": 50}}, f)
    with open(data_dir / "experiments" / "experiment_index.json", "w", encoding="utf-8") as f:
        json.dump({"exp_01": {"ticks": 1000}}, f)
    with open(data_dir / "runs" / "historical_setups.json", "w", encoding="utf-8") as f:
        json.dump([{"run_id": "run_old_01", "grade": "A"}], f)
        
    with open(data_dir / "issues" / "issue_index.json", "w", encoding="utf-8") as f:
        json.dump({"anomalies": ["ISS-001"]}, f)
    with open(data_dir / "issues" / "signal_coverage.json", "w", encoding="utf-8") as f:
        json.dump({"signals": ["gold_growth"]}, f)

    # Sessions store
    sessions_dir = data_dir / "lab_sessions"
    sessions_dir.mkdir(parents=True)
    
    # Initialize a mock session
    session_store = LabSessionStore(sessions_dir)
    session_store.create_session("session_001")
    
    session_dir = session_store.resolve_session_dir("session_001")
    
    # Write simulation result records into session
    reg_dir = session_dir / "registration"
    reg_dir.mkdir(parents=True, exist_ok=True)
    
    with open(reg_dir / "lab_summary.json", "w", encoding="utf-8") as f:
        json.dump({"completed_run_count": 2, "failed_run_count": 0, "status": "GREEN"}, f)
        
    with open(reg_dir / "missing_signals.json", "w", encoding="utf-8") as f:
        json.dump(["housing_demand"], f)

    # Create mock child runs (evidence folders)
    run_1_dir = reg_dir / "runs" / "run_001"
    run_1_dir.mkdir(parents=True, exist_ok=True)
    with open(run_1_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump({"run_id": "run_001", "score": 92.5}, f)
        
    # Write a heavy simulation_events.jsonl in the run directory (to make sure it's ignored!)
    (run_1_dir / "simulation_events.jsonl").write_text('{"event": "tick", "details": "worker moves"}\n' * 500, encoding="utf-8")

    run_2_dir = reg_dir / "runs" / "run_002"
    run_2_dir.mkdir(parents=True, exist_ok=True)
    with open(run_2_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump({"run_id": "run_002", "score": 88.1}, f)

    return tmp_path

def test_generation_context_aggregation(mock_workspace: Path):
    """Verify that build_generation_pack aggregates rule markdown files, catalogs, and filters issues."""
    request = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="generic",
        user_goal="Create an economy-focused stress test setup",
        constraints={"budget_profile": "local_dev"}
    )
    
    builder = ContextPackBuilder(mock_workspace)
    pack = builder.build_generation_pack("session_001", request)

    # Validate aggregated contents
    assert pack["session_id"] == "session_001"
    assert pack["user_goal"] == "Create an economy-focused stress test setup"
    assert pack["budget_profile"] == "local_dev"
    
    # 1. Indexes should be present
    assert "world_valley" in pack["indexes"]["worlds"]
    assert "scenario_harvest" in pack["indexes"]["scenarios"]
    assert "exp_01" in pack["indexes"]["experiments"]

    # 2. Markdown principles should be read
    assert "Rule 1: Resources must balance." in pack["rules"]["worldbuilding"]
    assert "Principle 1: Metamorphic checks." in pack["rules"]["testing_principles"]

    # 3. Tag-filtering known issues: user_goal has "economy" so ISS-001 (tagged "economy") matches, ISS-002 (movement) does not!
    issue_ids = [issue["id"] for issue in pack["known_issues"]]
    assert "ISS-001" in issue_ids
    assert "ISS-002" not in issue_ids

    # 4. Similar Historic Setups
    assert len(pack["similar_previous_setups"]) == 1
    assert pack["similar_previous_setups"][0]["run_id"] == "run_old_01"

    # Verify output files exist
    gen_dir = mock_workspace / "data" / "lab_sessions" / "session_001" / "generation"
    assert (gen_dir / "context_pack.json").is_file()
    assert (gen_dir / "context_pack.md").is_file()

def test_investigation_context_excludes_raw_logs(mock_workspace: Path):
    """Verify that build_investigation_pack compiles scorecards and strictly ignores simulation_events.jsonl."""
    request = WorkflowRequest(
        workflow="InvestigateSimulationResult",
        mode="generic",
        user_goal="Investigate balance anomalies"
    )

    builder = ContextPackBuilder(mock_workspace)
    pack = builder.build_investigation_pack("session_001", request)

    # Validate aggregate records
    assert pack["lab_summary"]["status"] == "GREEN"
    assert pack["lab_summary"]["completed_run_count"] == 2
    assert pack["missing_signal_report"] == ["housing_demand"]
    assert "anomalies" in pack["issue_index"]
    assert "signals" in pack["signal_coverage"]

    # Confirm Top N evidence scorecards are present
    assert len(pack["top_n_evidence_packs"]) == 2
    run_ids = [r["run_id"] for r in pack["top_n_evidence_packs"]]
    assert "run_001" in run_ids
    assert "run_002" in run_ids

    # CRITICAL: Confirm simulation_events.jsonl payload is NOT anywhere in the context pack
    pack_str = json.dumps(pack)
    assert "simulation_events.jsonl" not in pack_str
    assert "worker moves" not in pack_str

    # Verify outputs written
    invest_dir = mock_workspace / "data" / "lab_sessions" / "session_001" / "investigation"
    assert (invest_dir / "context_pack.json").is_file()
    assert (invest_dir / "context_pack.md").is_file()

def test_context_pack_limits(mock_workspace: Path):
    """Verify that the builder strictly respects limits and truncates arrays when limits are low."""
    request = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="generic",
        user_goal="stress setup"
    )
    builder = ContextPackBuilder(mock_workspace)
    
    # We ask to only load at most 0 historic runs
    pack = builder.build_generation_pack("session_001", request, limits={"max_previous_runs": 0})
    assert len(pack["similar_previous_setups"]) == 0

    # For investigation, we only load at most 1 evidence pack
    request_inv = WorkflowRequest(workflow="InvestigateSimulationResult", mode="generic", user_goal="investigate")
    pack_inv = builder.build_investigation_pack("session_001", request_inv, limits={"max_evidence_packs": 1})
    assert len(pack_inv["top_n_evidence_packs"]) == 1

def test_resilient_missing_index_warning(tmp_path: Path):
    """Verify that pointing the builder to a clean folder with no indexes produces safe warning logs, not crashes."""
    request = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="generic",
        user_goal="setup"
    )
    
    # Create session store under clean dir
    store = LabSessionStore(tmp_path / "lab_sessions")
    store.create_session("session_empty")

    builder = ContextPackBuilder(tmp_path, session_store=store)
    
    # Should complete without crashing!
    pack = builder.build_generation_pack("session_empty", request)
    assert pack["indexes"]["worlds"] == {}
    assert pack["indexes"]["scenarios"] == {}
    assert pack["indexes"]["experiments"] == {}
    assert pack["known_issues"] == []
    assert pack["similar_previous_setups"] == []
