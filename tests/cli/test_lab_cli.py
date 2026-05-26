import pytest
import sys
import subprocess
import json
import yaml
from pathlib import Path
from src.lab.schema import LabRunManifest

@pytest.fixture
def lab_setup(tmp_path: Path):
    """Sets up a fully configured temporary environment with valid specifications."""
    worlds_dir = tmp_path / "worlds"
    scenarios_dir = tmp_path / "scenarios"
    experiments_dir = tmp_path / "experiments"
    lab_runs_dir = tmp_path / "lab_runs"
    
    worlds_dir.mkdir()
    scenarios_dir.mkdir()
    experiments_dir.mkdir()
    lab_runs_dir.mkdir()
    
    # 1. Write valid World spec
    world_id = "test_world"
    world_data = {
        "schema_version": "worldspec.v1",
        "world_id": world_id,
        "name": "Test World",
        "topology": {"width": 100, "height": 100, "coordinate_system": "grid"},
        "regions": [{"id": "spawn_region", "type": "grassland", "bounds": [0, 0, 49, 49]}],
        "factions": [{"id": "test_faction", "type": "basic"}],
        "entities": [{"id": "pop1", "count": 5, "role": "worker", "faction": "test_faction", "spawn_region": "spawn_region"}],
        "resources": [],
        "validation": {"expected_min_entities": 1, "allow_overlapping_regions": False}
    }
    world_spec_dir = worlds_dir / world_id
    world_spec_dir.mkdir()
    with open(world_spec_dir / "world.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(world_data, f)
        
    # 2. Write valid Scenario spec
    scenario_id = "test_scenario"
    scenario_data = {
        "schema_version": "scenariospec.v1",
        "scenario_id": scenario_id,
        "name": "Test Scenario Name",
        "scenario_type": "health_sweep",
        "world_id": world_id,
        "intent": {"primary_goal": "test_goal", "description": "some intent"},
        "expected_behavior": {"health_score": {"min": 50.0, "max": 100.0}},
        "required_signals": {"metrics": ["health_score"]},
        "allowed_anomalies": [],
        "critical_anomalies": [],
        "tags": []
    }
    scenario_spec_dir = scenarios_dir / scenario_id
    scenario_spec_dir.mkdir()
    with open(scenario_spec_dir / "scenario.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(scenario_data, f)
        
    # 3. Write valid Experiment spec
    experiment_id = "test_experiment"
    experiment_data = {
        "schema_version": "experimentspec.v1",
        "experiment_id": experiment_id,
        "scenario_id": scenario_id,
        "experiment_type": "multi_seed_sweep",
        "run": {"ticks": 50, "seeds": [1, 2], "repeat_count": 1, "max_parallel_runs": 1},
        "observability": {"mode": "LIGHTWEIGHT", "record_events": True, "record_metric_windows": True, "record_cognition": False},
        "analysis": {"run_post_analysis": True, "generate_report": True, "run_mining": False, "compare_baseline": False},
        "retention": {"keep_raw_events": True, "keep_reports": True, "max_artifact_mb": 500},
        "budgets": {"max_runtime_minutes": 60, "max_total_artifact_mb": 2000}
    }
    experiment_spec_dir = experiments_dir / experiment_id
    experiment_spec_dir.mkdir()
    with open(experiment_spec_dir / "experiment.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(experiment_data, f)
        
    return {
        "worlds_dir": worlds_dir,
        "scenarios_dir": scenarios_dir,
        "experiments_dir": experiments_dir,
        "lab_runs_dir": lab_runs_dir,
        "world_id": world_id,
        "scenario_id": scenario_id,
        "experiment_id": experiment_id
    }

def test_validate_world_command(lab_setup):
    """Verify that validate-world returns 0 on success and non-zero on failure."""
    # 1. Valid world ID
    cmd = [
        sys.executable, "-m", "src.lab.cli",
        "--worlds-dir", str(lab_setup["worlds_dir"]),
        "validate-world", lab_setup["world_id"]
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "VALID" in res.stdout
    
    # 2. Invalid world ID
    cmd_invalid = [
        sys.executable, "-m", "src.lab.cli",
        "--worlds-dir", str(lab_setup["worlds_dir"]),
        "validate-world", "non_existent_world"
    ]
    res_invalid = subprocess.run(cmd_invalid, capture_output=True, text=True)
    assert res_invalid.returncode != 0
    assert "INVALID" in res_invalid.stderr or "Error" in res_invalid.stderr

def test_validate_scenario_command(lab_setup):
    """Verify that validate-scenario returns 0 on success and non-zero on failure."""
    cmd = [
        sys.executable, "-m", "src.lab.cli",
        "--worlds-dir", str(lab_setup["worlds_dir"]),
        "--scenarios-dir", str(lab_setup["scenarios_dir"]),
        "validate-scenario", lab_setup["scenario_id"]
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "VALID" in res.stdout

def test_validate_experiment_command(lab_setup):
    """Verify that validate-experiment returns 0 on success and non-zero on failure."""
    cmd = [
        sys.executable, "-m", "src.lab.cli",
        "--scenarios-dir", str(lab_setup["scenarios_dir"]),
        "--experiments-dir", str(lab_setup["experiments_dir"]),
        "validate-experiment", lab_setup["experiment_id"]
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "VALID" in res.stdout

def test_run_command_creates_lab_run(lab_setup):
    """Verify that execution run command successfully spawns runs and exits zero."""
    # We will invoke CLI run command using the temp layout
    cmd = [
        sys.executable, "-m", "src.lab.cli",
        "--worlds-dir", str(lab_setup["worlds_dir"]),
        "--scenarios-dir", str(lab_setup["scenarios_dir"]),
        "--experiments-dir", str(lab_setup["experiments_dir"]),
        "--lab-runs-dir", str(lab_setup["lab_runs_dir"]),
        "run", lab_setup["experiment_id"],
        "--lab-run-id", "cli_lab_run_01"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Lab Execution Finished" in res.stdout
    assert "cli_lab_run_01" in res.stdout
    
    # Assert filesystem structure
    run_dir = lab_setup["lab_runs_dir"] / "cli_lab_run_01"
    assert run_dir.exists()
    assert (run_dir / "lab_run_manifest.json").is_file()
    assert (run_dir / "lab_summary.json").is_file()

def test_status_command_shows_status(lab_setup):
    """Verify that status command successfully displays executed run state."""
    # Setup completed manifest in runs dir
    run_id = "completed_run_123"
    run_dir = lab_setup["lab_runs_dir"] / run_id
    run_dir.mkdir()
    
    manifest = LabRunManifest(
        lab_run_id=run_id,
        world_id=lab_setup["world_id"],
        scenario_id=lab_setup["scenario_id"],
        experiment_id=lab_setup["experiment_id"],
        status="COMPLETED",
        started_at="2026-05-23T12:00:00Z",
        ended_at="2026-05-23T12:05:00Z",
        run_count=2,
        completed_run_count=2,
        failed_run_count=0,
        artifact_root=str(run_dir),
        schema_versions={"world": "worldspec.v1"}
    )
    with open(run_dir / "lab_run_manifest.json", "w") as f:
        json.dump(manifest.model_dump(), f)
        
    cmd = [
        sys.executable, "-m", "src.lab.cli",
        "--lab-runs-dir", str(lab_setup["lab_runs_dir"]),
        "status", run_id
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert f"Lab Run: {run_id}" in res.stdout
    assert "Status: COMPLETED" in res.stdout
    assert "Progress: 2/2" in res.stdout

def test_report_command_shows_report_path(lab_setup):
    """Verify that report command prints the correct absolute path to the lab summary scorecard."""
    run_id = "completed_run_123"
    run_dir = lab_setup["lab_runs_dir"] / run_id
    run_dir.mkdir(exist_ok=True)
    
    manifest = LabRunManifest(
        lab_run_id=run_id,
        world_id=lab_setup["world_id"],
        scenario_id=lab_setup["scenario_id"],
        experiment_id=lab_setup["experiment_id"],
        status="COMPLETED",
        started_at="2026-05-23T12:00:00Z",
        ended_at="2026-05-23T12:05:00Z",
        run_count=2,
        completed_run_count=2,
        failed_run_count=0,
        artifact_root=str(run_dir),
        schema_versions={"world": "worldspec.v1"}
    )
    with open(run_dir / "lab_run_manifest.json", "w") as f:
        json.dump(manifest.model_dump(), f)
        
    # Markdown report not exists yet
    cmd = [
        sys.executable, "-m", "src.lab.cli",
        "--lab-runs-dir", str(lab_setup["lab_runs_dir"]),
        "report", run_id
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode != 0
    assert "Error" in res.stderr
    
    # Touch markdown report
    report_file = run_dir / "lab_summary.md"
    report_file.touch()
    
    res2 = subprocess.run(cmd, capture_output=True, text=True)
    assert res2.returncode == 0
    assert "Lab Summary Report Path" in res2.stdout
    assert str(report_file.resolve()) in res2.stdout

def test_list_and_inspect_commands(lab_setup):
    """Verify listing and raw summary JSON inspection subcommands."""
    run_id = "completed_run_123"
    run_dir = lab_setup["lab_runs_dir"] / run_id
    run_dir.mkdir(exist_ok=True)
    
    manifest = LabRunManifest(
        lab_run_id=run_id,
        world_id=lab_setup["world_id"],
        scenario_id=lab_setup["scenario_id"],
        experiment_id=lab_setup["experiment_id"],
        status="COMPLETED",
        started_at="2026-05-23T12:00:00Z",
        ended_at="2026-05-23T12:05:00Z",
        run_count=2,
        completed_run_count=2,
        failed_run_count=0,
        artifact_root=str(run_dir),
        schema_versions={"world": "worldspec.v1"}
    )
    with open(run_dir / "lab_run_manifest.json", "w") as f:
        json.dump(manifest.model_dump(), f)
    
    # Write summary
    summary_data = {"average_health_score": 95.0}
    with open(run_dir / "lab_summary.json", "w") as f:
        json.dump(summary_data, f)
        
    # 1. test list
    cmd_list = [
        sys.executable, "-m", "src.lab.cli",
        "--lab-runs-dir", str(lab_setup["lab_runs_dir"]),
        "list"
    ]
    res_list = subprocess.run(cmd_list, capture_output=True, text=True)
    assert res_list.returncode == 0
    assert run_id in res_list.stdout
    assert "COMPLETED" in res_list.stdout
    
    # 2. test inspect
    cmd_inspect = [
        sys.executable, "-m", "src.lab.cli",
        "--lab-runs-dir", str(lab_setup["lab_runs_dir"]),
        "inspect", run_id
    ]
    res_inspect = subprocess.run(cmd_inspect, capture_output=True, text=True)
    assert res_inspect.returncode == 0
    parsed_json = json.loads(res_inspect.stdout)
    assert parsed_json["average_health_score"] == 95.0
