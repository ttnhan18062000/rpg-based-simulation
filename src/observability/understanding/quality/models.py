"""Analyzer Quality and Baseline Evolution models."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class BaselineStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"


@dataclass
class RuleQualityMetrics:
    rule_name: str
    total_findings: int = 0
    reviewed: int = 0
    confirmed_bugs: int = 0
    false_positives: int = 0
    expected_behavior: int = 0
    balance_issues: int = 0
    unreviewed: int = 0

    @property
    def unreviewed_rate(self) -> float:
        if self.total_findings == 0:
            return 0.0
        return self.unreviewed / self.total_findings

    @property
    def false_positive_rate(self) -> float:
        if self.reviewed == 0:
            return 0.0
        return self.false_positives / self.reviewed

    @property
    def signal_rate(self) -> float:
        """Fraction of reviews that are actionable (bug or balance issue)."""
        if self.reviewed == 0:
            return 0.0
        return (self.confirmed_bugs + self.balance_issues) / self.reviewed

    def is_noisy(self) -> bool:
        """Rule is considered noisy if FP rate > 50% with ≥ 5 reviewed findings."""
        return self.reviewed >= 5 and self.false_positive_rate > 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "total_findings": self.total_findings,
            "reviewed": self.reviewed,
            "confirmed_bugs": self.confirmed_bugs,
            "false_positives": self.false_positives,
            "expected_behavior": self.expected_behavior,
            "balance_issues": self.balance_issues,
            "unreviewed": self.unreviewed,
            "unreviewed_rate": round(self.unreviewed_rate, 3),
            "false_positive_rate": round(self.false_positive_rate, 3),
            "signal_rate": round(self.signal_rate, 3),
            "is_noisy": self.is_noisy(),
        }


@dataclass
class AnalyzerQualityReport:
    generated_at: str = ""
    rule_metrics: List[RuleQualityMetrics] = field(default_factory=list)

    def noisy_rules(self) -> List[RuleQualityMetrics]:
        return [m for m in self.rule_metrics if m.is_noisy()]

    def unreviewed_heavy_rules(self, threshold: float = 0.7) -> List[RuleQualityMetrics]:
        return [m for m in self.rule_metrics if m.unreviewed_rate >= threshold]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_rules": len(self.rule_metrics),
            "noisy_rule_count": len(self.noisy_rules()),
            "rule_metrics": [m.to_dict() for m in self.rule_metrics],
        }


@dataclass
class BaselineStatusRecord:
    """Wraps a baseline_id with lifecycle status."""
    baseline_id: str
    scenario_type: str
    status: BaselineStatus = BaselineStatus.CANDIDATE
    promotion_timestamp: Optional[str] = None
    reviewer: Optional[str] = None
    deprecation_reason: Optional[str] = None
    schema_version: str = "baseline_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "scenario_type": self.scenario_type,
            "status": self.status.value,
            "promotion_timestamp": self.promotion_timestamp,
            "reviewer": self.reviewer,
            "deprecation_reason": self.deprecation_reason,
            "schema_version": self.schema_version,
        }
