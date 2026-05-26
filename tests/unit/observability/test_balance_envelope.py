import os
import json
import pytest
from pydantic import ValidationError
from src.observability.reporting.balance_envelope import BalanceEnvelopeLoader, BalanceEnvelope, ExpectationValue
from src.observability.reporting.baseline_generator import (
    BaselineConfig,
    DistributionSummary,
    BaselineThresholdSpec
)


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


def test_load_valid_envelope(tmp_path):
    env_data = {
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "expectations": {
            "critical_count": {
                "max": 0.0,
                "severity": "FAIL"
            },
            "health_score": {
                "min": 75.0,
                "severity": "WARNING"
            },
            "tick_compute_ms_p95": {
                "max_multiplier_from_baseline": 1.10,
                "severity": "WARNING"
            }
        },
        "schema_version": "1.0"
    }

    envelope_file = tmp_path / "balance_envelope.json"
    with open(envelope_file, "w", encoding="utf-8") as f:
        json.dump(env_data, f)

    envelope = BalanceEnvelopeLoader.load_from_file(str(envelope_file))
    assert envelope.scenario_name == "RESOURCE_ECONOMY_1000"
    assert envelope.scenario_type == "resource_economy"
    assert "critical_count" in envelope.expectations
    assert envelope.expectations["critical_count"].max == 0.0
    assert envelope.expectations["critical_count"].severity == "FAIL"
    assert envelope.expectations["health_score"].min == 75.0
    assert envelope.expectations["tick_compute_ms_p95"].max_multiplier_from_baseline == 1.10


def test_load_invalid_envelope_missing_fields(tmp_path):
    env_data = {
        "scenario_type": "resource_economy",
        "expectations": {}
    }
    envelope_file = tmp_path / "invalid_envelope.json"
    with open(envelope_file, "w", encoding="utf-8") as f:
        json.dump(env_data, f)

    with pytest.raises(ValidationError):
        BalanceEnvelopeLoader.load_from_file(str(envelope_file))


def test_load_invalid_expectation_missing_bounds(tmp_path):
    env_data = {
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "expectations": {
            "health_score": {
                "severity": "WARNING"
            }
        }
    }
    envelope_file = tmp_path / "invalid_exp.json"
    with open(envelope_file, "w", encoding="utf-8") as f:
        json.dump(env_data, f)

    with pytest.raises(ValidationError):
        BalanceEnvelopeLoader.load_from_file(str(envelope_file))


def test_load_invalid_severity(tmp_path):
    env_data = {
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "expectations": {
            "health_score": {
                "min": 75.0,
                "severity": "INVALID_SEVERITY"
            }
        }
    }
    envelope_file = tmp_path / "invalid_severity.json"
    with open(envelope_file, "w", encoding="utf-8") as f:
        json.dump(env_data, f)

    with pytest.raises(ValidationError):
        BalanceEnvelopeLoader.load_from_file(str(envelope_file))


def test_compare_run_with_envelope_overrides(fake_baseline, tmp_path):
    baseline_path = fake_baseline
    
    # 1. Create a passing run
    run_id = "run_env_test"
    run_dir = tmp_path / "runs"
    target_run_dir = run_dir / run_id
    os.makedirs(target_run_dir, exist_ok=True)
    
    # Health score is 85.0. Without envelope, baseline threshold_value is 90.0 (comparison_operator >=).
    # Since 85.0 >= 60.0, standard baseline check yields WARNING.
    # We will override health_score threshold in the envelope with min=80.0, severity=FAIL.
    # Therefore, 85.0 >= 80.0, so health_score should PASS!
    report_data = {
        "metadata": {
            "run_id": run_id,
            "health_score": 85.0,
            "errors_count": 0,
            "warnings_count": 0,
            "hard_law_violations_count": 0
        }
    }
    with open(target_run_dir / "run_report.json", "w") as f:
        json.dump(report_data, f)
        
    with open(target_run_dir / "metric_windows.jsonl", "w") as f:
        f.write(json.dumps({"tick_compute_ms_p95": 80.0, "memory_rss_bytes_max": 150.0, "event_count": 10}) + "\n")
        
    with open(target_run_dir / "anomalies.json", "w") as f:
        json.dump([], f)
        
    # Create envelope file
    env_data = {
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "expectations": {
            "health_score": {
                "min": 80.0,
                "severity": "FAIL"
            },
            "tick_compute_ms_p95": {
                "max_multiplier_from_baseline": 1.10, # Baseline mean is 75.0. 75 * 1.1 = 82.5. Actual is 80.0 (PASS)
                "severity": "FAIL"
            }
        },
        "schema_version": "1.0"
    }
    envelope_file = tmp_path / "balance_envelope.json"
    with open(envelope_file, "w", encoding="utf-8") as f:
        json.dump(env_data, f)
        
    from src.observability.reporting.baseline_comparator import BaselineComparator
    res = BaselineComparator.compare_run(run_id, baseline_path, run_dir=str(run_dir), envelope_path=str(envelope_file))
    
    assert res.status == "PASS"
    assert res.envelope_name == "RESOURCE_ECONOMY_1000"
    assert res.metric_comparisons["health_score"].status == "PASS"
    assert res.metric_comparisons["tick_compute_ms_p95"].status == "PASS"


def test_compare_run_with_envelope_failing_multiplier(fake_baseline, tmp_path):
    baseline_path = fake_baseline
    
    run_id = "run_env_fail"
    run_dir = tmp_path / "runs"
    target_run_dir = run_dir / run_id
    os.makedirs(target_run_dir, exist_ok=True)
    
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
    # tick_compute_ms_p95 is 150.0. Baseline recommend threshold is 114.0. Max multiplier is 1.1 => max limit is 125.4.
    # 150.0 > 125.4, which should FAIL!
    with open(target_run_dir / "metric_windows.jsonl", "w") as f:
        f.write(json.dumps({"tick_compute_ms_p95": 150.0, "memory_rss_bytes_max": 150.0, "event_count": 10}) + "\n")
        
    with open(target_run_dir / "anomalies.json", "w") as f:
        json.dump([], f)
        
    env_data = {
        "scenario_name": "RESOURCE_ECONOMY_1000",
        "scenario_type": "resource_economy",
        "expectations": {
            "tick_compute_ms_p95": {
                "max_multiplier_from_baseline": 1.10,
                "severity": "FAIL"
            }
        },
        "schema_version": "1.0"
    }
    envelope_file = tmp_path / "balance_envelope.json"
    with open(envelope_file, "w", encoding="utf-8") as f:
        json.dump(env_data, f)
        
    from src.observability.reporting.baseline_comparator import BaselineComparator
    res = BaselineComparator.compare_run(run_id, baseline_path, run_dir=str(run_dir), envelope_path=str(envelope_file))
    
    assert res.status == "FAIL"
    assert "tick_compute_ms_p95" in res.failed_metrics


def test_rules_engine_apply_envelope():
    from src.observability.anomaly.rules_engine import RuleEngine
    
    # Create envelope
    envelope = BalanceEnvelope(
        scenario_name="RESOURCE_ECONOMY_1000",
        scenario_type="resource_economy",
        expectations={
            "NavigationStuckBasic": ExpectationValue(
                max=20.0,
                severity="FAIL"
            ),
            "stalled_ticks": ExpectationValue(
                max=40.0,
                severity="WARNING"
            )
        }
    )
    
    engine = RuleEngine()
    engine.apply_envelope(envelope)
    
    # NavigationStuckBasic config
    stuck_config = engine.config["NavigationStuckBasic"]
    assert stuck_config.severity_override == "CRITICAL" # FAIL maps to CRITICAL
    assert stuck_config.thresholds["tick_threshold"] == 20
    assert "resource_economy" in stuck_config.scenario_types
    
    # QuestStalledBasic (stalled_ticks maps to QuestStalledBasic)
    stalled_config = engine.config["QuestStalledBasic"]
    assert stalled_config.severity_override == "WARNING"
    assert stalled_config.thresholds["tick_threshold"] == 40
    assert "resource_economy" in stalled_config.scenario_types
