import json
import pytest
import os
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import GenerateSimulationSetupWorkflow, PrepareSimulationExecutionWorkflow

@pytest.fixture
def mock_workspace_with_draft(tmp_path: Path) -> Path:
    """Sets up a complete workspace containing a pre-generated draft session."""
    (tmp_path / "data" / "worlds").mkdir(parents=True)
    (tmp_path / "data" / "scenarios").mkdir(parents=True)
    (tmp_path / "data" / "experiments").mkdir(parents=True)
    (tmp_path / "data" / "runs").mkdir(parents=True)
    (tmp_path / "data" / "issues").mkdir(parents=True)
    (tmp_path / "docs" / "mechanics").mkdir(parents=True)
    
    with open(tmp_path / "data" / "worlds" / "world_index.json", "w") as f:
        json.dump({}, f)
    with open(tmp_path / "data" / "scenarios" / "scenario_index.json", "w") as f:
        json.dump({}, f)
    with open(tmp_path / "data" / "experiments" / "experiment_index.json", "w") as f:
        json.dump({}, f)

    (tmp_path / "docs" / "mechanics" / "worldbuilding_rules.md").write_text("Rule: Must have regions.", encoding="utf-8")
    (tmp_path / "docs" / "mechanics" / "testing_principles.md").write_text("Principle: Safe runs.", encoding="utf-8")

    # Generate the draft specs
    sessions_dir = tmp_path / "data" / "lab_sessions"
    store = LabSessionStore(sessions_dir)
    store.create_session("session_prep_01")

    gen_request = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="generic",
        user_goal="Standard healthy verification run",
        constraints={"budget_profile": "local_dev"}
    )
    GenerateSimulationSetupWorkflow(workspace_root=tmp_path).run("session_prep_01", gen_request)
    return tmp_path

def test_prepare_execution_generates_command_script(mock_workspace_with_draft: Path):
    """Verify standard execution prep writes launch script, readiness reports, and enforces chmod."""
    request = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="generic",
        user_goal="Verify setup",
        constraints={"budget_profile": "local_dev"}
    )

    workflow = PrepareSimulationExecutionWorkflow(workspace_root=mock_workspace_with_draft)
    res = workflow.run("session_prep_01", request)

    assert res["status"] == "READY"
    assert "execution_command.sh" in res["command_script_path"]

    # Verify script existence and permissions
    support_dir = mock_workspace_with_draft / "data" / "lab_sessions" / "session_prep_01" / "execution_support"
    script_path = support_dir / "execution_command.sh"
    
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK)

    script_content = script_path.read_text(encoding="utf-8")
    assert "rpg-lab run" in script_content
    assert "--experiment" in script_content
    assert "local_dev" in script_content

    # Verify readiness reports exist
    assert (support_dir / "execution_readiness_report.md").is_file()
    assert (support_dir / "execution_readiness_report.json").is_file()
    assert (support_dir / "expected_output_paths.json").is_file()
    
    with open(support_dir / "execution_readiness_report.json", "r") as f:
        readiness_json = json.load(f)
        assert readiness_json["status"] == "READY"
        assert readiness_json["budget_check_status"] == "OK"

def test_validator_failure_blocks_execution(mock_workspace_with_draft: Path):
    """Verify that writing invalid draft specifications blocks launcher script compilation."""
    gen_dir = mock_workspace_with_draft / "data" / "lab_sessions" / "session_prep_01" / "generation"
    scenario_yaml = gen_dir / "draft_specs" / "scenario.yaml"
    
    # Intentionally corrupt scenario specification content
    scenario_yaml.write_text("invalid yaml text properties schema", encoding="utf-8")

    request = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="generic",
        user_goal="Verify validator failure",
        constraints={"budget_profile": "local_dev"}
    )

    workflow = PrepareSimulationExecutionWorkflow(workspace_root=mock_workspace_with_draft)
    res = workflow.run("session_prep_01", request)

    assert res["status"] == "BLOCKED"
    assert "Validation failed" in res["reason"]

    support_dir = mock_workspace_with_draft / "data" / "lab_sessions" / "session_prep_01" / "execution_support"
    assert not (support_dir / "execution_command.sh").exists()
    assert (support_dir / "execution_blocked_report.md").is_file()
    
    blocked_pack = (support_dir / "execution_blocked_report.md").read_text(encoding="utf-8")
    assert "Execution Blocked Report" in blocked_pack
    assert "invalid yaml" in blocked_pack or "Specification validation checks failed" in blocked_pack

def test_concurrency_lock_blocks_execution(mock_workspace_with_draft: Path):
    """Verify that active execution lock blocks compilation and outputs conflict warning."""
    # Write a concurrent lock file
    lock_file = mock_workspace_with_draft / "data" / "runs" / "run.lock"
    lock_file.touch()

    request = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="generic",
        user_goal="Verify lock conflict",
        constraints={"budget_profile": "local_dev"}
    )

    workflow = PrepareSimulationExecutionWorkflow(workspace_root=mock_workspace_with_draft)
    res = workflow.run("session_prep_01", request)

    assert res["status"] == "BLOCKED"
    assert "Concurrent sweep block" in res["reason"]

    support_dir = mock_workspace_with_draft / "data" / "lab_sessions" / "session_prep_01" / "execution_support"
    assert not (support_dir / "execution_command.sh").exists()
    assert (support_dir / "execution_blocked_report.md").is_file()
    
    blocked_pack = (support_dir / "execution_blocked_report.md").read_text(encoding="utf-8")
    assert "Concurrent sweeps are forbidden" in blocked_pack

def test_ci_budget_block_prevents_script_creation(mock_workspace_with_draft: Path):
    """Verify that CI profile budget limit violations block script compilation."""
    # Generate large setup using specific input parameters
    specific_request = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="specific",
        specific_inputs={
            "world_type": "resource_valley",
            "regions": ["town", "quarry"],
            "workers": 50,
            "resources": ["stone"],
            "pressures": [],
            "ticks": 8000,
            # CI Limit for run count is 20, let's exceed that by using 25 seeds!
            "seeds": list(range(25)),
            "observability_mode": "STANDARD"
        },
        constraints={"budget_profile": "CI"}
    )
    GenerateSimulationSetupWorkflow(workspace_root=mock_workspace_with_draft).run("session_prep_01", specific_request)

    # Trigger Prepare on CI profile
    prep_request = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="specific",
        specific_inputs={
            "profile": "CI"
        }
    )

    workflow = PrepareSimulationExecutionWorkflow(workspace_root=mock_workspace_with_draft)
    res = workflow.run("session_prep_01", prep_request)

    assert res["status"] == "BLOCKED"
    assert "CI Profile budget limit violated" in res["reason"]

    support_dir = mock_workspace_with_draft / "data" / "lab_sessions" / "session_prep_01" / "execution_support"
    assert not (support_dir / "execution_command.sh").exists()
    assert (support_dir / "execution_blocked_report.md").is_file()

def test_absolute_path_traversal_blocked(mock_workspace_with_draft: Path):
    """Verify path traversal outside workspace triggers PermissionError safety block."""
    prep_request = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="specific",
        specific_inputs={
            "experiment_path": "../../../etc/passwd",
            "profile": "local_dev"
        }
    )

    workflow = PrepareSimulationExecutionWorkflow(workspace_root=mock_workspace_with_draft)
    
    with pytest.raises(PermissionError) as exc_info:
        workflow.run("session_prep_01", prep_request)
    assert "Path traversal blocked" in str(exc_info.value)


# ── Semantic assertions ──────────────────────────────────────────────────────

def test_command_references_generated_experiment_path(mock_workspace_with_draft: Path):
    """The generated command script must reference the actual experiment.yaml path produced by
    GenerateSimulationSetup, not a hardcoded placeholder."""
    request = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="generic",
        user_goal="Verify command path accuracy",
        constraints={"budget_profile": "local_dev"}
    )
    workflow = PrepareSimulationExecutionWorkflow(workspace_root=mock_workspace_with_draft)
    res = workflow.run("session_prep_01", request)
    assert res["status"] == "READY"

    support_dir = mock_workspace_with_draft / "data" / "lab_sessions" / "session_prep_01" / "execution_support"
    script_content = (support_dir / "execution_command.sh").read_text(encoding="utf-8")

    # The draft experiment YAML must have been written by GenerateSimulationSetup
    experiment_yaml = (
        mock_workspace_with_draft / "data" / "lab_sessions"
        / "session_prep_01" / "generation" / "draft_specs" / "experiment.yaml"
    )
    assert experiment_yaml.is_file(), "Draft experiment.yaml must exist before Prepare"
    # The command must reference the relative path to this file
    relative_str = str(experiment_yaml.relative_to(mock_workspace_with_draft))
    assert relative_str in script_content, (
        f"Command script must contain experiment path {relative_str!r}; got:\n{script_content}"
    )


def test_budget_estimate_run_count_reflects_seeds(mock_workspace_with_draft: Path):
    """storage_estimate.run_count in the readiness report must match the seeds count in the spec."""
    import yaml as _yaml
    request = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="generic",
        user_goal="Verify budget run count",
        constraints={"budget_profile": "local_dev"}
    )
    workflow = PrepareSimulationExecutionWorkflow(workspace_root=mock_workspace_with_draft)
    res = workflow.run("session_prep_01", request)
    assert res["status"] == "READY"

    experiment_yaml = (
        mock_workspace_with_draft / "data" / "lab_sessions"
        / "session_prep_01" / "generation" / "draft_specs" / "experiment.yaml"
    )
    with open(experiment_yaml, "r", encoding="utf-8") as f:
        spec = _yaml.safe_load(f)
    seed_count = len(spec["run"]["seeds"])

    support_dir = mock_workspace_with_draft / "data" / "lab_sessions" / "session_prep_01" / "execution_support"
    with open(support_dir / "execution_readiness_report.json", encoding="utf-8") as f:
        readiness = json.load(f)

    assert readiness["storage_estimate"]["run_count"] == seed_count, (
        f"Expected run_count={seed_count} (from seeds), "
        f"got {readiness['storage_estimate']['run_count']}"
    )
