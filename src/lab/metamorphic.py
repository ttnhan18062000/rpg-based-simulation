# Compliance IDs: METAMORPHIC-RULE-001, METAMORPHIC-RULE-002, METAMORPHIC-RULE-003
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any

from src.lab.schema import ExpectedRelationshipSpec


class MetamorphicComparisonResult(BaseModel):
    """Represents the compiled outcome of evaluating a metamorphic relationship assertion."""
    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., description="Unique ID of the metamorphic rule specification")
    status: str = Field(..., description="Status of evaluation: PASSED | FAILED | INSUFFICIENT_DATA")
    weak_evidence: bool = Field(False, description="Flagged if either variant had low run counts (seeds < 3)")
    baseline_value: Optional[float] = Field(None, description="Actual metric value of the baseline variant")
    compared_value: Optional[float] = Field(None, description="Actual metric value of the compared variant")
    message: str = Field(..., description="Explanatory notes regarding validation outcome")


class MetamorphicRule:
    """Represents a single metamorphic assertion wrapping ExpectedRelationshipSpec."""
    def __init__(self, spec: ExpectedRelationshipSpec):
        self.spec = spec

    def evaluate(self, variant_metrics: dict[str, dict[str, Any]]) -> MetamorphicComparisonResult:
        """
        Evaluates this metamorphic rule against a dictionary of metrics for each variant ID.
        Returns a MetamorphicComparisonResult.
        """
        rule_id = self.spec.id
        metric_name = self.spec.metric
        rule_type = self.spec.type
        baseline_id = self.spec.baseline_variant
        compared_id = self.spec.compared_variant

        # 1. Check variant existence in data
        if baseline_id not in variant_metrics:
            return MetamorphicComparisonResult(
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                message=f"Baseline variant '{baseline_id}' has no recorded metrics."
            )
        if compared_id not in variant_metrics:
            return MetamorphicComparisonResult(
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                message=f"Compared variant '{compared_id}' has no recorded metrics."
            )

        baseline_data = variant_metrics[baseline_id]
        compared_data = variant_metrics[compared_id]

        # 2. Check metric existence in both variants
        if metric_name not in baseline_data:
            return MetamorphicComparisonResult(
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                message=f"Metric '{metric_name}' is missing in baseline variant '{baseline_id}'."
            )
        if metric_name not in compared_data:
            return MetamorphicComparisonResult(
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                message=f"Metric '{metric_name}' is missing in compared variant '{compared_id}'."
            )

        baseline_val = baseline_data[metric_name]
        compared_val = compared_data[metric_name]

        # Handle None values as insufficient data
        if baseline_val is None or compared_val is None:
            return MetamorphicComparisonResult(
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                message=f"Metric '{metric_name}' has null values in one or more variants."
            )

        try:
            baseline_val = float(baseline_val)
            compared_val = float(compared_val)
        except (ValueError, TypeError):
            return MetamorphicComparisonResult(
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                message=f"Metric '{metric_name}' value cannot be converted to float."
            )

        # 3. Detect weak evidence (run_count < 3)
        weak_evidence = False
        baseline_runs = baseline_data.get("run_count")
        compared_runs = compared_data.get("run_count")
        if baseline_runs is not None and compared_runs is not None:
            try:
                if int(baseline_runs) < 3 or int(compared_runs) < 3:
                    weak_evidence = True
            except (ValueError, TypeError):
                pass

        # 4. Perform evaluation checks based on type
        passed = False
        notes = ""

        if rule_type == "monotonic_non_decreasing":
            passed = (compared_val >= baseline_val)
            notes = f"Assertion: non-decreasing. Baseline={baseline_val}, Compared={compared_val}"

        elif rule_type == "monotonic_non_increasing":
            passed = (compared_val <= baseline_val)
            notes = f"Assertion: non-increasing. Baseline={baseline_val}, Compared={compared_val}"

        elif rule_type == "within_tolerance":
            tol = self.spec.tolerance if self.spec.tolerance is not None else 0.0
            passed = (abs(compared_val - baseline_val) <= tol)
            notes = f"Assertion: within tolerance (+/-{tol}). Baseline={baseline_val}, Compared={compared_val}"

        elif rule_type == "expected_worse":
            # Map unfavorable directions
            # Metrics where higher count is worse
            higher_worse_metrics = {"stuck_entity_ratio", "inventory_full_ratio", "hard_law_violations", "hard_law_violation_count"}
            if metric_name in higher_worse_metrics:
                passed = (compared_val > baseline_val)
            else:
                passed = (compared_val < baseline_val)
            notes = f"Assertion: intentionally worse metric. Baseline={baseline_val}, Compared={compared_val}"

        elif rule_type == "expected_better":
            # Map favorable directions
            # Metrics where lower count is better (worse = higher)
            lower_better_metrics = {"stuck_entity_ratio", "inventory_full_ratio", "hard_law_violations", "hard_law_violation_count"}
            if metric_name in lower_better_metrics:
                passed = (compared_val < baseline_val)
            else:
                passed = (compared_val > baseline_val)
            notes = f"Assertion: intentionally better metric. Baseline={baseline_val}, Compared={compared_val}"

        elif rule_type == "no_new_hard_law_violation":
            passed = (compared_val <= baseline_val)
            notes = f"Assertion: no new hard law violations. Baseline={baseline_val}, Compared={compared_val}"

        else:
            return MetamorphicComparisonResult(
                rule_id=rule_id,
                status="FAILED",
                baseline_value=baseline_val,
                compared_value=compared_val,
                weak_evidence=weak_evidence,
                message=f"Unrecognized metamorphic rule type: '{rule_type}'."
            )

        status = "PASSED" if passed else "FAILED"
        return MetamorphicComparisonResult(
            rule_id=rule_id,
            status=status,
            weak_evidence=weak_evidence,
            baseline_value=baseline_val,
            compared_value=compared_val,
            message=notes
        )


class MetamorphicRuleEngine:
    """Core evaluation engine executing metamorphic relationship assertions."""
    @staticmethod
    def evaluate_rules(
        rules: list[ExpectedRelationshipSpec],
        variant_metrics: dict[str, dict[str, Any]]
    ) -> list[MetamorphicComparisonResult]:
        """
        Evaluates a sequence of metamorphic rules against the loaded variant metrics collection.
        """
        results = []
        for spec in rules:
            rule = MetamorphicRule(spec)
            results.append(rule.evaluate(variant_metrics))
        return results
