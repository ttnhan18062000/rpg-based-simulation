# Compliance IDs: OBS-051, OBS-052, OBS-053
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from src.observability.reporting.run_set_repository import RunSetArtifactRepository


class DistributionSummary(BaseModel):
    """Calculated distribution metrics representing statistical outcomes of a telemetry metric."""
    count: int
    min: float
    max: float
    mean: float
    median: float
    p10: float
    p50: float
    p90: float
    p95: float
    stddev: float


class BaselineThresholdSpec(BaseModel):
    """Recommended statistical boundaries used to gate simulation validation pipelines."""
    metric_name: str
    comparison_operator: str  # "==", ">=", "<="
    threshold_value: float
    is_custom_override: bool = False


class BaselineConfig(BaseModel):
    """Structured baseline manifest representing normal statistical performance of a scenario."""
    baseline_id: str
    scenario_name: str
    scenario_type: str
    created_at: str
    source_sweep_id: str
    run_count: int
    accepted_run_count: int
    excluded_run_ids: List[str] = Field(default_factory=list)
    exclusion_reasons: Dict[str, str] = Field(default_factory=dict)
    is_weak_baseline: bool
    metrics: Dict[str, DistributionSummary] = Field(default_factory=dict)
    threshold_recommendations: Dict[str, BaselineThresholdSpec] = Field(default_factory=dict)
    artifact_schema_version: str = "baseline_v1"


def calculate_distribution(vals: List[float]) -> DistributionSummary:
    """Computes full statistical distribution percentiles in pure Python without external libraries."""
    if not vals:
        return DistributionSummary(
            count=0, min=0.0, max=0.0, mean=0.0, median=0.0,
            p10=0.0, p50=0.0, p90=0.0, p95=0.0, stddev=0.0
        )
    sorted_vals = sorted(vals)
    count = len(vals)
    min_val = float(sorted_vals[0])
    max_val = float(sorted_vals[-1])
    mean_val = sum(vals) / count

    def get_pct(p: float) -> float:
        if count == 1:
            return float(sorted_vals[0])
        idx = (p / 100.0) * (count - 1)
        k = int(idx)
        c = k + 1 if k < count - 1 else k
        if k == c:
            return float(sorted_vals[k])
        return float(sorted_vals[k] + (idx - k) * (sorted_vals[c] - sorted_vals[k]))

    median_val = get_pct(50.0)
    p10_val = get_pct(10.0)
    p50_val = get_pct(50.0)
    p90_val = get_pct(90.0)
    p95_val = get_pct(95.0)

    variance = sum((x - mean_val) ** 2 for x in vals) / count
    stddev_val = variance ** 0.5

    return DistributionSummary(
        count=count,
        min=min_val,
        max=max_val,
        mean=mean_val,
        median=median_val,
        p10=p10_val,
        p50=p50_val,
        p90=p90_val,
        p95=p95_val,
        stddev=stddev_val
    )


class BaselineGenerator:
    """Orchestrates generation of control baselines and gating thresholds from multi-run sweeps."""

    @classmethod
    def generate_baseline(
        cls,
        sweep_id: str,
        base_dir: str = "data/run_sets",
        manual_exclude: Optional[List[str]] = None,
        manual_include: Optional[List[str]] = None
    ) -> BaselineConfig:
        repo = RunSetArtifactRepository(base_dir=base_dir)
        sweeps = repo.list_sweeps()
        if sweep_id not in sweeps:
            raise FileNotFoundError(f"Sweep '{sweep_id}' not found under {base_dir}")

        manifest = sweeps[sweep_id]
        records = repo.read_run_index(sweep_id)

        manual_exclude = manual_exclude or []
        manual_include = manual_include or []

        accepted_records = []
        excluded_run_ids = []
        exclusion_reasons = {}

        for r in records:
            if r.run_id in manual_include:
                accepted_records.append(r)
                continue

            if r.run_id in manual_exclude:
                excluded_run_ids.append(r.run_id)
                exclusion_reasons[r.run_id] = "Manual developer override exclude."
                continue

            if r.status not in ("COMPLETED", "ANALYZED"):
                excluded_run_ids.append(r.run_id)
                exclusion_reasons[r.run_id] = f"Run status is {r.status}."
                continue

            if r.hard_law_violation_count > 0:
                excluded_run_ids.append(r.run_id)
                exclusion_reasons[r.run_id] = f"Run has {r.hard_law_violation_count} hard law violations."
                continue

            if r.health_score < 60.0:
                excluded_run_ids.append(r.run_id)
                exclusion_reasons[r.run_id] = f"Run is critical with health score {r.health_score}."
                continue

            accepted_records.append(r)

        health_scores = []
        critical_counts = []
        warning_counts = []
        hard_law_violation_counts = []
        tick_compute_ms_p95_list = []
        memory_rss_bytes_max_list = []
        event_counts = []
        anomaly_counts = []

        for r in accepted_records:
            health_scores.append(r.health_score)
            critical_counts.append(float(r.critical_count))
            warning_counts.append(float(r.warning_count))
            hard_law_violation_counts.append(float(r.hard_law_violation_count))

            metric_file = os.path.join(r.artifact_path, "metric_windows.jsonl")
            run_p95_list = []
            run_rss_list = []
            run_events = 0
            run_anoms = 0

            if os.path.exists(metric_file):
                try:
                    with open(metric_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                w_data = json.loads(line)
                                if "tick_compute_ms_p95" in w_data:
                                    run_p95_list.append(w_data["tick_compute_ms_p95"])
                                if "memory_rss_bytes_max" in w_data:
                                    run_rss_list.append(w_data["memory_rss_bytes_max"])
                                if "event_count" in w_data:
                                    run_events += w_data["event_count"]
                except Exception:
                    pass

            anomalies_file = os.path.join(r.artifact_path, "anomalies.json")
            if os.path.exists(anomalies_file):
                try:
                    with open(anomalies_file, "r", encoding="utf-8") as f:
                        a_list = json.load(f)
                        run_anoms = len(a_list)
                except Exception:
                    pass

            tick_compute_ms_p95_list.append(max(run_p95_list) if run_p95_list else 0.0)
            memory_rss_bytes_max_list.append(max(run_rss_list) if run_rss_list else 0.0)
            event_counts.append(float(run_events))
            anomaly_counts.append(float(run_anoms))

        metrics_dist = {
            "health_score": calculate_distribution(health_scores),
            "critical_count": calculate_distribution(critical_counts),
            "warning_count": calculate_distribution(warning_counts),
            "hard_law_violation_count": calculate_distribution(hard_law_violation_counts),
            "tick_compute_ms_p95": calculate_distribution(tick_compute_ms_p95_list),
            "memory_rss_bytes_max": calculate_distribution(memory_rss_bytes_max_list),
            "event_count": calculate_distribution(event_counts),
            "anomaly_count": calculate_distribution(anomaly_counts)
        }

        p10_health = metrics_dist["health_score"].p10
        p95_lat = metrics_dist["tick_compute_ms_p95"].p95 * 1.2
        p95_mem = metrics_dist["memory_rss_bytes_max"].p95 * 1.2
        p95_anom = metrics_dist["anomaly_count"].p95 * 1.2

        recommendations = {
            "critical_count": BaselineThresholdSpec(
                metric_name="critical_count",
                comparison_operator="==",
                threshold_value=0.0
            ),
            "hard_law_violation_count": BaselineThresholdSpec(
                metric_name="hard_law_violation_count",
                comparison_operator="==",
                threshold_value=0.0
            ),
            "health_score": BaselineThresholdSpec(
                metric_name="health_score",
                comparison_operator=">=",
                threshold_value=p10_health
            ),
            "tick_compute_ms_p95": BaselineThresholdSpec(
                metric_name="tick_compute_ms_p95",
                comparison_operator="<=",
                threshold_value=p95_lat
            ),
            "memory_rss_bytes_max": BaselineThresholdSpec(
                metric_name="memory_rss_bytes_max",
                comparison_operator="<=",
                threshold_value=p95_mem
            ),
            "anomaly_count": BaselineThresholdSpec(
                metric_name="anomaly_count",
                comparison_operator="<=",
                threshold_value=p95_anom
            )
        }

        run_count = len(records)
        accepted_run_count = len(accepted_records)
        is_weak_baseline = accepted_run_count < 5

        baseline_id = f"baseline_{sweep_id}"
        created_at = datetime.now(timezone.utc).isoformat()

        baseline_config = BaselineConfig(
            baseline_id=baseline_id,
            scenario_name=manifest.scenario_name,
            scenario_type=manifest.scenario_type,
            created_at=created_at,
            source_sweep_id=sweep_id,
            run_count=run_count,
            accepted_run_count=accepted_run_count,
            excluded_run_ids=excluded_run_ids,
            exclusion_reasons=exclusion_reasons,
            is_weak_baseline=is_weak_baseline,
            metrics=metrics_dist,
            threshold_recommendations=recommendations
        )

        baseline_path = os.path.join(repo.base_dir, sweep_id, "baseline.json")
        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
        with open(baseline_path, "w", encoding="utf-8") as f:
            f.write(baseline_config.model_dump_json(indent=2))

        return baseline_config
