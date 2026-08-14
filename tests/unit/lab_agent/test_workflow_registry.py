import pytest
from pathlib import Path
from src.lab.registry import WorkflowSkill, WorkflowRegistry

def test_scan_and_register_success(tmp_path: Path):
    """Verify scanning and parsing of valid YAML frontmatter contracts."""
    workflows_dir = tmp_path / "workflows"
    skills_dir = tmp_path / "skills"
    workflows_dir.mkdir()
    skills_dir.mkdir()

    # Create dummy workflow
    dummy_wf = workflows_dir / "test-workflow.md"
    dummy_wf.write_text("""---
name: TestWorkflow
description: "A test workflow"
allowed_actions:
  - action_1
  - action_2
forbidden_actions:
  - action_3
output_artifacts:
  - out.txt
---
# Content here
""", encoding="utf-8")

    # Create dummy skill
    skill_folder = skills_dir / "test-skill"
    skill_folder.mkdir()
    dummy_skill = skill_folder / "SKILL.md"
    dummy_skill.write_text("""---
name: test-skill
purpose: "A test skill"
allowed_actions:
  - skill_action
---
# Skill content
""", encoding="utf-8")

    registry = WorkflowRegistry(workflows_dir, skills_dir)
    registry.scan_and_register()

    # Verify lists
    assert registry.list_workflows() == ["TestWorkflow"]
    assert registry.list_skills() == ["test-skill"]

    # Verify workflow contract
    wf = registry.get_workflow("TestWorkflow")
    assert wf.name == "TestWorkflow"
    assert wf.purpose == "A test workflow"
    assert wf.allowed_actions == ["action_1", "action_2"]
    assert wf.forbidden_actions == ["action_3"]
    assert wf.output_artifacts == ["out.txt"]
    assert wf.approval_required is False
    assert wf.failure_behavior == "STOP"

    # Verify skill contract
    sk = registry.get_skill("test-skill")
    assert sk.name == "test-skill"
    assert sk.purpose == "A test skill"
    assert sk.allowed_actions == ["skill_action"]
    assert sk.forbidden_actions == []

def test_workflow_fields_validation():
    """Verify that defaults are populated and description is correctly mapped to purpose."""
    contract = WorkflowSkill(
        name="Test",
        description="Dynamic purpose mapping",
        allowed_actions=["act"]
    )
    assert contract.name == "Test"
    assert contract.purpose == "Dynamic purpose mapping"
    assert contract.allowed_actions == ["act"]
    assert contract.forbidden_actions == []
    assert contract.input_schema == {}
    assert contract.context_budget == {}

def test_unknown_workflow_rejected(tmp_path: Path):
    """Verify ValueError is raised when querying unregistered commands."""
    registry = WorkflowRegistry(tmp_path, tmp_path)
    registry.scan_and_register()

    with pytest.raises(ValueError) as excinfo:
        registry.get_workflow("UnknownWorkflow")
    assert "Unknown or unregistered workflow command" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        registry.get_skill("unknown-skill")
    assert "Unknown or unregistered skill" in str(excinfo.value)

def test_real_registry_contracts():
    """Verify workflow contract parsing against a frozen snapshot of the real Phase 14
    contracts — decoupled from live .agents/ per TCK-20260721-AGENTS-DIR-DISPOSITION,
    which classifies .agents/workflows/ as archive-retire."""
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    workflows_dir = fixtures_dir / "agents_workflows"
    skills_dir = fixtures_dir / "agents_skills"

    registry = WorkflowRegistry(workflows_dir, skills_dir)
    registry.scan_and_register()

    # Check that real workflows are successfully parsed
    real_workflows = registry.list_workflows()
    assert "GenerateSimulationSetup" in real_workflows
    assert "PrepareSimulationExecution" in real_workflows

    # 1. Verify PrepareSimulationExecution action constraints
    prep_wf = registry.get_workflow("PrepareSimulationExecution")
    assert "resolve_specs" in prep_wf.allowed_actions
    assert "execute_simulation_command" in prep_wf.forbidden_actions
    assert "run_simulation_directly" in prep_wf.forbidden_actions

    # 2. Verify GenerateSimulationSetup action constraints
    gen_wf = registry.get_workflow("GenerateSimulationSetup")
    assert "create_draft_specs" in gen_wf.allowed_actions
    assert "run_simulation" in gen_wf.forbidden_actions
    assert "promote_trusted_specs" in gen_wf.forbidden_actions
    assert "update_rulebooks_directly" in gen_wf.forbidden_actions
