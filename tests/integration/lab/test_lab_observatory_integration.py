import pytest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.lab.schema import ScenarioSpec, ExperimentSpec, LabRunManifest
from src.lab.repository import ScenarioRepository, ExperimentRepository, LabRunRepository
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.repository import WorldRepository
from src.lab.orchestrator import ScenarioLabOrchestrator
from src.observability.anomaly.pipeline import AnalysisPipeline


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


def test_observatory_integration_successful_sweep(temp_repos_dir):
    """Verify that a successful seed sweep records Observatory artifacts and compiles correct aggregations."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = temp_repos_dir

    # 1. Setup specs
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
            "seeds": [42, 43],
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
    experiment_repo.save_experiment(ExperimentSpec(**experiment_dict))

    # Mock AnalysisPipeline.run to output custom deterministic reports per seed
    def mock_run_pipeline(run_id, allow_partial=True):
        run_dir_path = os.path.join("data/runs", run_id)
        os.makedirs(run_dir_path, exist_ok=True)
        
        seed = run_id.split("_seed_")[-1]
        if seed == "42":
            report_data = {
                "health_score": 90.0,
                "critical_count": 0,
                "warning_count": 2,
                "anomalies": [
                    {"rule_name": "NavigationStuckRule"},
                    {"rule_name": "NavigationStuckRule"}
                ]
            }
        else:  # seed == "43"
            report_data = {
                "health_score": 60.0,
                "critical_count": 1,
                "warning_count": 0,
                "anomalies": [
                    {"rule_name": "HardLawViolationRule"}
                ]
            }
            
        with open(os.path.join(run_dir_path, "run_report.json"), "w", encoding="utf-8") as f:
            json.dump(report_data, f)
            
        return MagicMock()

    with patch.object(AnalysisPipeline, "run", side_effect=mock_run_pipeline):
        orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
        manifest = orchestrator.run_lab("test_experiment", "lab_run_obs_sweep")

    # 2. Verify overall manifest status
    assert manifest.status == "COMPLETED"
    assert manifest.completed_run_count == 2
    assert manifest.failed_run_count == 0

    run_dir = Path(manifest.artifact_root)
    assert (run_dir / "lab_summary.json").is_file()
    assert (run_dir / "lab_summary.md").is_file()

    # 3. Verify aggregated summary JSON content
    with open(run_dir / "lab_summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)
        assert summary["lab_run_id"] == "lab_run_obs_sweep"
        assert summary["status"] == "COMPLETED"
        assert summary["total_runs"] == 2
        assert summary["completed_runs"] == 2
        assert summary["failed_runs"] == 0
        assert summary["average_health_score"] == 75.0  # (90 + 60) / 2
        assert summary["critical_count_total"] == 1
        assert summary["warning_count_total"] == 2
        assert summary["best_run_id"] == "run_lab_run_obs_sweep_seed_42"
        assert summary["worst_run_id"] == "run_lab_run_obs_sweep_seed_43"
        assert summary["top_anomalies"] == {
            "NavigationStuckRule": 2,
            "HardLawViolationRule": 1
        }

    # 4. Verify aggregated summary Markdown content
    with open(run_dir / "lab_summary.md", "r", encoding="utf-8") as f:
        md_report = f.read()
        assert "# Scenario Lab Summary Report — lab_run_obs_sweep" in md_report
        assert "Average Seed Health**: `75.00/100`" in md_report
        assert "run_lab_run_obs_sweep_seed_42" in md_report
        assert "run_lab_run_obs_sweep_seed_43" in md_report
        assert "[View Report](runs/run_lab_run_obs_sweep_seed_42/run_report.md)" in md_report


def test_observatory_integration_partial_failure(temp_repos_dir):
    """Verify that a sweep with partial run failure compiles partial summaries and lists failed runs."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = temp_repos_dir

    # 1. Setup specs
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
            "seeds": [42, 99], # Seed 99 is set to fail
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
    experiment_repo.save_experiment(ExperimentSpec(**experiment_dict))

    # Mock AnalysisPipeline.run to output custom reports
    def mock_run_pipeline(run_id, allow_partial=True):
        seed = run_id.split("_seed_")[-1]
        if seed == "99":
            raise RuntimeError("Analysis pipeline failed on seed 99")
            
        run_dir_path = os.path.join("data/runs", run_id)
        os.makedirs(run_dir_path, exist_ok=True)
        report_data = {
            "health_score": 95.0,
            "critical_count": 0,
            "warning_count": 1,
            "anomalies": [{"rule_name": "ResourceNodeCrowdingRule"}]
        }
        with open(os.path.join(run_dir_path, "run_report.json"), "w", encoding="utf-8") as f:
            json.dump(report_data, f)
            
        return MagicMock()

    # Seed 99 fails kernel ticking via class monkey patching
    from src.engine.kernel import Kernel
    original_tick = Kernel.tick_once
    
    def mock_tick(self, *args, **kwargs):
        if "seed_99" in self.run_id:
            raise ValueError("Deterministic tick crash on seed 99")
        return original_tick(self, *args, **kwargs)

    Kernel.tick_once = mock_tick

    try:
        with patch.object(AnalysisPipeline, "run", side_effect=mock_run_pipeline):
            orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
            manifest = orchestrator.run_lab("test_experiment", "lab_run_partial_obs")
    finally:
        Kernel.tick_once = original_tick

    # 2. Verify overall status is PARTIAL
    assert manifest.status == "PARTIAL"
    assert manifest.completed_run_count == 1
    assert manifest.failed_run_count == 1

    run_dir = Path(manifest.artifact_root)
    assert (run_dir / "lab_summary.json").is_file()
    assert (run_dir / "lab_summary.md").is_file()

    with open(run_dir / "lab_summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)
        assert summary["status"] == "PARTIAL"
        assert summary["total_runs"] == 2
        assert summary["completed_runs"] == 1
        assert summary["failed_runs"] == 1
        assert summary["average_health_score"] == 95.0
        assert summary["worst_run_id"] == "run_lab_run_partial_obs_seed_42"

    with open(run_dir / "lab_summary.md", "r", encoding="utf-8") as f:
        md_report = f.read()
        assert "run_lab_run_partial_obs_seed_99" in md_report
        assert "FAILED/MISSING" in md_report


def test_observatory_integration_complete_failure(temp_repos_dir):
    """Verify that if all runs in a sweep fail, status is correctly marked FAILED."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = temp_repos_dir

    # 1. Setup specs
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
            "seeds": [101, 102],
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
    experiment_repo.save_experiment(ExperimentSpec(**experiment_dict))

    # All seeds fail immediately during compilation
    from src.worldbuilding.compiler import WorldCompiler
    def mock_compile_all_fail(spec, seed, *args, **kwargs):
        raise ValueError("Deterministic compilation crash")

    with patch.object(WorldCompiler, "compile", side_effect=mock_compile_all_fail):
        orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)
        manifest = orchestrator.run_lab("test_experiment", "lab_run_all_fail")

    # 2. Assert status is FAILED
    assert manifest.status == "FAILED"
    assert manifest.completed_run_count == 0
    assert manifest.failed_run_count == 2

    run_dir = Path(manifest.artifact_root)
    assert (run_dir / "lab_summary.json").is_file()
    assert (run_dir / "lab_summary.md").is_file()

    with open(run_dir / "lab_summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)
        assert summary["status"] == "FAILED"
        assert summary["completed_runs"] == 0
        assert summary["failed_runs"] == 2
        assert summary["average_health_score"] == 0.0
