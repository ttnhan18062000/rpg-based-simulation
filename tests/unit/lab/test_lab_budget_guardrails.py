import pytest
import logging
import json
import sys
import os
import shutil
from pathlib import Path
from unittest.mock import patch
from src.lab.schema import (
    ExperimentSpec,
    ScenarioSpec,
    ExperimentBudgetsSpec,
    ExperimentRunSpec,
    ExperimentObservabilitySpec,
    ExperimentAnalysisSpec,
    ExperimentRetentionSpec,
    IntentSpec,
    RequiredSignalsSpec
)
from src.worldbuilding.schema import WorldSpec
from src.lab.guardrails import (
    LabBudgetGuardrails,
    BudgetBlockedError,
    BudgetWarningError,
    BudgetCheckResult,
    BudgetEstimation
)
from src.lab.orchestrator import ScenarioLabOrchestrator
from src.worldbuilding.repository import WorldRepository
from src.lab.repository import ScenarioRepository, ExperimentRepository, LabRunRepository

@pytest.fixture(autouse=True)
def mock_simulation_loop():
    """Globally mocks simulation compiler and kernel execution to make tests run instantly."""
    with patch("src.worldbuilding.compiler.WorldCompiler.compile") as mock_compile, \
         patch("src.engine.kernel.Kernel") as mock_kernel_class:
         
        mock_kernel = mock_kernel_class.return_value
        mock_kernel.tick_once.return_value = None
        mock_kernel.shutdown.return_value = None
        
        def side_effect(*args, **kwargs):
            # Inspect stack to find caller's run_id and write mock report
            try:
                frame = sys._getframe(1)
                run_id = frame.f_locals.get("run_id")
                if run_id:
                    temp_run_dir = os.path.abspath(os.path.join("data/runs", run_id))
                    os.makedirs(temp_run_dir, exist_ok=True)
                    with open(os.path.join(temp_run_dir, "run_report.json"), "w") as f:
                        json.dump({"health_score": 100.0, "critical_count": 0, "warning_count": 0, "anomalies": []}, f)
            except Exception:
                pass
            return (None, None)
            
        mock_compile.side_effect = side_effect
        yield

@pytest.fixture
def base_world_spec() -> WorldSpec:
    return WorldSpec(
        schema_version="worldspec.v1",
        world_id="test_world",
        name="Test World",
        topology={"width": 10, "height": 10, "coordinate_system": "grid"},
        regions=[{"id": "spawn_region", "type": "grassland", "bounds": [0, 0, 4, 4]}],
        factions=[{"id": "test_faction", "type": "basic"}],
        entities=[{"id": "pop1", "count": 5, "role": "worker", "faction": "test_faction", "spawn_region": "spawn_region"}],
        resources=[],
        validation={"expected_min_entities": 1, "allow_overlapping_regions": False}
    )

@pytest.fixture
def base_scenario_spec() -> ScenarioSpec:
    return ScenarioSpec(
        schema_version="scenariospec.v1",
        scenario_id="test_scenario",
        name="Test Scenario",
        scenario_type="health_sweep",
        world_id="test_world",
        intent={"primary_goal": "test_goal", "description": "intent description"},
        expected_behavior={"health_score": {"min": 50.0}},
        required_signals={"metrics": ["health_score"]},
        allowed_anomalies=[],
        critical_anomalies=[],
        tags=[]
    )

@pytest.fixture
def base_experiment_spec() -> ExperimentSpec:
    return ExperimentSpec(
        schema_version="experimentspec.v1",
        experiment_id="test_experiment",
        scenario_id="test_scenario",
        experiment_type="multi_seed_sweep",
        run={"ticks": 100, "seeds": [1, 2], "repeat_count": 1, "max_parallel_runs": 1},
        observability={"mode": "LIGHTWEIGHT", "record_events": True, "record_metric_windows": True, "record_cognition": False},
        analysis={"run_post_analysis": True, "generate_report": True, "run_mining": False, "compare_baseline": False},
        retention={"keep_raw_events": True, "keep_reports": True, "max_artifact_mb": 500},
        budgets={"max_runtime_minutes": 60, "max_total_artifact_mb": 2000, "max_runs": 100, "max_total_ticks": 1000000}
    )

def test_small_experiment_passes_budget_check(base_world_spec, base_experiment_spec):
    """Verify that a standard small experiment is OK and passes check successfully."""
    guardrails = LabBudgetGuardrails(profile="local_dev")
    est = guardrails.estimate(base_experiment_spec, base_world_spec)
    assert est.run_count == 2
    assert est.total_ticks == 200
    assert est.expected_entity_count == 5
    
    check_res = guardrails.check(est, base_experiment_spec)
    assert check_res.is_ok
    assert len(check_res.warnings) == 0
    assert len(check_res.blocked_reasons) == 0

def test_huge_run_count_triggers_warning_and_block(base_world_spec, base_experiment_spec):
    """Verify that excessive runs configuration triggers WARNING and BLOCKED thresholds."""
    # 1. WARNING trigger (> 50 runs in local_dev)
    spec_warn = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=10, seeds=list(range(51)), repeat_count=1)
    })
    
    guardrails = LabBudgetGuardrails(profile="local_dev")
    est_warn = guardrails.estimate(spec_warn, base_world_spec)
    check_warn = guardrails.check(est_warn, spec_warn)
    assert check_warn.is_warning
    assert any("Run count" in w and "high" in w for w in check_warn.warnings)
    
    # 2. BLOCKED trigger (> 100 runs in local_dev)
    spec_block = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=10, seeds=list(range(101)), repeat_count=1)
    })
    
    est_block = guardrails.estimate(spec_block, base_world_spec)
    check_block = guardrails.check(est_block, spec_block)
    assert check_block.is_blocked
    assert any("Run count" in b and "exceeds limit" in b for b in check_block.blocked_reasons)

def test_huge_total_ticks_triggers_warning_and_block(base_world_spec, base_experiment_spec):
    """Verify that excessive ticks configuration triggers WARNING and BLOCKED thresholds."""
    # 1. WARNING trigger (> 50000 ticks in local_dev)
    spec_warn = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=30000, seeds=[1, 2], repeat_count=1) # 60,000 ticks
    })
    
    guardrails = LabBudgetGuardrails(profile="local_dev")
    est_warn = guardrails.estimate(spec_warn, base_world_spec)
    check_warn = guardrails.check(est_warn, spec_warn)
    assert check_warn.is_warning
    assert any("Total ticks" in w and "high" in w for w in check_warn.warnings)
    
    # 2. BLOCKED trigger (> 100000 ticks in local_dev)
    spec_block = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=60000, seeds=[1, 2], repeat_count=1) # 120,000 ticks
    })
    
    est_block = guardrails.estimate(spec_block, base_world_spec)
    check_block = guardrails.check(est_block, spec_block)
    assert check_block.is_blocked
    assert any("Total ticks" in b and "exceeds limit" in b for b in check_block.blocked_reasons)

def test_artifact_budget_estimate_triggers_warning(base_world_spec, base_experiment_spec):
    """Verify that estimated artifact size exceeding experiment budget triggers warning."""
    spec = base_experiment_spec.model_copy(update={
        "budgets": ExperimentBudgetsSpec(max_runtime_minutes=60, max_total_artifact_mb=1),
        "run": ExperimentRunSpec(ticks=5000, seeds=[1, 2], repeat_count=1) # 10,000 total ticks, 5 entities -> ~5 MB footprint
    })
    
    guardrails = LabBudgetGuardrails(profile="local_dev")
    est = guardrails.estimate(spec, base_world_spec)
    check_res = guardrails.check(est, spec)
    assert check_res.is_warning or check_res.is_blocked
    assert any("artifact size" in w and "exceeds experiment budget" in w for w in check_res.warnings)

def test_ci_profile_blocks_oversized_experiment(base_world_spec, base_experiment_spec):
    """Verify that CI profile strictly blocks oversized runs, completely ignoring force/confirm."""
    spec = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=100, seeds=list(range(21)), repeat_count=1)
    })
    
    guardrails = LabBudgetGuardrails(profile="CI")
    est = guardrails.estimate(spec, base_world_spec)
    check_res = guardrails.check(est, spec)
    assert check_res.is_blocked

def test_local_profile_requires_confirmation_for_warning(tmp_path, base_world_spec, base_scenario_spec, base_experiment_spec):
    """Verify that warnings in local profile raise BudgetWarningError unless confirm=True."""
    worlds_dir = tmp_path / "worlds"
    scenarios_dir = tmp_path / "scenarios"
    experiments_dir = tmp_path / "experiments"
    lab_runs_dir = tmp_path / "lab_runs"
    worlds_dir.mkdir()
    scenarios_dir.mkdir()
    experiments_dir.mkdir()
    lab_runs_dir.mkdir()
    
    import yaml
    w_dir = worlds_dir / base_world_spec.world_id
    w_dir.mkdir()
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(base_world_spec.model_dump(), f)
    s_dir = scenarios_dir / base_scenario_spec.scenario_id
    s_dir.mkdir()
    with open(s_dir / "scenario.yaml", "w") as f:
        yaml.safe_dump(base_scenario_spec.model_dump(), f)
        
    # Setup warning spec (>50 runs)
    spec_warn = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=10, seeds=list(range(55)), repeat_count=1)
    })
    e_dir = experiments_dir / spec_warn.experiment_id
    e_dir.mkdir()
    with open(e_dir / "experiment.yaml", "w") as f:
        yaml.safe_dump(spec_warn.model_dump(), f)
        
    world_repo = WorldRepository(str(worlds_dir))
    scenario_repo = ScenarioRepository(str(scenarios_dir))
    experiment_repo = ExperimentRepository(str(experiments_dir))
    lab_run_repo = LabRunRepository(str(lab_runs_dir))
    
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
    
    # 1. Should raise BudgetWarningError when confirm=False
    with pytest.raises(BudgetWarningError) as exc_info:
        orchestrator.run_lab(spec_warn.experiment_id, "run_warn_fail", profile="local_dev", confirm=False)
    assert "Execution requires confirmation" in str(exc_info.value)
    
    # 2. Should pass when confirm=True
    manifest = orchestrator.run_lab(spec_warn.experiment_id, "run_warn_success", profile="local_dev", confirm=True)
    assert manifest.status in ["COMPLETED", "RUNNING", "PARTIAL"]

def test_force_flag_is_audited(caplog, tmp_path, base_world_spec, base_scenario_spec, base_experiment_spec):
    """Verify that using --force for blocked runs writes an audit log message."""
    worlds_dir = tmp_path / "worlds"
    scenarios_dir = tmp_path / "scenarios"
    experiments_dir = tmp_path / "experiments"
    lab_runs_dir = tmp_path / "lab_runs"
    worlds_dir.mkdir()
    scenarios_dir.mkdir()
    experiments_dir.mkdir()
    lab_runs_dir.mkdir()
    
    import yaml
    w_dir = worlds_dir / base_world_spec.world_id
    w_dir.mkdir()
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(base_world_spec.model_dump(), f)
    s_dir = scenarios_dir / base_scenario_spec.scenario_id
    s_dir.mkdir()
    with open(s_dir / "scenario.yaml", "w") as f:
        yaml.safe_dump(base_scenario_spec.model_dump(), f)
        
    # Setup blocked spec (>100 runs)
    spec_block = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=10, seeds=list(range(105)), repeat_count=1)
    })
    e_dir = experiments_dir / spec_block.experiment_id
    e_dir.mkdir()
    with open(e_dir / "experiment.yaml", "w") as f:
        yaml.safe_dump(spec_block.model_dump(), f)
        
    world_repo = WorldRepository(str(worlds_dir))
    scenario_repo = ScenarioRepository(str(scenarios_dir))
    experiment_repo = ExperimentRepository(str(experiments_dir))
    lab_run_repo = LabRunRepository(str(lab_runs_dir))
    
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
    
    # Verify that without force it fails
    with pytest.raises(BudgetBlockedError):
        orchestrator.run_lab(spec_block.experiment_id, "run_block_fail", profile="local_dev", force=False)
        
    # Verify that with force it prints AUDIT log
    with caplog.at_level(logging.WARNING):
        manifest = orchestrator.run_lab(spec_block.experiment_id, "run_block_force", profile="local_dev", force=True)
        assert manifest.status in ["COMPLETED", "RUNNING", "PARTIAL"]
        assert any("[AUDIT]" in record.message and "bypassed via --force" in record.message for record in caplog.records)

def test_blocked_experiment_does_not_create_partial_run_artifacts(tmp_path, base_world_spec, base_scenario_spec, base_experiment_spec):
    """Verify that a blocked experiment aborts before creating any directory structures or manifests."""
    worlds_dir = tmp_path / "worlds"
    scenarios_dir = tmp_path / "scenarios"
    experiments_dir = tmp_path / "experiments"
    lab_runs_dir = tmp_path / "lab_runs"
    worlds_dir.mkdir()
    scenarios_dir.mkdir()
    experiments_dir.mkdir()
    lab_runs_dir.mkdir()
    
    import yaml
    w_dir = worlds_dir / base_world_spec.world_id
    w_dir.mkdir()
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(base_world_spec.model_dump(), f)
    s_dir = scenarios_dir / base_scenario_spec.scenario_id
    s_dir.mkdir()
    with open(s_dir / "scenario.yaml", "w") as f:
        yaml.safe_dump(base_scenario_spec.model_dump(), f)
        
    # Blocked spec (>100 runs)
    spec_block = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=10, seeds=list(range(105)), repeat_count=1)
    })
    e_dir = experiments_dir / spec_block.experiment_id
    e_dir.mkdir()
    with open(e_dir / "experiment.yaml", "w") as f:
        yaml.safe_dump(spec_block.model_dump(), f)
        
    world_repo = WorldRepository(str(worlds_dir))
    scenario_repo = ScenarioRepository(str(scenarios_dir))
    experiment_repo = ExperimentRepository(str(experiments_dir))
    lab_run_repo = LabRunRepository(str(lab_runs_dir))
    
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
    
    # Run blocked execution
    with pytest.raises(BudgetBlockedError):
        orchestrator.run_lab(spec_block.experiment_id, "run_block_folder_test", profile="local_dev", force=False)
        
    # Verify no folder was created in lab runs directory
    created_folders = list(lab_runs_dir.iterdir())
    assert len(created_folders) == 0

def test_budget_warning_appears_in_lab_summary(tmp_path, base_world_spec, base_scenario_spec, base_experiment_spec):
    """Verify that triggered budget warnings are written to lab_summary.json and lab_summary.md scorecard."""
    worlds_dir = tmp_path / "worlds"
    scenarios_dir = tmp_path / "scenarios"
    experiments_dir = tmp_path / "experiments"
    lab_runs_dir = tmp_path / "lab_runs"
    worlds_dir.mkdir()
    scenarios_dir.mkdir()
    experiments_dir.mkdir()
    lab_runs_dir.mkdir()
    
    import yaml
    w_dir = worlds_dir / base_world_spec.world_id
    w_dir.mkdir()
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(base_world_spec.model_dump(), f)
    s_dir = scenarios_dir / base_scenario_spec.scenario_id
    s_dir.mkdir()
    with open(s_dir / "scenario.yaml", "w") as f:
        yaml.safe_dump(base_scenario_spec.model_dump(), f)
        
    # Setup warning spec (>50 runs)
    spec_warn = base_experiment_spec.model_copy(update={
        "run": ExperimentRunSpec(ticks=10, seeds=list(range(55)), repeat_count=1)
    })
    e_dir = experiments_dir / spec_warn.experiment_id
    e_dir.mkdir()
    with open(e_dir / "experiment.yaml", "w") as f:
        yaml.safe_dump(spec_warn.model_dump(), f)
        
    world_repo = WorldRepository(str(worlds_dir))
    scenario_repo = ScenarioRepository(str(scenarios_dir))
    experiment_repo = ExperimentRepository(str(experiments_dir))
    lab_run_repo = LabRunRepository(str(lab_runs_dir))
    
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
    
    # Run with confirm=True
    manifest = orchestrator.run_lab(spec_warn.experiment_id, "run_warn_summary_check", profile="local_dev", confirm=True)
        
    # Check that summary JSON exists and contains the warning
    summary_json_path = lab_runs_dir / "run_warn_summary_check" / "lab_summary.json"
    assert summary_json_path.is_file()
    with open(summary_json_path, "r", encoding="utf-8") as f:
        summary_data = json.load(f)
    assert "budget_warnings" in summary_data
    assert len(summary_data["budget_warnings"]) > 0
    assert any("Run count" in w for w in summary_data["budget_warnings"])
    
    # Check that summary MD scorecard has budget warning section
    summary_md_path = lab_runs_dir / "run_warn_summary_check" / "lab_summary.md"
    assert summary_md_path.is_file()
    with open(summary_md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    assert "Budget Guardrail Warnings triggered for this run:" in md_content
    assert "Run count" in md_content
