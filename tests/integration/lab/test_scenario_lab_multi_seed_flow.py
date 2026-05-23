# Compliance IDs: SCENARIO-TEST-016, SCENARIO-TEST-017, SCENARIO-TEST-018
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch

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


def test_multi_seed_flow_all_succeed(temp_repos_dir):
    """Verify that a multi-seed experiment sweeps all seeds successfully and marks status COMPLETED."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = temp_repos_dir

    # 1. Setup valid specs
    world_dict = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
        "regions": [
            {"id": "town_square", "type": "town", "bounds": (0, 0, 10, 10), "terrain": "GRASS"},
            {"id": "wilds", "type": "wilderness", "bounds": (15, 15, 40, 40), "terrain": "FOREST"}
        ],
        "factions": [{"id": "villagers", "type": "civilian"}],
        "entities": [{"id": "pop1", "count": 2, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"}],
        "validation": {"expected_min_entities": 1, "allow_overlapping_regions": False}
    }
    world_repo.save_world(WorldSpec(**world_dict))

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
    scenario_repo.save_scenario(ScenarioSpec(**scenario_dict))

    experiment_dict = {
        "schema_version": "experimentspec.v1",
        "experiment_id": "test_experiment",
        "scenario_id": "test_scenario",
        "experiment_type": "multi_seed_sweep",
        "run": {
            "ticks": 2,
            "seeds": [42, 43, 44],
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
            "run_post_analysis": False,
            "generate_report": False,
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
    experiment_repo.save_experiment(ExperimentSpec(**experiment_dict))

    # Run
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
    manifest = orchestrator.run_lab("test_experiment", "lab_run_all_success")

    # Assert status
    assert manifest.status == "COMPLETED"
    assert manifest.completed_run_count == 3
    assert manifest.failed_run_count == 0

    run_dir = Path(manifest.artifact_root)
    assert (run_dir / "lab_summary.json").is_file()


def test_multi_seed_flow_partial_failure(temp_repos_dir):
    """Verify that if some runs in a sweep fail, the lab updates successfully and marks status PARTIAL."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = temp_repos_dir

    # 1. Setup valid specs
    world_dict = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
        "regions": [
            {"id": "town_square", "type": "town", "bounds": (0, 0, 10, 10), "terrain": "GRASS"},
            {"id": "wilds", "type": "wilderness", "bounds": (15, 15, 40, 40), "terrain": "FOREST"}
        ],
        "factions": [{"id": "villagers", "type": "civilian"}],
        "entities": [{"id": "pop1", "count": 2, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"}],
        "validation": {"expected_min_entities": 1, "allow_overlapping_regions": False}
    }
    world_repo.save_world(WorldSpec(**world_dict))

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
    scenario_repo.save_scenario(ScenarioSpec(**scenario_dict))

    experiment_dict = {
        "schema_version": "experimentspec.v1",
        "experiment_id": "test_experiment",
        "scenario_id": "test_scenario",
        "experiment_type": "multi_seed_sweep",
        "run": {
            "ticks": 2,
            "seeds": [42, 99], # Seed 99 is set to fail compile
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
            "run_post_analysis": False,
            "generate_report": False,
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
    experiment_repo.save_experiment(ExperimentSpec(**experiment_dict))

    from src.worldbuilding.compiler import WorldCompiler
    original_compile = WorldCompiler.compile

    def mock_compile(spec, seed, *args, **kwargs):
        if seed == 99:
            raise ValueError("Deterministic compilation failure for testing")
        return original_compile(spec, seed, *args, **kwargs)

    # Run with patch
    with patch("src.worldbuilding.compiler.WorldCompiler.compile", side_effect=mock_compile):
        orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
        manifest = orchestrator.run_lab("test_experiment", "lab_run_partial_success")

    # Assert status is PARTIAL
    assert manifest.status == "PARTIAL"
    assert manifest.completed_run_count == 1
    assert manifest.failed_run_count == 1

    run_dir = Path(manifest.artifact_root)
    assert (run_dir / "lab_summary.json").is_file()

    with open(run_dir / "lab_summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)
        assert summary["status"] == "PARTIAL"
        assert summary["completed_run_count"] == 1
        assert summary["failed_run_count"] == 1
