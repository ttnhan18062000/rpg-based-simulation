# Compliance IDs: OBS-051, OBS-052, OBS-053
from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.observability.reporting.baseline_comparator import BaselineComparator, SweepComparisonResult
from src.observability.reporting.run_set_repository import RunSetArtifactRepository

logger = logging.getLogger(__name__)


class CIGateResult(BaseModel):
    """Result schema for the CI pass/fail gate evaluation."""
    status: str  # "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_DATA"
    failed_metrics: List[str] = Field(default_factory=list)
    warning_metrics: List[str] = Field(default_factory=list)
    failed_runs: List[str] = Field(default_factory=list)
    outlier_runs: List[str] = Field(default_factory=list)
    baseline_id: str
    sweep_id: str
    message: str


class SweepReportGenerator:
    """Generates scenario-level Markdown and JSON reports for sweeps, and runs the CI gate."""

    @staticmethod
    def generate(
        sweep_id: str,
        baseline_path: str,
        envelope_path: Optional[str] = None,
        base_dir: str = "data/run_sets",
        warn_as_fail: bool = False,
        insufficient_as_fail: bool = False
    ) -> tuple[str, str, CIGateResult]:
        """
        Orchestrates scenario-level sweep comparison, generates report files, and evaluates CI gating.
        
        Returns:
            A tuple of (markdown_report_path, json_report_path, ci_gate_result)
        """
        repo = RunSetArtifactRepository(base_dir=base_dir)
        resolved_base_dir = repo.base_dir
        sweep_dir = os.path.join(resolved_base_dir, sweep_id)

        if not os.path.exists(sweep_dir):
            raise FileNotFoundError(f"Sweep directory not found: {sweep_dir}")

        # 1. Run sweep comparison to ensure we have up-to-date baseline gating outcomes
        comparison: SweepComparisonResult = BaselineComparator.compare_sweep(
            sweep_id=sweep_id,
            baseline_path=baseline_path,
            envelope_path=envelope_path,
            base_dir=base_dir
        )

        # 2. Load sweep metadata
        manifest_path = repo.resolve_path(sweep_id, "manifest")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        summary_path = repo.resolve_path(sweep_id, "summary")
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        records = repo.read_run_index(sweep_id)

        # Load baseline config metadata
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
        baseline_id = baseline_data.get("baseline_id", "unknown")
        baseline_run_count = baseline_data.get("run_count", 0)

        # Identify failed metrics and failed runs
        failed_metrics: List[str] = []
        warning_metrics: List[str] = []
        failed_runs: List[str] = [r.run_id for r in records if r.status == "FAILED"]

        # Collate individual run metric failures/warnings from comparison results
        for r in records:
            run_comp_path = os.path.join(sweep_dir, "runs", r.run_id, "baseline_comparison.json")
            if os.path.exists(run_comp_path):
                try:
                    with open(run_comp_path, "r", encoding="utf-8") as f:
                        rc_data = json.load(f)
                        for fm in rc_data.get("failed_metrics", []):
                            if fm not in failed_metrics:
                                failed_metrics.append(fm)
                        for wm in rc_data.get("warning_metrics", []):
                            if wm not in warning_metrics:
                                warning_metrics.append(wm)
                except Exception as e:
                    logger.error(f"Failed parsing run comparison result for {r.run_id}: {e}")

        # 3. Evaluate CI Gate Result
        gate_status = "PASS"
        gate_message = "All validation checks passed successfully."

        if comparison.status == "FAIL":
            gate_status = "FAIL"
            gate_message = "CI Gate failed: Baseline comparison or custom envelope expectations were failed."
        elif failed_runs:
            gate_status = "FAIL"
            gate_message = f"CI Gate failed: {len(failed_runs)} run(s) failed execution inside the sweep."
        elif comparison.status == "WARNING":
            if warn_as_fail:
                gate_status = "FAIL"
                gate_message = "CI Gate failed: Warnings detected and --warn-as-fail is enabled."
            else:
                gate_status = "WARNING"
                gate_message = "CI Gate passed with warnings."
        elif comparison.status == "INSUFFICIENT_DATA":
            if insufficient_as_fail:
                gate_status = "FAIL"
                gate_message = "CI Gate failed: Insufficient data detected and --insufficient-as-fail is enabled."
            else:
                gate_status = "INSUFFICIENT_DATA"
                gate_message = "CI Gate returned status: INSUFFICIENT_DATA."

        gate_result = CIGateResult(
            status=gate_status,
            failed_metrics=failed_metrics,
            warning_metrics=warning_metrics,
            failed_runs=failed_runs,
            outlier_runs=comparison.outlier_runs,
            baseline_id=baseline_id,
            sweep_id=sweep_id,
            message=gate_message
        )

        # Save ci_gate_result.json
        gate_result_path = os.path.join(sweep_dir, "ci_gate_result.json")
        with open(gate_result_path, "w", encoding="utf-8") as f:
            f.write(gate_result.model_dump_json(indent=2))

        # 4. Generate Markdown report containing all 12 required sections
        md_content = []
        status_color = "🔴 FAIL" if gate_status == "FAIL" else ("🟡 WARNING" if gate_status in ("WARNING", "INSUFFICIENT_DATA") else "🟢 PASS")

        # Section 1: Executive Summary
        md_content.append(f"# Sweep Observability & Validation Report: {status_color}\n")
        if gate_status == "FAIL":
            md_content.append(f"> [!CAUTION]\n> **CI GATE STATUS**: **FAIL**\n> {gate_message}\n")
        elif gate_status == "WARNING":
            md_content.append(f"> [!WARNING]\n> **CI GATE STATUS**: **WARNING**\n> {gate_message}\n")
        else:
            md_content.append(f"> [!NOTE]\n> **CI GATE STATUS**: **PASS**\n> {gate_message}\n")

        md_content.append(f"Aggregated average health score: **{summary_data.get('average_health_score', 0.0):.2f}** across **{summary_data.get('total_runs', 0)}** runs.\n")

        # Section 2: Sweep Metadata
        md_content.append("## 2. Sweep Metadata\n")
        md_content.append(f"- **Sweep ID**: `{sweep_id}`")
        md_content.append(f"- **Scenario Name**: `{manifest_data.get('scenario_name', 'unknown')}`")
        md_content.append(f"- **Scenario Type**: `{manifest_data.get('scenario_type', 'unknown')}`")
        md_content.append(f"- **Requested Ticks**: `{manifest_data.get('ticks_requested', 0)}`")
        md_content.append(f"- **Started At**: `{manifest_data.get('started_at', 'unknown')}`")
        md_content.append(f"- **Ended At**: `{manifest_data.get('ended_at', 'unknown')}`\n")

        # Section 3: Run Distribution
        md_content.append("## 3. Run Distribution\n")
        md_content.append(f"- **Total Runs**: `{summary_data.get('total_runs', 0)}`")
        md_content.append(f"- **Completed Runs**: `{summary_data.get('completed_runs', 0)}`")
        md_content.append(f"- **Failed Runs**: `{summary_data.get('failed_runs', 0)}`\n")

        # Section 4: Baseline Summary
        md_content.append("## 4. Baseline Summary\n")
        md_content.append(f"- **Baseline ID**: `{baseline_id}`")
        md_content.append(f"- **Baseline Sample Size**: `{baseline_run_count} runs`\n")

        # Section 5: Comparison Result
        md_content.append("## 5. Comparison Result\n")
        md_content.append(f"Gating status: **{comparison.status}**")
        md_content.append("| Run ID | Run Status | Comparison Status | Health Score |")
        md_content.append("| :--- | :--- | :--- | :--- |")
        for rec in records:
            run_status = comparison.run_statuses.get(rec.run_id, "UNKNOWN")
            md_content.append(f"| `{rec.run_id}` | {rec.status} | **{run_status}** | {rec.health_score:.1f} |")
        md_content.append("")

        # Section 6: Outlier Seeds
        md_content.append("## 6. Outlier Seeds\n")
        if comparison.outlier_runs:
            md_content.append("The following outlier seeds were detected shifting away from baseline distributions:")
            for o_run in comparison.outlier_runs:
                md_content.append(f"- Run ID: `{o_run}`")
        else:
            md_content.append("No statistical outlier seeds were detected in this sweep.\n")
        md_content.append("")

        # Section 7: Most Common Anomalies
        md_content.append("## 7. Most Common Anomalies\n")
        anom_mapping = summary_data.get("most_common_anomaly_rule_ids", {})
        if anom_mapping:
            md_content.append("| Anomaly Rule ID | Trigger Count |")
            md_content.append("| :--- | :--- |")
            for rule_id, count in sorted(anom_mapping.items(), key=lambda item: item[1], reverse=True):
                md_content.append(f"| `{rule_id}` | {count} |")
        else:
            md_content.append("No anomalies triggered during this sweep.\n")
        md_content.append("")

        # Helper method for drift formatting
        def get_drift_section(metric_name: str) -> str:
            d_val = comparison.drifts.get(metric_name)
            if d_val:
                dir_symbol = "📈" if d_val.drift_direction == "IMPROVED" else ("📉" if d_val.drift_direction == "DEGRADED" else "➡️")
                return (f"- **Drift**: {d_val.drift_direction} {dir_symbol}\n"
                        f"- **Baseline Mean**: `{d_val.baseline_mean:.4f}`\n"
                        f"- **Sweep Mean**: `{d_val.sweep_mean:.4f}`\n"
                        f"- **Magnitude Shift**: `{d_val.magnitude:+.4f}`\n")
            return "No drift telemetry recorded.\n"

        # Section 8: Performance Drift
        md_content.append("## 8. Performance Drift\n")
        md_content.append(get_drift_section("tick_compute_ms_p95"))

        # Section 9: Memory Drift
        md_content.append("## 9. Memory Drift\n")
        md_content.append(get_drift_section("memory_rss_bytes_max"))

        # Section 10: Health Score Distribution
        md_content.append("## 10. Health Score Distribution\n")
        md_content.append(get_drift_section("health_score"))

        # Section 11: Failed Expectations
        md_content.append("## 11. Failed Expectations\n")
        if failed_metrics:
            md_content.append("Expectation checks failed for the following telemetry metrics across the sweep:")
            for fm in failed_metrics:
                md_content.append(f"- **Failed Metric**: `{fm}`")
        else:
            md_content.append("All custom envelope and baseline metric expectations met.\n")
        md_content.append("")

        # Section 12: Recommended Investigation Points
        md_content.append("## 12. Recommended Investigation Points\n")
        inv_points = []
        if failed_runs:
            inv_points.append(f"🔍 **Execute diagnostics on crashed runs**: Run execution failed for run seeds: {', '.join(failed_runs)}.")
        if comparison.outlier_runs:
            inv_points.append(f"⚠️ **Outlier analysis needed**: Seeds `{', '.join(comparison.outlier_runs)}` were marked as outliers due to elevated anomaly rates or high RSS memory peaks. Replay these seeds locally with debug logs.")
        if failed_metrics:
            inv_points.append(f"📊 **Expectation threshold drift**: Metric(s) `{', '.join(failed_metrics)}` exceeded expectations. Review combat or economic mechanics configs causing this shift.")
        
        # Check for degrading drifts
        degraded_metrics = [m for m, d in comparison.drifts.items() if d.drift_direction == "DEGRADED"]
        if degraded_metrics:
            inv_points.append(f"📉 **Overall system degradation**: Systematic degradation detected in `{', '.join(degraded_metrics)}` averages. Inspect recent performance or memory leaks in the engine kernel.")

        if not inv_points:
            inv_points.append("✅ **All metrics nominal**: The system is fully compliant and balanced. No investigation points identified.")

        for pt in inv_points:
            md_content.append(pt + "\n")

        # Save Markdown Report
        md_report_path = os.path.join(sweep_dir, "sweep_report.md")
        with open(md_report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

        # 5. Generate JSON report
        json_report_data = {
            "sweep_id": sweep_id,
            "scenario_name": manifest_data.get("scenario_name", "unknown"),
            "scenario_type": manifest_data.get("scenario_type", "unknown"),
            "status": comparison.status,
            "total_runs": summary_data.get("total_runs", 0),
            "completed_count": summary_data.get("completed_runs", 0),
            "failed_count": summary_data.get("failed_runs", 0),
            "average_health_score": summary_data.get("average_health_score", 0.0),
            "worst_run_id": summary_data.get("worst_run_id"),
            "best_run_id": summary_data.get("best_run_id"),
            "most_common_anomalies": anom_mapping,
            "outliers": comparison.outlier_runs,
            "drifts": {
                m: {
                    "metric_name": d.metric_name,
                    "baseline_mean": d.baseline_mean,
                    "sweep_mean": d.sweep_mean,
                    "drift_direction": d.drift_direction,
                    "magnitude": d.magnitude
                }
                for m, d in comparison.drifts.items()
            },
            "failed_metrics": failed_metrics,
            "warning_metrics": warning_metrics,
            "ci_gate": {
                "status": gate_status,
                "message": gate_message
            }
        }

        json_report_path = os.path.join(sweep_dir, "sweep_report.json")
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(json_report_data, f, indent=2)

        return md_report_path, json_report_path, gate_result
