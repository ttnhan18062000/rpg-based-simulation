import pytest
from src.observability.reporting.baseline_generator import (
    calculate_distribution,
    BaselineGenerator,
    BaselineConfig
)
from src.observability.reporting.run_set_repository import RunSetArtifactRepository, RunIndexRecord
from src.observability.sweeper import RunSetManifest


def test_percentile_and_stddev_calculation():
    # Simple dataset: [10.0, 20.0, 30.0, 40.0, 50.0]
    # count = 5
    # mean = 30.0
    # stddev = sqrt(((10-30)^2 + (20-30)^2 + (30-30)^2 + (40-30)^2 + (50-30)^2)/5) = sqrt((400 + 100 + 0 + 100 + 400)/5) = sqrt(200) = 14.1421356...
    # median = 30.0
    # p10: index = 0.1 * 4 = 0.4. V[0] + 0.4 * (V[1] - V[0]) = 10.0 + 0.4 * 10.0 = 14.0
    # p90: index = 0.9 * 4 = 3.6. V[3] + 0.6 * (V[4] - V[3]) = 40.0 + 0.6 * 10.0 = 46.0
    
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]
    dist = calculate_distribution(vals)

    assert dist.count == 5
    assert dist.min == 10.0
    assert dist.max == 50.0
    assert dist.mean == 30.0
    assert dist.median == 30.0
    assert abs(dist.p10 - 14.0) < 1e-7
    assert abs(dist.p90 - 46.0) < 1e-7
    assert abs(dist.stddev - 14.1421356) < 1e-5


def test_baseline_generator_run_filters(tmp_path):
    repo = RunSetArtifactRepository(base_dir=str(tmp_path))
    sweep_id = "sweep_test_filters"

    manifest = RunSetManifest(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        started_at="2026-05-20T00:00:00Z",
        ticks_requested=5
    )
    repo.create_sweep(sweep_id, manifest)

    records = [
        # Run 1: Normal completed run
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_1",
            seed=1,
            scenario_name="idle",
            scenario_type="sandbox",
            status="COMPLETED",
            ticks_completed=5,
            health_score=100.0,
            critical_count=0,
            warning_count=0,
            hard_law_violation_count=0,
            artifact_path="data/run_sets/sweep_test_filters/runs/run_1"
        ),
        # Run 2: Failed run (excluded)
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_2",
            seed=2,
            scenario_name="idle",
            scenario_type="sandbox",
            status="FAILED",
            ticks_completed=1,
            health_score=0.0,
            critical_count=1,
            warning_count=0,
            hard_law_violation_count=0,
            artifact_path="data/run_sets/sweep_test_filters/runs/run_2"
        ),
        # Run 3: Completed with hard law violations (excluded)
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_3",
            seed=3,
            scenario_name="idle",
            scenario_type="sandbox",
            status="COMPLETED",
            ticks_completed=5,
            health_score=60.0,
            critical_count=0,
            warning_count=0,
            hard_law_violation_count=1,
            artifact_path="data/run_sets/sweep_test_filters/runs/run_3"
        ),
        # Run 4: Completed with critical health score < 60 (excluded)
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_4",
            seed=4,
            scenario_name="idle",
            scenario_type="sandbox",
            status="COMPLETED",
            ticks_completed=5,
            health_score=50.0,
            critical_count=2,
            warning_count=0,
            hard_law_violation_count=0,
            artifact_path="data/run_sets/sweep_test_filters/runs/run_4"
        ),
    ]

    repo.write_run_index(sweep_id, records)

    # Generate baseline with defaults
    baseline = BaselineGenerator.generate_baseline(sweep_id, base_dir=str(tmp_path))

    assert baseline.run_count == 4
    assert baseline.accepted_run_count == 1
    assert "run_2" in baseline.excluded_run_ids
    assert "run_3" in baseline.excluded_run_ids
    assert "run_4" in baseline.excluded_run_ids
    assert baseline.is_weak_baseline is True  # accepted count < 5


def test_baseline_generator_manual_overrides(tmp_path):
    repo = RunSetArtifactRepository(base_dir=str(tmp_path))
    sweep_id = "sweep_test_overrides"

    manifest = RunSetManifest(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        started_at="2026-05-20T00:00:00Z",
        ticks_requested=5
    )
    repo.create_sweep(sweep_id, manifest)

    records = [
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_1",
            seed=1,
            scenario_name="idle",
            scenario_type="sandbox",
            status="COMPLETED",
            ticks_completed=5,
            health_score=100.0,
            critical_count=0,
            warning_count=0,
            hard_law_violation_count=0,
            artifact_path="data/run_sets/sweep_test_overrides/runs/run_1"
        ),
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_2",
            seed=2,
            scenario_name="idle",
            scenario_type="sandbox",
            status="FAILED",
            ticks_completed=1,
            health_score=0.0,
            critical_count=1,
            warning_count=0,
            hard_law_violation_count=0,
            artifact_path="data/run_sets/sweep_test_overrides/runs/run_2"
        ),
    ]

    repo.write_run_index(sweep_id, records)

    # 1. Force Include the failed run, Force Exclude the normal run
    baseline = BaselineGenerator.generate_baseline(
        sweep_id,
        base_dir=str(tmp_path),
        manual_exclude=["run_1"],
        manual_include=["run_2"]
    )

    assert baseline.accepted_run_count == 1
    assert baseline.excluded_run_ids == ["run_1"]
    assert baseline.metrics["health_score"].mean == 0.0
