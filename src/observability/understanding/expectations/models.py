"""
Scenario Expectation Pack models.

Defines what "normal" means for each scenario type. The same anomaly can
have different severity depending on scenario context:
- High combat rate: bad in peaceful_village, expected in combat_heavy
- Zero combat: expected in peaceful_village, suspicious in combat_heavy
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExpectationRule:
    """
    A single threshold rule within an expectation pack.

    Evaluates whether a measured value is within acceptable bounds for
    a given scenario type.
    """
    rule_id: str
    description: str
    metric_key: str            # what to measure (e.g. "stuck_ratio", "combat_events_count")
    operator: str              # "<", "<=", ">", ">=", "==", "!="
    threshold: float
    severity_if_violated: str  # "WARNING" / "ERROR" / "CRITICAL"

    def evaluate(self, value: float) -> bool:
        """Return True if the value satisfies this rule (i.e. NOT violated)."""
        ops = {
            "<": lambda v, t: v < t,
            "<=": lambda v, t: v <= t,
            ">": lambda v, t: v > t,
            ">=": lambda v, t: v >= t,
            "==": lambda v, t: v == t,
            "!=": lambda v, t: v != t,
        }
        fn = ops.get(self.operator)
        if fn is None:
            raise ValueError(f"Unknown operator: {self.operator!r}")
        return fn(value, self.threshold)


@dataclass
class ExpectationResult:
    """Result of evaluating a single ExpectationRule."""
    rule_id: str
    passed: bool
    message: str
    severity: str
    measured_value: Optional[float] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity,
            "measured_value": self.measured_value,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


@dataclass
class ScenarioExpectationPack:
    """
    Defines expected behavior bounds for a specific scenario type.

    Packs are versioned and can evolve independently of analyzer code.
    Domain analyzers and the balance engine consult the active pack to
    determine whether anomalies are concerning, acceptable, or expected.
    """
    scenario_type: str
    version: str
    description: str = ""
    hard_fail_rules: List[ExpectationRule] = field(default_factory=list)
    warning_rules: List[ExpectationRule] = field(default_factory=list)
    # Anomaly rule names that are acceptable/expected for this scenario
    acceptable_anomaly_types: List[str] = field(default_factory=list)
    # Metric keys that should not trigger findings in this scenario
    ignored_metrics: List[str] = field(default_factory=list)
    # Event categories that must be present for this pack to be meaningful
    required_signals: List[str] = field(default_factory=list)

    def all_rules(self) -> List[ExpectationRule]:
        return self.hard_fail_rules + self.warning_rules

    def is_anomaly_acceptable(self, rule_name: str) -> bool:
        return rule_name in self.acceptable_anomaly_types

    def is_metric_ignored(self, metric_key: str) -> bool:
        return metric_key in self.ignored_metrics

    @staticmethod
    def default() -> "ScenarioExpectationPack":
        """Return a minimal default pack with only hard law constraint."""
        return ScenarioExpectationPack(
            scenario_type="mixed_sandbox",
            version="default-1.0",
            description="Default pack — only hard law violations are hard failures.",
            hard_fail_rules=[
                ExpectationRule(
                    rule_id="no_hard_law_violations",
                    description="Hard law violations must be zero",
                    metric_key="hard_law_violations_count",
                    operator="==",
                    threshold=0.0,
                    severity_if_violated="CRITICAL"
                )
            ]
        )
