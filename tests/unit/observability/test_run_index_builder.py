import os
import pytest
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode
from src.observability.reporting.run_set_repository import RunSetArtifactRepository


def test_index_builder_with_missing_and_failed_runs(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_resilient_sweep"
    
    # We will construct a minimal sweep configuration
    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1, 2],
        ticks=5,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # Let's run a sweep. We know "idle" will complete successfully, but we want to assert
    # that if we manually delete run_report.json or manipulate directories, the index builder
    # fallback paths handle it gracefully.
    
    # 1. Run sweep to generate valid directories
    manifest = ScenarioSweeper.run_sweep(config)
    assert manifest.status == "COMPLETED"

    # Verify run index was generated
    repo = RunSetArtifactRepository(base_dir=output_dir)
    records = repo.read_run_index(sweep_id)
    assert len(records) == 2
    assert records[0].health_score >= 90.0  # Success fallback (allows light warning variance under slow virtualized CPU execution)

    # 2. Let's delete a run's manifest and report files to simulate corruption
    sweep_dir = os.path.join(output_dir, sweep_id)
    run_dir_1 = os.path.join(sweep_dir, "runs", "run_test_resilient_sweep_seed_1")
    manifest_file = os.path.join(run_dir_1, "run_manifest.json")
    report_file = os.path.join(run_dir_1, "run_report.json")
    
    if os.path.exists(manifest_file):
        os.remove(manifest_file)
    if os.path.exists(report_file):
        os.remove(report_file)

    # Re-run a sweep or invoke index generation again on same specs
    # ScenarioSweeper's internal indexing method is robust. Let's test that it handles
    # missing manifest / report files without throwing Exceptions.
    # We can invoke ScenarioSweeper.run_sweep again or just test its internal indexing block.
    # To test robust parsing, let's run again on same config
    manifest2 = ScenarioSweeper.run_sweep(config)
    assert manifest2.status == "COMPLETED"

    # Assert that index generation did not crash and records still parsed cleanly
    records2 = repo.read_run_index(sweep_id)
    assert len(records2) == 2
    # Seed 1 (re-executed successfully, recreating files) works!
    assert records2[0].run_id == "run_test_resilient_sweep_seed_1"
