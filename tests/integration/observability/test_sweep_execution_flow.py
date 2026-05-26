import os
import shutil
import pytest
from unittest.mock import patch
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode
from src.engine.kernel import Kernel


def test_sweep_execution_success(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    config = ScenarioSweepConfig(
        sweep_id="integration_success_sweep",
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1, 2, 3],
        ticks=3,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    manifest = ScenarioSweeper.run_sweep(config)

    assert manifest.status == "COMPLETED"
    assert manifest.completed_count == 3
    assert manifest.failed_count == 0
    assert len(manifest.failures) == 0

    # Assert directories and file outputs exist and are complete
    sweep_dir = os.path.join(output_dir, "integration_success_sweep")
    assert os.path.exists(sweep_dir)
    assert os.path.exists(os.path.join(sweep_dir, "run_set_manifest.json"))

    for seed in [1, 2, 3]:
        run_dir = os.path.join(sweep_dir, "runs", f"run_integration_success_sweep_seed_{seed}")
        assert os.path.exists(run_dir)
        assert os.path.exists(os.path.join(run_dir, "run_manifest.json"))
        assert os.path.exists(os.path.join(run_dir, "simulation_events.jsonl"))
        assert os.path.exists(os.path.join(run_dir, "metric_windows.jsonl"))


def test_sweep_execution_failure_isolation(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    config = ScenarioSweepConfig(
        sweep_id="integration_fail_isolation_sweep",
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[101, 102],
        ticks=2,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir,
        stop_on_first_critical=False
    )

    # Mock Kernel.tick_once to raise an exception only for seed 101
    original_tick = Kernel.tick_once
    def mock_tick(self):
        if "seed_101" in self._run_id:
            raise RuntimeError("Injected Failure for Seed 101")
        return original_tick(self)

    with patch.object(Kernel, "tick_once", mock_tick):
        manifest = ScenarioSweeper.run_sweep(config)

    assert manifest.status == "PARTIAL"
    assert manifest.completed_count == 1
    assert manifest.failed_count == 1
    assert "run_integration_fail_isolation_sweep_seed_101" in manifest.failures
    assert "Injected Failure for Seed 101" in manifest.failures["run_integration_fail_isolation_sweep_seed_101"]

    # Verify that the successful run (102) produced its outputs
    sweep_dir = os.path.join(output_dir, "integration_fail_isolation_sweep")
    success_run_dir = os.path.join(sweep_dir, "runs", "run_integration_fail_isolation_sweep_seed_102")
    assert os.path.exists(success_run_dir)
    assert os.path.exists(os.path.join(success_run_dir, "run_manifest.json"))


def test_sweep_stop_on_critical(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    config = ScenarioSweepConfig(
        sweep_id="integration_stop_critical_sweep",
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[201, 202, 203],
        ticks=2,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir,
        stop_on_first_critical=True
    )

    # Mock Kernel.tick_once to raise an exception for seed 201
    original_tick = Kernel.tick_once
    def mock_tick(self):
        if "seed_201" in self._run_id:
            raise RuntimeError("Injected Critical Failure")
        return original_tick(self)

    with patch.object(Kernel, "tick_once", mock_tick):
        manifest = ScenarioSweeper.run_sweep(config)

    # Since stop_on_first_critical is True, it should fail run 201 and stop immediately,
    # meaning run 202 and 203 are never executed.
    assert manifest.status == "FAILED"
    assert manifest.completed_count == 0
    assert manifest.failed_count == 1
    assert "run_integration_stop_critical_sweep_seed_201" in manifest.failures
    assert "run_integration_stop_critical_sweep_seed_202" not in manifest.failures
    assert "run_integration_stop_critical_sweep_seed_203" not in manifest.failures
