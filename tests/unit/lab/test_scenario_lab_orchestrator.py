# Compliance IDs: SCENARIO-TEST-010, SCENARIO-TEST-011, SCENARIO-TEST-012
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.lab.schema import (
    ExperimentSpec,
    ScenarioSpec,
    InvalidExperimentSpecError,
    InvalidScenarioSpecError,
    LabRunManifest
)
from src.lab.repository import (
    ScenarioRepository,
    ExperimentRepository,
    LabRunRepository
)
from src.worldbuilding.schema import WorldSpec, InvalidWorldSpecError
from src.worldbuilding.repository import WorldRepository
from src.lab.orchestrator import ScenarioLabOrchestrator
from src.observability.config import ObservabilityConfig, ObservabilityMode


@pytest.fixture
def mock_repos():
    world_repo = MagicMock(spec=WorldRepository)
    world_repo.list_worlds.return_value = ["test_world"]
    scenario_repo = MagicMock(spec=ScenarioRepository)
    experiment_repo = MagicMock(spec=ExperimentRepository)
    lab_run_repo = MagicMock(spec=LabRunRepository)
    return world_repo, scenario_repo, experiment_repo, lab_run_repo


@pytest.fixture
def valid_specs():
    world_dict = {
        "schema_version": "worldspec.v1",
        "world_id": "test_world",
        "name": "Test World",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "spawn_region", "type": "grassland", "bounds": (0, 0, 49, 49)},
            {"id": "resource_region", "type": "grassland", "bounds": (50, 50, 99, 99)}
        ],
        "factions": [
            {"id": "test_faction", "type": "basic"}
        ],
        "entities": [
            {"id": "pop1", "count": 5, "role": "worker", "faction": "test_faction", "spawn_region": "spawn_region"}
        ],
        "resources": [
            {"id": "node1", "resource_type": "wood", "count": 100, "region": "resource_region"}
        ],
        "validation": {
            "expected_min_entities": 1,
            "allow_overlapping_regions": False
        }
    }
    
    scenario_dict = {
        "schema_version": "scenariospec.v1",
        "scenario_id": "test_scenario",
        "name": "Test Scenario",
        "world_id": "test_world",
        "scenario_type": "sandbox",
        "intent": {"primary_goal": "test"},
        "expected_behavior": {},
        "required_signals": {"metrics": [], "events": [], "cognition": []}
    }
    
    experiment_dict = {
        "schema_version": "experimentspec.v1",
        "experiment_id": "test_experiment",
        "scenario_id": "test_scenario",
        "experiment_type": "single_run",
        "run": {
            "ticks": 10,
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
    
    return (
        WorldSpec(**world_dict),
        ScenarioSpec(**scenario_dict),
        ExperimentSpec(**experiment_dict)
    )


def test_orchestrator_validates_world_before_compilation(mock_repos, valid_specs):
    """Verify that world spec is loaded and validated prior to executing compilation/runs."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = mock_repos
    w_spec, s_spec, e_spec = valid_specs

    world_repo.load_world.return_value = w_spec
    scenario_repo.load_scenario.return_value = s_spec
    scenario_repo.list_scenarios.return_value = ["test_scenario"]
    experiment_repo.load_experiment.return_value = e_spec

    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)

    with patch("src.worldbuilding.validator.WorldValidator.validate") as mock_world_val:
        mock_world_val.return_value = []
        try:
            orchestrator.run_lab("test_experiment", "lab_run_123")
        except Exception:
            # We expect it might fail or succeed depending on other parts, but the call to validate must happen
            pass
        assert mock_world_val.called


def test_invalid_world_stops_workflow(mock_repos, valid_specs):
    """Verify that an invalid world specification successfully aborts workflow."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = mock_repos
    w_spec, s_spec, e_spec = valid_specs

    # Break world validation rules e.g. empty factions
    bad_world_dict = w_spec.model_dump()
    bad_world_dict["factions"] = [] # FactionExistenceRule will fail because entity references 'test_faction' which is now missing
    bad_w_spec = WorldSpec(**bad_world_dict)

    world_repo.load_world.return_value = bad_w_spec
    scenario_repo.load_scenario.return_value = s_spec
    scenario_repo.list_scenarios.return_value = ["test_scenario"]
    experiment_repo.load_experiment.return_value = e_spec

    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)

    with pytest.raises(InvalidWorldSpecError):
        orchestrator.run_lab("test_experiment", "lab_run_123")

    # Verify run_lab did not proceed to initialize lab directory
    assert not lab_run_repo.create_lab_run.called


def test_invalid_scenario_stops_workflow(mock_repos, valid_specs):
    """Verify that an invalid scenario specification successfully aborts workflow."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = mock_repos
    w_spec, s_spec, e_spec = valid_specs

    # Break scenario specification
    bad_scenario_dict = s_spec.model_dump()
    bad_scenario_dict["world_id"] = "non_existent_world"
    bad_s_spec = ScenarioSpec(**bad_scenario_dict)

    world_repo.load_world.return_value = w_spec
    scenario_repo.load_scenario.return_value = bad_s_spec
    scenario_repo.list_scenarios.return_value = ["test_scenario"]
    experiment_repo.load_experiment.return_value = e_spec

    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)

    with pytest.raises(InvalidScenarioSpecError):
        orchestrator.run_lab("test_experiment", "lab_run_123")

    # Verify run_lab did not proceed to initialize lab directory
    assert not lab_run_repo.create_lab_run.called


def test_invalid_experiment_stops_workflow(mock_repos, valid_specs):
    """Verify that an invalid experiment specification successfully aborts workflow."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = mock_repos
    w_spec, s_spec, e_spec = valid_specs

    # Break experiment specification
    bad_experiment_dict = e_spec.model_dump()
    bad_experiment_dict["scenario_id"] = "non_existent_scenario"
    bad_e_spec = ExperimentSpec(**bad_experiment_dict)

    world_repo.load_world.return_value = w_spec
    scenario_repo.load_scenario.return_value = s_spec
    scenario_repo.list_scenarios.return_value = ["test_scenario"]
    experiment_repo.load_experiment.return_value = bad_e_spec

    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)

    with pytest.raises(InvalidExperimentSpecError):
        orchestrator.run_lab("test_experiment", "lab_run_123")

    # Verify run_lab did not proceed to initialize lab directory
    assert not lab_run_repo.create_lab_run.called


def test_orchestrator_does_not_overwrite_existing_lab_run(mock_repos, valid_specs):
    """Verify that orchestrator raises FileExistsError if lab run folder already exists."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = mock_repos
    w_spec, s_spec, e_spec = valid_specs

    world_repo.load_world.return_value = w_spec
    scenario_repo.load_scenario.return_value = s_spec
    scenario_repo.list_scenarios.return_value = ["test_scenario"]
    experiment_repo.load_experiment.return_value = e_spec

    # Simulate existing run directory by making create_lab_run raise FileExistsError
    lab_run_repo.create_lab_run.side_effect = FileExistsError("Lab run folder already exists")

    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)

    with pytest.raises(FileExistsError):
        orchestrator.run_lab("test_experiment", "lab_run_123")


# TCK-20260627-P3B-OBS-MODE-REMAP: STANDARD mode must resolve to NORMAL, not LIGHT
def test_standard_obs_mode_resolves_to_normal(mock_repos):
    """STANDARD lab mode must map to ObservabilityMode.NORMAL to provide richer output than LIGHT.

    D03 F5 identified that STANDARD was silently mapped to LIGHT, making it useless
    as a diagnostic step-up. This test guards against regression to the old mapping.
    """
    world_repo, scenario_repo, experiment_repo, lab_run_repo = mock_repos
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)

    assert orchestrator._resolve_obs_mode("STANDARD") == ObservabilityMode.NORMAL, (
        "STANDARD must resolve to NORMAL, not LIGHT (D03 F5 regression guard)"
    )


def test_obs_mode_mapping_full_table(mock_repos):
    """All lab mode strings must resolve to their expected engine ObservabilityMode values."""
    world_repo, scenario_repo, experiment_repo, lab_run_repo = mock_repos
    orchestrator = ScenarioLabOrchestrator(world_repo, scenario_repo, experiment_repo, lab_run_repo)

    assert orchestrator._resolve_obs_mode("LIGHTWEIGHT") == ObservabilityMode.LIGHT
    assert orchestrator._resolve_obs_mode("MINIMAL") == ObservabilityMode.LIGHT
    assert orchestrator._resolve_obs_mode("STANDARD") == ObservabilityMode.NORMAL
    assert orchestrator._resolve_obs_mode("LONG_RUN") == ObservabilityMode.LONG_RUN
    # Unknown mode falls back to LIGHT
    assert orchestrator._resolve_obs_mode("UNKNOWN") == ObservabilityMode.LIGHT
