import json
import pytest
from pathlib import Path
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.workflows import GenerateSimulationSetupWorkflow
from src.worldbuilding.schema import load_world_spec_from_yaml
from src.lab.schema import load_scenario_spec_from_yaml, load_experiment_spec_from_yaml

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Sets up empty directories and base index templates for integration tests."""
    (tmp_path / "data" / "worlds").mkdir(parents=True)
    (tmp_path / "data" / "scenarios").mkdir(parents=True)
    (tmp_path / "data" / "experiments").mkdir(parents=True)
    (tmp_path / "data" / "runs").mkdir(parents=True)
    (tmp_path / "data" / "issues").mkdir(parents=True)
    (tmp_path / "docs" / "mechanics").mkdir(parents=True)
    
    # Write empty catalog indexes
    with open(tmp_path / "data" / "worlds" / "world_index.json", "w") as f:
        json.dump({}, f)
    with open(tmp_path / "data" / "scenarios" / "scenario_index.json", "w") as f:
        json.dump({}, f)
    with open(tmp_path / "data" / "experiments" / "experiment_index.json", "w") as f:
        json.dump({}, f)
        
    # Write rule files
    (tmp_path / "docs" / "mechanics" / "worldbuilding_rules.md").write_text("Rule: Must have regions.", encoding="utf-8")
    (tmp_path / "docs" / "mechanics" / "testing_principles.md").write_text("Principle: Safe runs.", encoding="utf-8")

    # Create lab sessions store
    sessions_dir = tmp_path / "data" / "lab_sessions"
    store = LabSessionStore(sessions_dir)
    store.create_session("session_gen_01")
    return tmp_path

def test_generic_generation_creates_draft_specs(mock_workspace: Path):
    """Verify that a generic request dynamically resolves goals, creates spec YAMLs, and runs validations."""
    request = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="generic",
        user_goal="Create a large stress inflation economic setup",
        constraints={"budget_profile": "local_dev"}
    )
    
    workflow = GenerateSimulationSetupWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_gen_01", request)

    assert res["validation_passed"] is True
    assert res["budget_status"] == "OK"

    # Verify files created in stage folder
    stage_dir = mock_workspace / "data" / "lab_sessions" / "session_gen_01" / "generation"
    drafts_dir = stage_dir / "draft_specs"
    
    assert (drafts_dir / "world.yaml").is_file()
    assert (drafts_dir / "scenario.yaml").is_file()
    assert (drafts_dir / "experiment.yaml").is_file()

    # Load specs and verify compliance
    world_spec = load_world_spec_from_yaml(drafts_dir / "world.yaml")
    scenario_spec = load_scenario_spec_from_yaml(drafts_dir / "scenario.yaml")
    experiment_spec = load_experiment_spec_from_yaml(drafts_dir / "experiment.yaml")

    # Check generic dynamic heuristics applied (stress inflation goal -> large workers & ticks)
    assert world_spec.world_id == "world_session_gen_01"
    assert sum(e.count for e in world_spec.entities) == 300  # large stress heuristic
    assert experiment_spec.run.ticks == 5000                 # large stress heuristic
    assert "gold" in [r.resource_type for r in world_spec.resources]  # inflation/economy heuristic

    # 1. Duplication report
    assert (stage_dir / "duplication_report.json").is_file()
    # 2. Budget report
    assert (stage_dir / "budget_report.json").is_file()
    with open(stage_dir / "budget_report.json", "r") as f:
        rep = json.load(f)
        assert rep["status"] == "OK"
        assert rep["run_count"] == 1
        assert rep["total_ticks"] == 5000

    # 3. Review pack is created
    assert (stage_dir / "generation_review_pack.md").is_file()
    pack_text = (stage_dir / "generation_review_pack.md").read_text(encoding="utf-8")
    assert "Simulation Generation Review Pack" in pack_text
    assert "world_session_gen_01" in pack_text

    # CRITICAL: Confirm draft specs are NOT promoted to trusted production folders directly!
    production_worlds_dir = mock_workspace / "data" / "worlds"
    assert len(list(production_worlds_dir.glob("**/*.yaml"))) == 0

def test_specific_generation_respects_user_parameters(mock_workspace: Path):
    """Verify that specific mode parameters are exactly mapped to generated YAML specs."""
    request = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="specific",
        specific_inputs={
            "world_type": "resource_valley",
            "regions": ["town", "quarry"],
            "workers": 150,
            "resources": ["stone", "iron"],
            "pressures": ["inventory_full"],
            "ticks": 8000,
            "seeds": [11, 22],
            "observability_mode": "STANDARD"
        },
        constraints={"budget_profile": "CI"}
    )

    workflow = GenerateSimulationSetupWorkflow(workspace_root=mock_workspace)
    res = workflow.run("session_gen_01", request)

    assert res["validation_passed"] is True
    
    stage_dir = mock_workspace / "data" / "lab_sessions" / "session_gen_01" / "generation"
    drafts_dir = stage_dir / "draft_specs"
    
    world_spec = load_world_spec_from_yaml(drafts_dir / "world.yaml")
    scenario_spec = load_scenario_spec_from_yaml(drafts_dir / "scenario.yaml")
    experiment_spec = load_experiment_spec_from_yaml(drafts_dir / "experiment.yaml")

    # Verify custom parameters mapped
    assert set(r.id for r in world_spec.regions) == {"town", "quarry"}
    assert sum(e.count for e in world_spec.entities) == 150
    assert set(res.resource_type for res in world_spec.resources) == {"stone", "iron"}
    assert "inventory_full" in scenario_spec.allowed_anomalies
    assert experiment_spec.run.ticks == 8000
    assert experiment_spec.run.seeds == [11, 22]
    assert experiment_spec.observability.mode == "STANDARD"
