import pytest
import os
import json
from src.observability.reporting.baseline_generator import (
    BaselineConfig,
    DistributionSummary,
    BaselineThresholdSpec
)
from src.observability.reporting.baseline_comparator import BaselineComparator
from src.observability.reporting.run_set_repository import RunSetArtifactRepository, RunIndexRecord
from src.observability.sweeper import RunSetManifest


@pytest.fixture
def fake_baseline(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    
    metrics = {
        "health_score": DistributionSummary(
            count=10, min=80.0, max=100.0, mean=95.0, median=95.0,
            p10=90.0, p50=95.0, p90=98.0, p95=100.0, stddev=5.0
        ),
        "critical_count": DistributionSummary(
            count=10, min=0.0, max=0.0, mean=0.0, median=0.0,
            p10=0.0, p50=0.0, p90=0.0, p95=0.0, stddev=0.0
        ),
        "hard_law_violation_count": DistributionSummary(
            count=10, min=0.0, max=0.0, mean=0.0, median=0.0,
            p10=0.0, p50=0.0, p90=0.0, p95=0.0, stddev=0.0
        ),
        "tick_compute_ms_p95": DistributionSummary(
            count=10, min=50.0, max=100.0, mean=75.0, median=75.0,
            p10=60.0, p50=75.0, p90=90.0, p95=95.0, stddev=15.0
        ),
        "memory_rss_bytes_max": DistributionSummary(
            count=10, min=100.0, max=200.0, mean=150.0, median=150.0,
            p10=110.0, p50=150.0, p90=180.0, p95=190.0, stddev=30.0
        ),
        "anomaly_count": DistributionSummary(
            count=10, min=0.0, max=4.0, mean=2.0, median=2.0,
            p10=0.0, p50=2.0, p90=3.0, p95=4.0, stddev=1.0
        )
    }

    thresholds = {
        "critical_count": BaselineThresholdSpec(
            metric_name="critical_count", comparison_operator="==", threshold_value=0.0
        ),
        "hard_law_violation_count": BaselineThresholdSpec(
            metric_name="hard_law_violation_count", comparison_operator="==", threshold_value=0.0
        ),
        "health_score": BaselineThresholdSpec(
            metric_name="health_score", comparison_operator=">=", threshold_value=90.0
        ),
        "tick_compute_ms_p95": BaselineThresholdSpec(
            metric_name="tick_compute_ms_p95", comparison_operator="<=", threshold_value=114.0  # 95 * 1.2
        ),
        "memory_rss_bytes_max": BaselineThresholdSpec(
            metric_name="memory_rss_bytes_max", comparison_operator="<=", threshold_value=228.0  # 190 * 1.2
        ),
        "anomaly_count": BaselineThresholdSpec(
            metric_name="anomaly_count", comparison_operator="<=", threshold_value=4.8  # 4 * 1.2
        )
    }

    config = BaselineConfig(
        baseline_id="baseline_fake",
        scenario_name="fake_scenario",
        scenario_type="sandbox",
        created_at="2026-05-20T00:00:00Z",
        source_sweep_id="sweep_fake",
        run_count=10,
        accepted_run_count=10,
        is_weak_baseline=False,
        metrics=metrics,
        threshold_recommendations=thresholds
    )

    with open(baseline_path, "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2))

    return str(baseline_path)


def test_compare_single_run_good(fake_baseline, tmp_path):
    run_id = "run_good"
    run_dir = tmp_path / "runs"
    target_run_dir = run_dir / run_id
    os.makedirs(target_run_dir, exist_ok=True)

    # 1. Create run report JSON with passing values
    report_data = {
        "metadata": {
            "run_id": run_id,
            "health_score": 100.0,
            "errors_count": 0,
            "warnings_count": 0,
            "hard_law_violations_count": 0
        }
    }
    with open(target_run_dir / "run_report.json", "w") as f:
        json.dump(report_data, f)

    # 2. Create metric windows with passing values
    with open(target_run_dir / "metric_windows.jsonl", "w") as f:
        f.write(json.dumps({"tick_compute_ms_p95": 80.0, "memory_rss_bytes_max": 150.0, "event_count": 10}) + "\n")

    # 3. Create anomalies.json with empty list
    with open(target_run_dir / "anomalies.json", "w") as f:
        json.dump([], f)

    res = BaselineComparator.compare_run(run_id, fake_baseline, run_dir=str(run_dir))

    assert res.status == "PASS"
    assert len(res.failed_metrics) == 0
    assert len(res.warning_metrics) == 0


def test_compare_single_run_failing(fake_baseline, tmp_path):
    run_id = "run_failing"
    run_dir = tmp_path / "runs"
    target_run_dir = run_dir / run_id
    os.makedirs(target_run_dir, exist_ok=True)

    # Health score below envelope < 60 fails
    report_data = {
        "metadata": {
            "run_id": run_id,
            "health_score": 50.0,
            "errors_count": 2,
            "warnings_count": 0,
            "hard_law_violations_count": 0
        }
    }
    with open(target_run_dir / "run_report.json", "w") as f:
        json.dump(report_data, f)

    res = BaselineComparator.compare_run(run_id, fake_baseline, run_dir=str(run_dir))

    assert res.status == "FAIL"
    assert "health_score" in res.failed_metrics
    assert "critical_count" in res.failed_metrics


def test_compare_single_run_insufficient_data(fake_baseline, tmp_path):
    run_id = "run_partial"
    run_dir = tmp_path / "runs"
    target_run_dir = run_dir / run_id
    os.makedirs(target_run_dir, exist_ok=True)

    # Only include health score report, performance metrics are completely missing
    report_data = {
        "metadata": {
            "run_id": run_id,
            "health_score": 100.0,
            "errors_count": 0,
            "warnings_count": 0,
            "hard_law_violations_count": 0
        }
    }
    with open(target_run_dir / "run_report.json", "w") as f:
        json.dump(report_data, f)

    res = BaselineComparator.compare_run(run_id, fake_baseline, run_dir=str(run_dir))

    assert res.status == "INSUFFICIENT_DATA"
    assert res.metric_comparisons["tick_compute_ms_p95"].status == "INSUFFICIENT_DATA"
