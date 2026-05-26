import os
import shutil
import pytest
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode


def test_sweeper_directory_setup(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    config = ScenarioSweepConfig(
        sweep_id="test_sweep_123",
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[10, 20],
        ticks=5,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # Let's mock SCENARIO_BUILDERS execution or mock the actual Kernel execution
    # to test sweeper logic in isolation.
    # We will test integration fully in the integration test, but here we can assert config outputs.
    sweep_dir = os.path.join(output_dir, "test_sweep_123")
    assert not os.path.exists(sweep_dir)
    
    # We can run a small 1-tick sweep with "idle" which executes extremely fast!
    manifest = ScenarioSweeper.run_sweep(config)

    assert os.path.exists(sweep_dir)
    assert os.path.exists(os.path.join(sweep_dir, "sweep_config.json"))
    assert os.path.exists(os.path.join(sweep_dir, "run_set_manifest.json"))
    
    assert manifest.sweep_id == "test_sweep_123"
    assert manifest.completed_count == 2
    assert manifest.status == "COMPLETED"
    assert manifest.run_ids == ["run_test_sweep_123_seed_10", "run_test_sweep_123_seed_20"]
    assert manifest.seed_by_run_id == {"run_test_sweep_123_seed_10": 10, "run_test_sweep_123_seed_20": 20}
    
    # Check that individual runs directory outputs were moved correctly
    assert os.path.exists(os.path.join(sweep_dir, "runs", "run_test_sweep_123_seed_10"))
    assert os.path.exists(os.path.join(sweep_dir, "runs", "run_test_sweep_123_seed_20"))
