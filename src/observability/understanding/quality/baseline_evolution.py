"""
BaselineEvolutionPolicy — validates candidate baselines for promotion.
BaselinePromotionWorkflow — promotes or deprecates baseline records.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from src.observability.understanding.quality.models import BaselineStatus, BaselineStatusRecord


@dataclass
class PromotionCriteria:
    min_accepted_run_count: int = 5
    max_hard_law_violations: int = 0
    max_critical_anomalies: int = 0
    min_health_score_p10: float = 60.0


@dataclass
class ValidationResult:
    passed: bool
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BaselineEvolutionPolicy:
    """
    Validates whether a candidate baseline config meets promotion criteria.

    Reads baseline metadata from a BaselineConfig dict (not the full object,
    to avoid circular imports).
    """

    def __init__(self, criteria: Optional[PromotionCriteria] = None) -> None:
        self.criteria = criteria or PromotionCriteria()

    def validate_for_promotion(self, baseline_dict: dict) -> ValidationResult:
        """
        Validate a baseline dict (as returned by BaselineConfig.model_dump())
        against the promotion criteria.
        """
        reasons = []
        warnings = []
        passed = True

        accepted_count = baseline_dict.get("accepted_run_count", 0)
        if accepted_count < self.criteria.min_accepted_run_count:
            reasons.append(
                f"Insufficient accepted runs: {accepted_count} < {self.criteria.min_accepted_run_count}"
            )
            passed = False

        if baseline_dict.get("is_weak_baseline", True):
            warnings.append("Baseline is marked weak (< 5 accepted runs). Promote with caution.")

        # Check metrics if present
        metrics = baseline_dict.get("metrics", {})

        if "hard_law_violation_count" in metrics:
            hlv_max = metrics["hard_law_violation_count"].get("max", 0)
            if hlv_max > self.criteria.max_hard_law_violations:
                reasons.append(
                    f"Hard law violations present in runs (max={hlv_max})"
                )
                passed = False

        if "critical_count" in metrics:
            crit_max = metrics["critical_count"].get("max", 0)
            if crit_max > self.criteria.max_critical_anomalies:
                warnings.append(
                    f"Critical anomalies present in some runs (max={crit_max})"
                )

        if "health_score" in metrics:
            p10_health = metrics["health_score"].get("p10", 0.0)
            if p10_health < self.criteria.min_health_score_p10:
                reasons.append(
                    f"Health score p10 too low: {p10_health:.1f} < {self.criteria.min_health_score_p10}"
                )
                passed = False

        return ValidationResult(passed=passed, reasons=reasons, warnings=warnings)


class BaselinePromotionWorkflow:
    """
    Manages the lifecycle of baseline status records:
    promote CANDIDATE → ACTIVE, deprecate ACTIVE → DEPRECATED.
    """

    def promote(
        self,
        record: BaselineStatusRecord,
        reviewer: str = "system",
    ) -> Tuple[BaselineStatusRecord, bool]:
        """
        Promote a CANDIDATE baseline to ACTIVE.
        Returns (updated_record, success). Fails if not in CANDIDATE state.
        """
        if record.status != BaselineStatus.CANDIDATE:
            return record, False

        record.status = BaselineStatus.ACTIVE
        record.promotion_timestamp = datetime.now(timezone.utc).isoformat()
        record.reviewer = reviewer
        return record, True

    def deprecate(
        self,
        record: BaselineStatusRecord,
        reason: str,
        reviewer: str = "system",
    ) -> Tuple[BaselineStatusRecord, bool]:
        """
        Deprecate an ACTIVE baseline. Returns (updated_record, success).
        """
        if record.status != BaselineStatus.ACTIVE:
            return record, False

        record.status = BaselineStatus.DEPRECATED
        record.deprecation_reason = reason
        record.reviewer = reviewer
        return record, True

    def reject(
        self,
        record: BaselineStatusRecord,
        reason: str,
    ) -> Tuple[BaselineStatusRecord, bool]:
        """Reject a CANDIDATE baseline."""
        if record.status != BaselineStatus.CANDIDATE:
            return record, False
        record.status = BaselineStatus.REJECTED
        record.deprecation_reason = reason
        return record, True
