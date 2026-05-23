# Compliance IDs: SCENARIO-TEST-013, SCENARIO-TEST-014, SCENARIO-TEST-015
import pytest
import os
import json
from pathlib import Path

from src.lab.schema import ScenarioSpec, ExperimentSpec, LabRunManifest
from src.lab.repository import ScenarioRepository, ExperimentRepository, LabRunRepository
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.repository import WorldRepository
from src.lab.orchestrator import ScenarioLabOrchestrator


@pytest.fixture
def temp_repos_dir(tmp_path: Path):
    worlds_dir = tmp_path / "worlds"
    scenarios_dir = tmp_path / "scenarios"
    experiments_dir = tmp_path / "experiments"
    lab_runs_dir = tmp_path / "lab_runs"

    worlds_dir.mkdir()
    scenarios_dir.mkdir()
    experiments_dir.mkdir()
    lab_runs_dir.mkdir()

    world_repo = WorldRepository(worlds_dir)
    scenario_repo = ScenarioRepository(scenarios_dir)
    experiment_repo = ExperimentRepository(experiments_dir)
    lab_run_repo = LabRunRepository(lab_runs_dir)

    return world_repo, scenario_repo, experiment_repo, lab_run_repo


def test_single_run_flow_end_to_end(temp_repos_dir):
    """Verify that a single-run experiment successfully coordinates loading, validation, simulation, and post-analysis."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = temp_repos_dir

    # 1. Setup valid WorldSpec
    world_dict = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 50,
            "height": 50,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "town_square", "type": "town", "bounds": (0, 0, 10, 10), "terrain": "GRASS"},
            {"id": "wilds", "type": "wilderness", "bounds": (15, 15, 40, 40), "terrain": "FOREST"}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"},
            {"id": "monsters", "type": "hostile"}
        ],
        "entities": [
            {"id": "citizen_group", "count": 5, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"},
            {"id": "horde", "count": 2, "role": "monster", "faction": "monsters", "spawn_region": "wilds"}
        ],
        "resources": [
            {"id": "ore_node", "resource_type": "ore", "count": 5, "region": "wilds"}
        ],
        "buildings": [
            {"id": "tavern", "type": "inn", "region": "town_square"}
        ],
        "validation": {
            "expected_min_entities": 1,
            "allow_overlapping_regions": False
        }
    }
    world_spec = WorldSpec(**world_dict)
    world_repo.save_world(world_spec)

    # 2. Setup ScenarioSpec
    scenario_dict = {
        "schema_version": "scenariospec.v1",
        "scenario_id": "test_scenario",
        "name": "Test Scenario",
        "world_id": "test_valley",
        "scenario_type": "sandbox",
        "intent": {"primary_goal": "validate_economy"},
        "expected_behavior": {},
        "required_signals": {"metrics": [], "events": [], "cognition": []}
    }
    scenario_spec = ScenarioSpec(**scenario_dict)
    scenario_repo.save_scenario(scenario_spec)

    # 3. Setup ExperimentSpec
    experiment_dict = {
        "schema_version": "experimentspec.v1",
        "experiment_id": "test_experiment",
        "scenario_id": "test_scenario",
        "experiment_type": "single_run",
        "run": {
            "ticks": 5,
            "seeds": [42],
            "repeat_count": 1,
            "max_parallel_runs": 1
        },
        "observability": {
            "mode": "STANDARD",
            "record_events": True,
            "record_metric_windows": True,
            "record_cognition": False
        },
        "analysis": {
            "run_post_analysis": True,
            "generate_report": True,
            "run_mining": False,
            "compare_baseline": False
        },
        "retention": {
            "keep_raw_events": True,
            "keep_reports": True,
            "max_artifact_mb": 500
        },
        "budgets": {
            "max_runtime_minutes": 60,
            "max_total_artifact_mb": 2000
        }
    }
    experiment_spec = ExperimentSpec(**experiment_dict)
    experiment_repo.save_experiment(experiment_spec)

    # 4. Initialize and execute ScenarioLabOrchestrator
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
    manifest = orchestrator.run_lab("test_experiment", "lab_run_001")

    # 5. Assert manifest completed status
    assert manifest.status == "COMPLETED"
    assert manifest.completed_run_count == 1
    assert manifest.failed_run_count == 0

    # 6. Verify run directories and copies
    run_dir = Path(manifest.artifact_root)
    assert run_dir.exists()
    assert (run_dir / "world" / "world.yaml").is_file()
    assert (run_dir / "scenario" / "scenario.yaml").is_file()
    assert (run_dir / "experiment" / "experiment.yaml").is_file()

    # 7. Verify isolated run folder copy exists
    child_run_dir = run_dir / "runs" / "run_lab_run_001_seed_42"
    assert child_run_dir.is_dir()
    assert (child_run_dir / "run_manifest.json").is_file()

    # 8. Verify lab summary report
    summary_path = run_dir / "lab_summary.json"
    assert summary_path.is_file()

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
        assert summary["lab_run_id"] == "lab_run_001"
        assert summary["status"] == "COMPLETED"
        assert summary["run_count"] == 1
        assert summary["completed_run_count"] == 1
        assert summary["failed_run_count"] == 0
