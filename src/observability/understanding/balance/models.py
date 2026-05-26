"""Balance Diagnosis models."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class BalanceDimension(str, Enum):
    ACTIVITY = "ACTIVITY"
    LIVENESS = "LIVENESS"
    DOMINANCE = "DOMINANCE"
    RUNTIME_STABILITY = "RUNTIME_STABILITY"


@dataclass
class BalanceFinding:
    finding_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    dimension: BalanceDimension = BalanceDimension.ACTIVITY
    severity: str = "WARNING"
    summary: str = ""
    metric_values: Dict[str, float] = field(default_factory=dict)
    expected_range: Optional[Tuple[float, float]] = None
    scenario_type: str = ""
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "dimension": self.dimension.value,
            "severity": self.severity,
            "summary": self.summary,
            "metric_values": self.metric_values,
            "expected_range": list(self.expected_range) if self.expected_range else None,
            "scenario_type": self.scenario_type,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


@dataclass
class ScenarioBalanceSummary:
    run_id: str
    scenario_type: str
    findings: List[BalanceFinding] = field(default_factory=list)

    def findings_by_dimension(self, dimension: BalanceDimension) -> List[BalanceFinding]:
        return [f for f in self.findings if f.dimension == dimension]

    def is_balanced(self) -> bool:
        return not any(f.severity in ("ERROR", "CRITICAL") for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_type": self.scenario_type,
            "is_balanced": self.is_balanced(),
            "total_findings": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
        }
