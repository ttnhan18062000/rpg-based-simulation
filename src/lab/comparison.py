# Compliance IDs: BALANCE-COMPARE-001, BALANCE-COMPARE-002, BALANCE-COMPARE-003
from __future__ import annotations
import json
import re
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any

from src.lab.metamorphic import MetamorphicComparisonResult


class BalanceComparisonReport(BaseModel):
    """Structured report detailing the differential metrics and balance shifts between variants."""
    model_config = ConfigDict(frozen=True)

    status: str = Field(..., description="Classification: IMPROVED | REGRESSED | UNCHANGED | MIXED | INSUFFICIENT_DATA")
    evidence: dict[str, dict[str, Any]] = Field(..., description="Mapping of compared metrics evidence")
    metamorphic_summary: dict[str, int] = Field(..., description="Counts of metamorphic rule evaluations")
    explanation: str = Field(..., description="Scientifically humble, correlative analysis description")


class BalanceComparisonEngine:
    """Differential engine comparing metrics and classifying RPG simulation balance shifts."""

    @staticmethod
    def compare(
        baseline_metrics: dict[str, Any],
        mutated_metrics: dict[str, Any],
        metamorphic_results: Optional[list[MetamorphicComparisonResult]] = None
    ) -> BalanceComparisonReport:
        """
        Performs a differential analysis comparing mutated_metrics against baseline_metrics.
        Optionally integrates metamorphic validation rules.
        """
        # 1. Check for insufficient data
        if not baseline_metrics or not mutated_metrics:
            return BalanceComparisonReport(
                status="INSUFFICIENT_DATA",
                evidence={},
                metamorphic_summary={"passed": 0, "failed": 0, "insufficient": 0},
                explanation="Comparison could not be performed due to completely missing variant metrics."
            )

        # Essential check: health_score must exist
        if "health_score" not in baseline_metrics or "health_score" not in mutated_metrics:
            return BalanceComparisonReport(
                status="INSUFFICIENT_DATA",
                evidence={},
                metamorphic_summary={"passed": 0, "failed": 0, "insufficient": 0},
                explanation="Essential metric 'health_score' is missing from one or both variants."
            )

        # Define dimension directions
        higher_better_dimensions = {
            "health_score",
            "resource_production",
            "resource_production_rate",
            "quest_completion",
            "quest_completion_rate",
            "combat_resolution"
        }
        lower_better_dimensions = {
            "hard_law_violations",
            "hard_law_violation_count",
            "critical_anomalies",
            "critical_count",
            "stuck_entity_ratio",
            "stuck_ratio",
            "runtime_performance",
            "execution_time_seconds",
            "memory_usage",
            "memory_usage_mb",
            "event_volume"
        }

        evidence = {}
        better_count = 0
        worse_count = 0
        stable_count = 0

        # Combine all present keys
        all_keys = set(baseline_metrics.keys()).union(mutated_metrics.keys())
        comparable_keys = all_keys.intersection(higher_better_dimensions.union(lower_better_dimensions))

        for metric in sorted(list(comparable_keys)):
            b_val = baseline_metrics.get(metric)
            m_val = mutated_metrics.get(metric)

            if b_val is None or m_val is None:
                continue

            try:
                b_val_f = float(b_val)
                m_val_f = float(m_val)
            except (ValueError, TypeError):
                continue

            shift = m_val_f - b_val_f
            evidence[metric] = {
                "baseline": b_val_f,
                "compared": m_val_f,
                "shift": shift
            }

            # Determine direction of shift
            if metric in higher_better_dimensions:
                if m_val_f > b_val_f:
                    better_count += 1
                elif m_val_f < b_val_f:
                    worse_count += 1
                else:
                    stable_count += 1
            elif metric in lower_better_dimensions:
                if m_val_f < b_val_f:
                    better_count += 1
                elif m_val_f > b_val_f:
                    worse_count += 1
                else:
                    stable_count += 1

        # 2. Check metamorphic rules and violations
        passed_m = 0
        failed_m = 0
        insufficient_m = 0
        if metamorphic_results:
            for r in metamorphic_results:
                if r.status == "PASSED":
                    passed_m += 1
                elif r.status == "FAILED":
                    failed_m += 1
                else:
                    insufficient_m += 1

        # Check hard law violations directly
        violations_baseline = baseline_metrics.get("hard_law_violations", baseline_metrics.get("hard_law_violation_count", 0))
        violations_mutated = mutated_metrics.get("hard_law_violations", mutated_metrics.get("hard_law_violation_count", 0))
        has_increased_violations = False
        if violations_baseline is not None and violations_mutated is not None:
            try:
                if int(violations_mutated) > int(violations_baseline) or int(violations_mutated) > 0:
                    has_increased_violations = True
            except (ValueError, TypeError):
                pass

        # 3. Classify Overall Shift
        if failed_m > 0 or has_increased_violations:
            status = "REGRESSED"
        elif worse_count > 0 and better_count > 0:
            status = "MIXED"
        elif worse_count > 0 and better_count == 0:
            status = "REGRESSED"
        elif better_count > 0 and worse_count == 0:
            status = "IMPROVED"
        else:
            status = "UNCHANGED"

        # 4. Generate Scientifically Humble Explanation
        base_h = evidence["health_score"]["baseline"]
        comp_h = evidence["health_score"]["compared"]

        explanation_clauses = [
            f"Variant analysis indicates that the applied mutation correlates with the observed performance shifts.",
            f"The health score changed from {base_h:.1f} to {comp_h:.1f}."
        ]

        if status == "IMPROVED":
            explanation_clauses.append("This shift is associated with general balance improvements across comparable dimensions.")
        elif status == "REGRESSED":
            explanation_clauses.append("The metrics indicate a regression in simulation stability or specific constraint satisfaction.")
        elif status == "MIXED":
            explanation_clauses.append("The results co-occur with a mix of positive and negative shifts across different dimensions.")
        else:
            explanation_clauses.append("The metrics remain stable and unchanged relative to baseline parameters.")

        explanation_clauses.append("Note: These correlations do not establish direct causal proof or a single root cause, as complex emergent simulation variables remain associated with the outcomes.")

        explanation = " ".join(explanation_clauses)

        # Safety Gate: Guarantee no causal certainty phrases are present in the final output
        causal_certainties = ["caused by", "proves that", "directly resulted from", "is the root cause of", "causation"]
        for phrase in causal_certainties:
            explanation = re.sub(phrase, "correlates with", explanation, flags=re.IGNORECASE)

        return BalanceComparisonReport(
            status=status,
            evidence=evidence,
            metamorphic_summary={
                "passed": passed_m,
                "failed": failed_m,
                "insufficient": insufficient_m
            },
            explanation=explanation
        )

    @staticmethod
    def write_reports(output_dir: Path, report: BalanceComparisonReport) -> None:
        """
        Serializes and writes the balance comparison report to:
        - balance_comparison.json
        - balance_comparison.md
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(output_dir / "balance_comparison.json", "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        # Write Markdown
        md_path = output_dir / "balance_comparison.md"
        status_badge = (
            "🟢 **IMPROVED**" if report.status == "IMPROVED"
            else "🔴 **REGRESSED**" if report.status == "REGRESSED"
            else "🟡 **MIXED**" if report.status == "MIXED"
            else "⚪ **UNCHANGED**" if report.status == "UNCHANGED"
            else "➖ **INSUFFICIENT_DATA**"
        )

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Balance Comparison Scorecard\n\n")
            f.write(f"## Status: {status_badge}\n\n")
            f.write(f"### Analytical Summary\n")
            f.write(f"> {report.explanation}\n\n")

            f.write(f"## Telemetry Evidence Scorecard\n\n")
            f.write(f"| Dimension Metric Name | Baseline Value | Compared Value | Delta Shift |\n")
            f.write(f"| :--- | :--- | :--- | :--- |\n")

            for metric, data in sorted(report.evidence.items()):
                b = data["baseline"]
                c = data["compared"]
                s = data["shift"]
                sign = "+" if s > 0 else ""
                f.write(f"| `{metric}` | `{b:.2f}` | `{c:.2f}` | `{sign}{s:.2f}` |\n")

            f.write(f"\n## Metamorphic Rules Validation Summary\n\n")
            f.write(f"- **Passed assertions**: `{report.metamorphic_summary['passed']}`\n")
            f.write(f"- **Failed assertions**: `{report.metamorphic_summary['failed']}`\n")
            f.write(f"- **Insufficient data assertions**: `{report.metamorphic_summary['insufficient']}`\n")
