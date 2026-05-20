# Compliance IDs: OBS-061, OBS-062, OBS-063
from __future__ import annotations

import os
import json
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from src.observability.reporting.baseline_generator import BaselineConfig, calculate_distribution


class MetricComparison(BaseModel):
    """Result of comparing a single actual metric value against baseline expectations."""
    metric_name: str
    baseline_value: float
    actual_value: float
    status: str  # "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_DATA"
    message: str


class ComparisonResult(BaseModel):
    """Consolidated report for a single run's baseline compliance check."""
    comparison_id: str
    baseline_id: str
    run_id: str
    status: str  # "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_DATA"
    metric_comparisons: Dict[str, MetricComparison] = Field(default_factory=dict)
    failed_metrics: List[str] = Field(default_factory=list)
    warning_metrics: List[str] = Field(default_factory=list)
    summary: str
    envelope_name: Optional[str] = None


class DriftMetricSummary(BaseModel):
    """Calculated drift indicators showing performance shift direction and magnitude."""
    metric_name: str
    baseline_mean: float
    sweep_mean: float
    drift_direction: str  # "DEGRADED" | "IMPROVED" | "STABLE"
    magnitude: float


class SweepComparisonResult(BaseModel):
    """Aggregated compliance and statistical drift detection report for a simulation sweep."""
    comparison_id: str
    baseline_id: str
    sweep_id: str
    status: str  # "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_DATA"
    run_statuses: Dict[str, str] = Field(default_factory=dict)
    outlier_runs: List[str] = Field(default_factory=list)
    drifts: Dict[str, DriftMetricSummary] = Field(default_factory=dict)
    summary: str
    envelope_name: Optional[str] = None


class BaselineComparator:
    """Orchestrates validation comparing runs and sweeps against scenario statistical baselines."""

    @classmethod
    def compare_run(
        cls,
        run_id: str,
        baseline_path: str,
        run_dir: str = "data/runs",
        envelope_path: Optional[str] = None
    ) -> ComparisonResult:
        if not os.path.exists(baseline_path):
            raise FileNotFoundError(f"Baseline file not found: {baseline_path}")

        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
        baseline = BaselineConfig.model_validate(baseline_data)

        # Load envelope if provided
        envelope = None
        if envelope_path:
            from src.observability.reporting.balance_envelope import BalanceEnvelopeLoader
            envelope = BalanceEnvelopeLoader.load_from_file(envelope_path)

        # Locate run files
        target_run_dir = os.path.join(run_dir, run_id)
        if not os.path.exists(target_run_dir):
            # Fallback check under sweep run sets directories if needed
            from src.observability.reporting.run_set_repository import RunSetArtifactRepository
            possible_sets_dir = RunSetArtifactRepository().base_dir
            found = False
            if os.path.exists(possible_sets_dir):
                for sweep_folder in os.listdir(possible_sets_dir):
                    sweep_run_path = os.path.join(possible_sets_dir, sweep_folder, "runs", run_id)
                    if os.path.exists(sweep_run_path):
                        target_run_dir = sweep_run_path
                        found = True
                        break
            if not found:
                raise FileNotFoundError(f"Run directory not found for: {run_id}")

        # Extract actual values
        health_score = None
        critical_count = None
        warning_count = None
        hard_law_violation_count = None
        tick_compute_ms_p95 = None
        memory_rss_bytes_max = None
        event_count = None
        anomaly_count = None

        # Parse run_report.json or manifest
        report_path = os.path.join(target_run_dir, "run_report.json")
        manifest_path = os.path.join(target_run_dir, "run_manifest.json")

        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    rep = json.load(f)
                meta = rep.get("metadata", {})
                health_score = meta.get("health_score")
                critical_count = meta.get("errors_count", 0)  # matching errors_count/critical_count
                warning_count = meta.get("warnings_count", 0)
                hard_law_violation_count = meta.get("hard_law_violations_count", 0)
            except Exception:
                pass

        if health_score is None and os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    man = json.load(f)
                health_score = man.get("health_score", 100.0)
                hard_law_violation_count = man.get("hard_law_violations_count", 0)
                # If manifest status shows COMPLETED or RUNNING (with ticks completed), default counts to 0
                run_status = man.get("status")
                if run_status in ("COMPLETED", "RUNNING") or man.get("ticks_completed", 0) > 0:
                    critical_count = 0
                    warning_count = 0
            except Exception:
                pass

        # Load performance metrics from metric windows
        metric_file = os.path.join(target_run_dir, "metric_windows.jsonl")
        if os.path.exists(metric_file):
            try:
                p95_list = []
                rss_list = []
                events_sum = 0
                with open(metric_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            w_data = json.loads(line)
                            if "tick_compute_ms_p95" in w_data:
                                p95_list.append(w_data["tick_compute_ms_p95"])
                            if "memory_rss_bytes_max" in w_data:
                                rss_list.append(w_data["memory_rss_bytes_max"])
                            if "event_count" in w_data:
                                events_sum += w_data["event_count"]
                if p95_list:
                    tick_compute_ms_p95 = max(p95_list)
                if rss_list:
                    memory_rss_bytes_max = max(rss_list)
                event_count = events_sum
            except Exception:
                pass

        # Load anomaly count
        anomalies_file = os.path.join(target_run_dir, "anomalies.json")
        if os.path.exists(anomalies_file):
            try:
                with open(anomalies_file, "r", encoding="utf-8") as f:
                    anom_list = json.load(f)
                anomaly_count = len(anom_list)
            except Exception:
                pass

        # Map actual values
        actuals = {
            "health_score": health_score,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "hard_law_violation_count": hard_law_violation_count,
            "tick_compute_ms_p95": tick_compute_ms_p95,
            "memory_rss_bytes_max": memory_rss_bytes_max,
            "event_count": event_count,
            "anomaly_count": anomaly_count
        }

        metric_comparisons = {}
        failed_metrics = []
        warning_metrics = []

        all_metric_names = set(baseline.threshold_recommendations.keys())
        if envelope:
            all_metric_names.update(envelope.expectations.keys())

        for metric_name in sorted(all_metric_names):
            actual_val = actuals.get(metric_name)

            # Determine baseline_value
            if metric_name in baseline.threshold_recommendations:
                baseline_value = baseline.threshold_recommendations[metric_name].threshold_value
            elif metric_name in baseline.metrics:
                baseline_value = baseline.metrics[metric_name].mean
            else:
                baseline_value = 0.0

            if actual_val is None:
                # Missing telemetry metric yields INSUFFICIENT_DATA
                metric_comparisons[metric_name] = MetricComparison(
                    metric_name=metric_name,
                    baseline_value=baseline_value,
                    actual_value=0.0,
                    status="INSUFFICIENT_DATA",
                    message="Insufficient data: metric not found in actual run artifacts."
                )
                continue

            # Check if there is an envelope expectation
            expectation = envelope.expectations.get(metric_name) if envelope else None

            if expectation:
                status = "PASS"
                reasons = []

                # Check min
                if expectation.min is not None:
                    if actual_val < expectation.min:
                        status = expectation.severity
                        reasons.append(f"actual {actual_val} < min expectation {expectation.min}")
                # Check max
                if expectation.max is not None:
                    if actual_val > expectation.max:
                        status = expectation.severity
                        reasons.append(f"actual {actual_val} > max expectation {expectation.max}")
                # Check equals
                if expectation.equals is not None:
                    if actual_val != expectation.equals:
                        status = expectation.severity
                        reasons.append(f"actual {actual_val} != expectation {expectation.equals}")
                # Check max_multiplier_from_baseline
                if expectation.max_multiplier_from_baseline is not None:
                    allowed_max = baseline_value * expectation.max_multiplier_from_baseline
                    if actual_val > allowed_max:
                        status = expectation.severity
                        reasons.append(
                            f"actual {actual_val} > baseline multiplier max {allowed_max} "
                            f"(baseline {baseline_value} * {expectation.max_multiplier_from_baseline})"
                        )
                # Check min_multiplier_from_baseline
                if expectation.min_multiplier_from_baseline is not None:
                    allowed_min = baseline_value * expectation.min_multiplier_from_baseline
                    if actual_val < allowed_min:
                        status = expectation.severity
                        reasons.append(
                            f"actual {actual_val} < baseline multiplier min {allowed_min} "
                            f"(baseline {baseline_value} * {expectation.min_multiplier_from_baseline})"
                        )

                if status == "FAIL":
                    failed_metrics.append(metric_name)
                    message = f"Envelope expectation failed: {', '.join(reasons)}"
                elif status == "WARNING":
                    warning_metrics.append(metric_name)
                    message = f"Envelope expectation warning: {', '.join(reasons)}"
                else:
                    message = f"Metric meets envelope expectations: actual {actual_val}"

                metric_comparisons[metric_name] = MetricComparison(
                    metric_name=metric_name,
                    baseline_value=baseline_value,
                    actual_value=float(actual_val),
                    status=status,
                    message=message
                )
            else:
                # Standard baseline check (only if present in baseline threshold recommendations)
                if metric_name in baseline.threshold_recommendations:
                    spec = baseline.threshold_recommendations[metric_name]
                    status = "PASS"
                    message = f"Metric meets baseline recommendation: {actual_val} vs {spec.threshold_value}"

                    if spec.comparison_operator == "==":
                        if actual_val != spec.threshold_value:
                            status = "FAIL"
                            message = f"Metric mismatch: actual {actual_val} != expected {spec.threshold_value}"
                            failed_metrics.append(metric_name)

                    elif spec.comparison_operator == ">=":
                        if actual_val < spec.threshold_value:
                            if metric_name == "health_score" and actual_val < 60.0:
                                status = "FAIL"
                                message = f"Critical health drop: actual health {actual_val} < critical threshold 60.0"
                                failed_metrics.append(metric_name)
                            else:
                                status = "WARNING"
                                message = f"Metric envelope degraded: actual {actual_val} < baseline threshold {spec.threshold_value}"
                                warning_metrics.append(metric_name)

                    elif spec.comparison_operator == "<=":
                        if actual_val > spec.threshold_value:
                            status = "WARNING"
                            message = f"Metric envelope exceeded: actual {actual_val} > baseline threshold {spec.threshold_value}"
                            warning_metrics.append(metric_name)

                    metric_comparisons[metric_name] = MetricComparison(
                        metric_name=metric_name,
                        baseline_value=spec.threshold_value,
                        actual_value=float(actual_val),
                        status=status,
                        message=message
                    )

        # Overall status resolution
        if failed_metrics:
            overall_status = "FAIL"
        elif warning_metrics:
            overall_status = "WARNING"
        elif any(c.status == "INSUFFICIENT_DATA" for c in metric_comparisons.values()):
            overall_status = "INSUFFICIENT_DATA"
        else:
            overall_status = "PASS"

        summary = f"Comparison completed with status: {overall_status}."
        if failed_metrics:
            summary += f" Failed metrics: {', '.join(failed_metrics)}."
        if warning_metrics:
            summary += f" Warnings raised on: {', '.join(warning_metrics)}."

        result = ComparisonResult(
            comparison_id=f"comp_{run_id}",
            baseline_id=baseline.baseline_id,
            run_id=run_id,
            status=overall_status,
            metric_comparisons=metric_comparisons,
            failed_metrics=failed_metrics,
            warning_metrics=warning_metrics,
            summary=summary,
            envelope_name=envelope.scenario_name if envelope else None
        )

        # Write result to baseline_comparison.json inside target run directory
        result_path = os.path.join(target_run_dir, "baseline_comparison.json")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        return result

    @classmethod
    def compare_sweep(
        cls,
        sweep_id: str,
        baseline_path: str,
        base_dir: str = "data/run_sets",
        envelope_path: Optional[str] = None
    ) -> SweepComparisonResult:
        if not os.path.exists(baseline_path):
            raise FileNotFoundError(f"Baseline file not found: {baseline_path}")

        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
        baseline = BaselineConfig.model_validate(baseline_data)

        # Load envelope if provided to extract name
        envelope = None
        if envelope_path:
            from src.observability.reporting.balance_envelope import BalanceEnvelopeLoader
            envelope = BalanceEnvelopeLoader.load_from_file(envelope_path)

        from src.observability.reporting.run_set_repository import RunSetArtifactRepository
        repo = RunSetArtifactRepository(base_dir=base_dir)
        resolved_base_dir = repo.base_dir
        records = repo.read_run_index(sweep_id)

        run_statuses = {}
        outlier_runs = []
        completed_runs_metrics = {
            "health_score": [],
            "tick_compute_ms_p95": [],
            "memory_rss_bytes_max": [],
            "anomaly_count": []
        }

        # Compare individual runs
        for r in records:
            # Find run path
            run_path = os.path.join(resolved_base_dir, sweep_id, "runs", r.run_id)
            comp = cls.compare_run(
                r.run_id,
                baseline_path,
                run_dir=os.path.join(resolved_base_dir, sweep_id, "runs"),
                envelope_path=envelope_path
            )
            run_statuses[r.run_id] = comp.status

            if r.status == "COMPLETED":
                # Check for outliers
                # 1. Health score < p10
                baseline_p10_health = baseline.metrics["health_score"].p10
                if r.health_score < baseline_p10_health:
                    outlier_runs.append(r.run_id)

                # Read run telemetry details for drifts
                tick_p95 = 0.0
                mem_rss = 0.0
                anoms = r.critical_count + r.warning_count

                metric_file = os.path.join(run_path, "metric_windows.jsonl")
                if os.path.exists(metric_file):
                    try:
                        p95_list = []
                        rss_list = []
                        with open(metric_file, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip():
                                    w_data = json.loads(line)
                                    if "tick_compute_ms_p95" in w_data:
                                        p95_list.append(w_data["tick_compute_ms_p95"])
                                    if "memory_rss_bytes_max" in w_data:
                                        rss_list.append(w_data["memory_rss_bytes_max"])
                        if p95_list:
                            tick_p95 = max(p95_list)
                        if rss_list:
                            mem_rss = max(rss_list)
                    except Exception:
                        pass

                completed_runs_metrics["health_score"].append(r.health_score)
                completed_runs_metrics["tick_compute_ms_p95"].append(tick_p95)
                completed_runs_metrics["memory_rss_bytes_max"].append(mem_rss)
                completed_runs_metrics["anomaly_count"].append(float(anoms))

        # Outliers check based on telemetry metrics
        for r in records:
            if r.status == "COMPLETED" and r.run_id not in outlier_runs:
                # 2. Anomaly count > baseline p95
                baseline_p95_anom = baseline.metrics["anomaly_count"].p95
                anoms = r.critical_count + r.warning_count
                if anoms > baseline_p95_anom:
                    outlier_runs.append(r.run_id)
                    continue

                # 3. Peak RSS > baseline p95
                run_path = os.path.join(resolved_base_dir, sweep_id, "runs", r.run_id)
                metric_file = os.path.join(run_path, "metric_windows.jsonl")
                if os.path.exists(metric_file):
                    try:
                        rss_list = []
                        with open(metric_file, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip():
                                    w_data = json.loads(line)
                                    if "memory_rss_bytes_max" in w_data:
                                        rss_list.append(w_data["memory_rss_bytes_max"])
                        if rss_list and max(rss_list) > baseline.metrics["memory_rss_bytes_max"].p95:
                            outlier_runs.append(r.run_id)
                    except Exception:
                        pass

        # Calculate drifts
        drifts = {}
        for metric, vals in completed_runs_metrics.items():
            baseline_dist = baseline.metrics.get(metric)
            if not baseline_dist or not vals:
                continue

            sweep_dist = calculate_distribution(vals)
            magnitude = sweep_dist.mean - baseline_dist.mean

            drift_direction = "STABLE"
            if abs(magnitude) > 1e-5:
                if metric == "health_score":
                    drift_direction = "IMPROVED" if magnitude > 0 else "DEGRADED"
                else:  # tick_compute_ms_p95, memory_rss_bytes_max, anomaly_count
                    drift_direction = "IMPROVED" if magnitude < 0 else "DEGRADED"

            drifts[metric] = DriftMetricSummary(
                metric_name=metric,
                baseline_mean=baseline_dist.mean,
                sweep_mean=sweep_dist.mean,
                drift_direction=drift_direction,
                magnitude=magnitude
            )

        # Derive sweep status
        statuses = list(run_statuses.values())
        if "FAIL" in statuses:
            overall_status = "FAIL"
        elif "WARNING" in statuses:
            overall_status = "WARNING"
        elif "INSUFFICIENT_DATA" in statuses:
            overall_status = "INSUFFICIENT_DATA"
        else:
            overall_status = "PASS"

        summary = f"Sweep baseline comparison finished with status: {overall_status}."
        if outlier_runs:
            summary += f" Identified {len(outlier_runs)} outlier run seeds: {', '.join(outlier_runs)}."

        result = SweepComparisonResult(
            comparison_id=f"sweep_comp_{sweep_id}",
            baseline_id=baseline.baseline_id,
            sweep_id=sweep_id,
            status=overall_status,
            run_statuses=run_statuses,
            outlier_runs=outlier_runs,
            drifts=drifts,
            summary=summary,
            envelope_name=envelope.scenario_name if envelope else None
        )

        # Save output to sweep_baseline_comparison.json inside sweep folder
        result_path = os.path.join(resolved_base_dir, sweep_id, "sweep_baseline_comparison.json")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        return result
