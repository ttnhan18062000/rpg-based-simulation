import os
import json
import pytest
from src.observability.reporting.sweep_report import SweepReportGenerator, CIGateResult
from src.observability.reporting.run_set_repository import RunSetArtifactRepository, RunIndexRecord, SweepSummary
from src.observability.reporting.baseline_generator import (
    BaselineConfig,
    DistributionSummary,
    BaselineThresholdSpec
)


@pytest.fixture
def test_setup(tmp_path):
    base_dir = tmp_path / "run_sets"
    sweep_id = "sweep_test"
    sweep_dir = base_dir / sweep_id
    sweep_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = sweep_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write run_set_manifest.json
    manifest = {
        "sweep_id": sweep_id,
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "started_at": "2026-05-20T00:00:00Z",
        "ended_at": "2026-05-20T00:05:00Z",
        "status": "COMPLETED",
        "run_ids": ["run_1", "run_2"],
        "seed_by_run_id": {"run_1": 1, "run_2": 2},
        "ticks_requested": 1000,
        "completed_count": 2,
        "failed_count": 0,
        "artifact_schema_version": 2
    }
    with open(sweep_dir / "run_set_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 2. Write sweep_summary.json
    summary = {
        "sweep_id": sweep_id,
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "total_runs": 2,
        "completed_runs": 2,
        "failed_runs": 0,
        "average_health_score": 95.0,
        "critical_run_count": 0,
        "warning_run_count": 1,
        "worst_run_id": "run_2",
        "best_run_id": "run_1",
        "most_common_anomaly_rule_ids": {"NavigationStuckBasic": 1}
    }
    with open(sweep_dir / "sweep_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 3. Write run_index.jsonl
    records = [
        {
            "sweep_id": sweep_id,
            "run_id": "run_1",
            "seed": 1,
            "scenario_name": "RESOURCE_ECONOMY_1000",
            "scenario_type": "resource_economy",
            "status": "COMPLETED",
            "ticks_completed": 1000,
            "health_score": 100.0,
            "critical_count": 0,
            "warning_count": 0,
            "hard_law_violation_count": 0,
            "artifact_path": str(runs_dir / "run_1")
        },
        {
            "sweep_id": sweep_id,
            "run_id": "run_2",
            "seed": 2,
            "scenario_name": "RESOURCE_ECONOMY_1000",
            "scenario_type": "resource_economy",
            "status": "COMPLETED",
            "ticks_completed": 1000,
            "health_score": 90.0,
            "critical_count": 0,
            "warning_count": 1,
            "hard_law_violation_count": 0,
            "artifact_path": str(runs_dir / "run_2")
        }
    ]
    with open(sweep_dir / "run_index.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Write run_report.json, anomalies.json, and metric_windows.jsonl for run_1 and run_2
    # run_1: health 100.0, warnings 0, anomalies 0
    rid_dir = runs_dir / "run_1"
    rid_dir.mkdir(parents=True, exist_ok=True)
    
    report_1 = {
        "metadata": {
            "health_score": 100.0,
            "errors_count": 0,
            "warnings_count": 0,
            "hard_law_violations_count": 0
        }
    }
    with open(rid_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump(report_1, f, indent=2)
        
    with open(rid_dir / "anomalies.json", "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)
        
    with open(rid_dir / "metric_windows.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"tick_compute_ms_p95": 80.0, "memory_rss_bytes_max": 150.0, "event_count": 100}) + "\n")

    # run_2: health 90.0, warnings 1, anomalies 1
    rid_dir = runs_dir / "run_2"
    rid_dir.mkdir(parents=True, exist_ok=True)
    
    report_2 = {
        "metadata": {
            "health_score": 90.0,
            "errors_count": 0,
            "warnings_count": 1,
            "hard_law_violations_count": 0
        }
    }
    with open(rid_dir / "run_report.json", "w", encoding="utf-8") as f:
        json.dump(report_2, f, indent=2)
        
    anoms_2 = [
        {
            "rule_name": "NavigationStuckBasic",
            "severity": "WARNING",
            "tick_detected": 45,
            "message": "stuck basic warning",
            "entity_id": "hero",
            "context": {}
        }
    ]
    with open(rid_dir / "anomalies.json", "w", encoding="utf-8") as f:
        json.dump(anoms_2, f, indent=2)
        
    with open(rid_dir / "metric_windows.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"tick_compute_ms_p95": 90.0, "memory_rss_bytes_max": 160.0, "event_count": 80}) + "\n")

    # 4. Write baseline.json
    baseline = {
        "baseline_id": "baseline_test",
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "created_at": "2026-05-20T00:00:00Z",
        "source_sweep_id": "sweep_base",
        "run_count": 10,
        "accepted_run_count": 10,
        "excluded_run_ids": [],
        "is_weak_baseline": False,
        "metrics": {
            "health_score": {
                "count": 10, "min": 90.0, "max": 100.0, "mean": 98.0, "median": 98.0,
                "p10": 95.0, "p50": 98.0, "p90": 100.0, "p95": 100.0, "stddev": 2.0
            },
            "critical_count": {
                "count": 10, "min": 0, "max": 0, "mean": 0.0, "median": 0.0,
                "p10": 0, "p50": 0, "p90": 0, "p95": 0, "stddev": 0.0
            },
            "hard_law_violation_count": {
                "count": 10, "min": 0, "max": 0, "mean": 0.0, "median": 0.0,
                "p10": 0, "p50": 0, "p90": 0, "p95": 0, "stddev": 0.0
            },
            "tick_compute_ms_p95": {
                "count": 10, "min": 50.0, "max": 100.0, "mean": 75.0, "median": 75.0,
                "p10": 60.0, "p50": 75.0, "p90": 90.0, "p95": 95.0, "stddev": 15.0
            },
            "memory_rss_bytes_max": {
                "count": 10, "min": 100.0, "max": 200.0, "mean": 150.0, "median": 150.0,
                "p10": 110.0, "p50": 150.0, "p90": 180.0, "p95": 190.0, "stddev": 30.0
            },
            "anomaly_count": {
                "count": 10, "min": 0, "max": 2, "mean": 1.0, "median": 1.0,
                "p10": 0, "p50": 1.0, "p90": 2.0, "p95": 2.0, "stddev": 0.5
            }
        },
        "threshold_recommendations": {
            "critical_count": {"metric_name": "critical_count", "comparison_operator": "==", "threshold_value": 0.0},
            "hard_law_violation_count": {"metric_name": "hard_law_violation_count", "comparison_operator": "==", "threshold_value": 0.0},
            "health_score": {"metric_name": "health_score", "comparison_operator": ">=", "threshold_value": 95.0},
            "tick_compute_ms_p95": {"metric_name": "tick_compute_ms_p95", "comparison_operator": "<=", "threshold_value": 114.0},
            "memory_rss_bytes_max": {"metric_name": "memory_rss_bytes_max", "comparison_operator": "<=", "threshold_value": 228.0},
            "anomaly_count": {"metric_name": "anomaly_count", "comparison_operator": "<=", "threshold_value": 2.4}
        },
        "artifact_schema_version": "baseline_v1"
    }
    baseline_path = tmp_path / "baseline.json"
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)

    return base_dir, sweep_id, baseline_path


def test_sweep_report_generator_success(test_setup):
    base_dir, sweep_id, baseline_path = test_setup

    md_path, json_path, gate_result = SweepReportGenerator.generate(
        sweep_id=sweep_id,
        baseline_path=str(baseline_path),
        base_dir=str(base_dir)
    )

    assert os.path.exists(md_path)
    assert os.path.exists(json_path)

    # 1. Verify JSON report contents
    with open(json_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert report["sweep_id"] == sweep_id
    assert report["scenario_name"] == "RESOURCE_ECONOMY_1000"
    assert report["average_health_score"] == 95.0

    # 2. Verify all 12 Markdown sections are present
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    assert "Sweep Observability & Validation Report" in md
    assert "2. Sweep Metadata" in md
    assert "3. Run Distribution" in md
    assert "4. Baseline Summary" in md
    assert "5. Comparison Result" in md
    assert "6. Outlier Seeds" in md
    assert "7. Most Common Anomalies" in md
    assert "8. Performance Drift" in md
    assert "9. Memory Drift" in md
    assert "10. Health Score Distribution" in md
    assert "11. Failed Expectations" in md
    assert "12. Recommended Investigation Points" in md


def test_ci_gate_gating_warnings_and_failures(test_setup):
    base_dir, sweep_id, baseline_path = test_setup

    # Test default behaviour: WARNING is not FAIL
    _, _, gate_result_default = SweepReportGenerator.generate(
        sweep_id=sweep_id,
        baseline_path=str(baseline_path),
        base_dir=str(base_dir),
        warn_as_fail=False
    )
    assert gate_result_default.status == "WARNING"

    # Test warn_as_fail = True
    _, _, gate_result_warn_fail = SweepReportGenerator.generate(
        sweep_id=sweep_id,
        baseline_path=str(baseline_path),
        base_dir=str(base_dir),
        warn_as_fail=True
    )
    assert gate_result_warn_fail.status == "FAIL"
