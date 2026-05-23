# Compliance IDs: EXPERIMENT-TEST-007, EXPERIMENT-TEST-008, EXPERIMENT-TEST-009
import pytest
import json
from pathlib import Path
from src.lab.schema import ExperimentSpec
from src.lab.repository import ExperimentRepository

@pytest.fixture
def sample_exp_dict():
    return {
        "schema_version": "experimentspec.v1",
        "experiment_id": "test_experiment_xyz",
        "scenario_id": "resource_economy_basic",
        "experiment_type": "single_run",
        "run": {
            "ticks": 1000,
            "seeds": [100],
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

def test_repository_save_and_load(tmp_path: Path, sample_exp_dict):
    """Verify that saving an experiment stores a valid yaml, and loading retrieves it."""
    repo = ExperimentRepository(tmp_path)
    spec = ExperimentSpec(**sample_exp_dict)
    
    # Save the experiment spec
    repo.save_experiment(spec)
    
    # Assert YAML file was created at target subfolder
    expected_yaml = tmp_path / "test_experiment_xyz" / "experiment.yaml"
    assert expected_yaml.is_file()
    
    # Load back and verify equality
    loaded_spec = repo.load_experiment("test_experiment_xyz")
    assert loaded_spec.experiment_id == spec.experiment_id
    assert loaded_spec.scenario_id == spec.scenario_id
    assert loaded_spec.run.ticks == 1000
    
    # List experiments should return it
    assert repo.list_experiments() == ["test_experiment_xyz"]

def test_repository_index_rebuild(tmp_path: Path, sample_exp_dict):
    """Verify that the repository manifest index is rebuilt and accurate."""
    repo = ExperimentRepository(tmp_path)
    spec1 = ExperimentSpec(**sample_exp_dict)
    
    # Save 1st experiment
    repo.save_experiment(spec1)
    
    # Save 2nd experiment
    sample_exp_dict["experiment_id"] = "another_experiment"
    sample_exp_dict["experiment_type"] = "multi_seed_sweep"
    sample_exp_dict["run"]["ticks"] = 5000
    spec2 = ExperimentSpec(**sample_exp_dict)
    repo.save_experiment(spec2)
    
    # Verify both exist in list
    assert repo.list_experiments() == ["another_experiment", "test_experiment_xyz"]
    
    # Index path should exist and contain both entries
    index_path = tmp_path / "experiment_index.json"
    assert index_path.is_file()
    
    index_data = repo.get_index()
    assert len(index_data) == 2
    assert index_data["test_experiment_xyz"]["status"] == "VALIDATED"
    assert index_data["test_experiment_xyz"]["ticks"] == 1000
    
    assert index_data["another_experiment"]["experiment_type"] == "multi_seed_sweep"
    assert index_data["another_experiment"]["status"] == "VALIDATED"
    assert index_data["another_experiment"]["ticks"] == 5000

def test_repository_handles_broken_experiments(tmp_path: Path):
    """Verify that broken/malformed experiment files are handled gracefully by indexer."""
    repo = ExperimentRepository(tmp_path)
    
    # Write a broken YAML manually under target folder
    broken_dir = tmp_path / "broken_experiment"
    broken_dir.mkdir(parents=True, exist_ok=True)
    (broken_dir / "experiment.yaml").write_text("invalid yaml text [hello: world")
    
    # List experiments should still find the folder containing experiment.yaml
    assert repo.list_experiments() == ["broken_experiment"]
    
    # Rebuild index should handle broken file cleanly
    repo.rebuild_index()
    index_data = repo.get_index()
    assert index_data["broken_experiment"]["status"] == "BROKEN"
    assert index_data["broken_experiment"]["scenario_id"] == "Unknown"

def test_repository_path_traversal_guards(tmp_path: Path, sample_exp_dict):
    """Verify that path traversal attempts are blocked via security boundaries."""
    repo = ExperimentRepository(tmp_path)
    
    # 1. Unsafe pattern in ID should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        repo.load_experiment("../unsafe_id")
    assert "Invalid or unsafe experiment_id pattern" in str(exc_info.value)
    
    # 2. Bypassing check if someone constructs a spec with unsafe ID and tries to save it
    sample_exp_dict["experiment_id"] = "unsafe/path"
    with pytest.raises(ValueError):
        repo.save_experiment(ExperimentSpec(**sample_exp_dict))
