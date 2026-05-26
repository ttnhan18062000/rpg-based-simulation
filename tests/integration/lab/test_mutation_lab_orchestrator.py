# Compliance IDs: MUTATION-TEST-007, MUTATION-TEST-008, MUTATION-TEST-009
import pytest
import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.repository import WorldRepository
from src.lab.schema import ScenarioSpec, ExperimentSpec, MutationSpec
from src.lab.repository import (
    ScenarioRepository,
    ExperimentRepository,
    LabRunRepository,
    MutationRepository
)
from src.lab.mutation_orchestrator import MutationLabOrchestrator


@pytest.fixture
def temp_mutation_lab_repos(tmp_path: Path):
    worlds_dir = tmp_path / "worlds"
    scenarios_dir = tmp_path / "scenarios"
    experiments_dir = tmp_path / "experiments"
    lab_runs_dir = tmp_path / "lab_runs"
    mutations_dir = tmp_path / "mutations"

    worlds_dir.mkdir()
    scenarios_dir.mkdir()
    experiments_dir.mkdir()
    lab_runs_dir.mkdir()
    mutations_dir.mkdir()

    world_repo = WorldRepository(worlds_dir)
    scenario_repo = ScenarioRepository(scenarios_dir)
    experiment_repo = ExperimentRepository(experiments_dir)
    lab_run_repo = LabRunRepository(lab_runs_dir)
    mutation_repo = MutationRepository(mutations_dir)

    return world_repo, scenario_repo, experiment_repo, lab_run_repo, mutation_repo


def test_mutation_lab_orchestrator_end_to_end(temp_mutation_lab_repos):
    """
    Verifies that the MutationLabOrchestrator coordinates full workflow execution
    correctly: validation, isolated runs, metamorphic checking, differential scorecarding,
    and report generation.
    """
    world_repo, scenario_repo, experiment_repo, lab_run_repo, mutation_repo = temp_mutation_lab_repos

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
            {"id": "villagers", "type": "civilian"}
        ],
        "entities": [
            {"id": "citizen_group", "count": 5, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"}
        ],
        "resources": [
            {"id": "wood_zone", "resource_type": "wood", "count": 5, "region": "town_square"}
        ],
        "buildings": [],
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

    # 3. Setup ExperimentSpec (with at least 3 seeds to satisfy evidence counts)
    experiment_dict = {
        "schema_version": "experimentspec.v1",
        "experiment_id": "test_experiment",
        "scenario_id": "test_scenario",
        "experiment_type": "single_run",
        "run": {
            "ticks": 5,
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

    # 4. Setup MutationSpec
    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "economy_sweep",
        "name": "Economy Sweep",
        "base_world_id": "test_valley",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {
                "id": "wood_low",
                "target": "resources.wood_zone.count",
                "operation": "multiply",
                "value": 0.5
            }
        ],

        "matrix": {
            "mode": "one_at_a_time",
            "max_variants": 10
        },
        "expected_relationships": [
            {
                "id": "wood_impact",
                "type": "monotonic_non_increasing",
                "metric": "health_score",
                "baseline_variant": "base",
                "compared_variant": "wood_low"
            }
        ],


        "budgets": {
            "max_variant_count": 10,
            "max_total_ticks": 100000
        }
    }
    mutation_spec = MutationSpec(**mutation_dict)
    mutation_repo.save_mutation(mutation_spec)

    # 5. Execute orchestrator
    orchestrator = MutationLabOrchestrator(
        world_repo=world_repo,
        scenario_repo=scenario_repo,
        experiment_repo=experiment_repo,
        lab_run_repo=lab_run_repo,
        mutation_repo=mutation_repo
    )

    mutation_lab_id = "test_mutlab_run"
    manifest = orchestrator.run_mutation_lab(
        mutation_id="economy_sweep",
        experiment_id="test_experiment",
        mutation_lab_id=mutation_lab_id
    )

    # 6. Verify outputs
    assert manifest["status"] == "COMPLETED"
    assert "base" in manifest["variants"]
    assert "var_one_wood_low" in manifest["variants"]
    assert manifest["variants"]["base"] == "COMPLETED"
    assert manifest["variants"]["var_one_wood_low"] == "COMPLETED"

    # Verify directories and artifacts exist
    lab_dir = Path("data/mutation_labs") / mutation_lab_id
    assert lab_dir.exists()
    assert (lab_dir / "mutation_lab_manifest.json").is_file()
    assert (lab_dir / "mutation.yaml").is_file()

    variants_dir = lab_dir / "variants"
    assert (variants_dir / "base" / "world.yaml").is_file()
    assert (variants_dir / "base" / "scenario.yaml").is_file()
    assert (variants_dir / "base" / "lab_run" / "lab_run_manifest.json").is_file()

    assert (variants_dir / "var_one_wood_low" / "world.yaml").is_file()
    assert (variants_dir / "var_one_wood_low" / "scenario.yaml").is_file()
    assert (variants_dir / "var_one_wood_low" / "lab_run" / "lab_run_manifest.json").is_file()


    analysis_dir = lab_dir / "analysis"
    assert (analysis_dir / "metamorphic_results.json").is_file()
    assert (analysis_dir / "balance_comparison.json").is_file()
    assert (analysis_dir / "mutation_lab_report.md").is_file()

    # Load report content and verify details are written nicely
    with open(analysis_dir / "mutation_lab_report.md", "r", encoding="utf-8") as f:
        report_content = f.read()
        assert "Mutation and Balance Lab Sweeps" in report_content
        assert "Sweep Manifest Details" in report_content
        assert "Variant Sweep Registry Status" in report_content
        assert "Metamorphic Assertions validation" in report_content
        assert "Differential Balance Scorecard comparison" in report_content

    # Clean up outputs
    shutil.rmtree(lab_dir)


def test_mutation_lab_budget_blocked(temp_mutation_lab_repos):
    """
    Verifies that oversized sweeps exceeding variant budget limits are preemptively blocked.
    """
    from src.lab.guardrails import BudgetBlockedError
    world_repo, scenario_repo, experiment_repo, lab_run_repo, mutation_repo = temp_mutation_lab_repos

    # 1. Setup specs
    world_dict = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
        "regions": [{"id": "town_square", "type": "town", "bounds": (0, 0, 10, 10), "terrain": "GRASS"}],
        "factions": [{"id": "villagers", "type": "civilian"}],
        "entities": [{"id": "citizen_group", "count": 5, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"}],
        "resources": [{"id": "wood_zone", "resource_type": "wood", "count": 5, "region": "town_square"}],
        "buildings": [],
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
        "experiment_type": "single_run",
        "run": {"ticks": 5, "seeds": [42], "repeat_count": 1, "max_parallel_runs": 1},
        "observability": {"mode": "STANDARD", "record_events": True, "record_metric_windows": True, "record_cognition": False},
        "analysis": {"run_post_analysis": True, "generate_report": True, "run_mining": False, "compare_baseline": False},
        "retention": {"keep_raw_events": True, "keep_reports": True, "max_artifact_mb": 500},
        "budgets": {"max_runtime_minutes": 60, "max_total_artifact_mb": 2000}
    }
    experiment_repo.save_experiment(ExperimentSpec(**experiment_dict))

    # Mutation spec with strict variant limit = 1 (but we have base + 1 variant = 2 variants!)
    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "budget_sweep",
        "name": "Budget Sweep",
        "base_world_id": "test_valley",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {"id": "wood_low", "target": "resources.wood_zone.count", "operation": "multiply", "value": 0.5}
        ],
        "matrix": {"mode": "one_at_a_time", "max_variants": 10},
        "expected_relationships": [],
        "budgets": {
            "max_variant_count": 1,  # strictly limit to 1 variant
            "max_total_ticks": 100000
        }
    }
    mutation_repo.save_mutation(MutationSpec(**mutation_dict))

    orchestrator = MutationLabOrchestrator(
        world_repo=world_repo,
        scenario_repo=scenario_repo,
        experiment_repo=experiment_repo,
        lab_run_repo=lab_run_repo,
        mutation_repo=mutation_repo
    )

    with pytest.raises(BudgetBlockedError) as exc_info:
        orchestrator.run_mutation_lab(
            mutation_id="budget_sweep",
            experiment_id="test_experiment",
            mutation_lab_id="budget_blocked_run"
        )
    assert "exceeds budget: estimated 2 variants" in str(exc_info.value)


def test_mutation_lab_invalid_spec_blocked(temp_mutation_lab_repos):
    """
    Verifies that a spec with invalid metamorphic reference is preemptively blocked.
    """
    from src.lab.validator import InvalidMutationSpecError
    world_repo, scenario_repo, experiment_repo, lab_run_repo, mutation_repo = temp_mutation_lab_repos

    # 1. Setup specs
    world_dict = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
        "regions": [{"id": "town_square", "type": "town", "bounds": (0, 0, 10, 10), "terrain": "GRASS"}],
        "factions": [{"id": "villagers", "type": "civilian"}],
        "entities": [{"id": "citizen_group", "count": 5, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"}],
        "resources": [{"id": "wood_zone", "resource_type": "wood", "count": 5, "region": "town_square"}],
        "buildings": [],
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
        "experiment_type": "single_run",
        "run": {"ticks": 5, "seeds": [42], "repeat_count": 1, "max_parallel_runs": 1},
        "observability": {"mode": "STANDARD", "record_events": True, "record_metric_windows": True, "record_cognition": False},
        "analysis": {"run_post_analysis": True, "generate_report": True, "run_mining": False, "compare_baseline": False},
        "retention": {"keep_raw_events": True, "keep_reports": True, "max_artifact_mb": 500},
        "budgets": {"max_runtime_minutes": 60, "max_total_artifact_mb": 2000}
    }
    experiment_repo.save_experiment(ExperimentSpec(**experiment_dict))

    # Spec has compared variant pointing to an undefined mutation ID: "nonexistent"
    mutation_dict = {
        "schema_version": "mutationspec.v1",
        "mutation_id": "invalid_sweep",
        "name": "Invalid Sweep",
        "base_world_id": "test_valley",
        "base_scenario_id": "test_scenario",
        "mutations": [
            {"id": "wood_low", "target": "resources.wood_zone.count", "operation": "multiply", "value": 0.5}
        ],
        "matrix": {"mode": "one_at_a_time", "max_variants": 10},
        "expected_relationships": [
            {
                "id": "wood_impact",
                "type": "monotonic_non_increasing",
                "metric": "health_score",
                "baseline_variant": "base",
                "compared_variant": "nonexistent"
            }
        ],
        "budgets": {
            "max_variant_count": 10,
            "max_total_ticks": 100000
        }
    }
    mutation_repo.save_mutation(MutationSpec(**mutation_dict))

    orchestrator = MutationLabOrchestrator(
        world_repo=world_repo,
        scenario_repo=scenario_repo,
        experiment_repo=experiment_repo,
        lab_run_repo=lab_run_repo,
        mutation_repo=mutation_repo
    )

    with pytest.raises(InvalidMutationSpecError) as exc_info:
        orchestrator.run_mutation_lab(
            mutation_id="invalid_sweep",
            experiment_id="test_experiment",
            mutation_lab_id="invalid_run"
        )
    assert "references an undefined compared variant ID: 'nonexistent'" in str(exc_info.value)

