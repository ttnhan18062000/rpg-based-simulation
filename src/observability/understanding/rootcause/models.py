"""
Root-Cause Hypothesis models.

A hypothesis is not a proof — it is a ranked suggestion based on
evidence patterns from events and anomalies. The system should say
"The evidence suggests likely causes: X, Y, Z" not "This is definitely X."
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @property
    def rank(self) -> int:
        return {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[self.value]


@dataclass
class RootCauseHypothesis:
    """
    A single ranked hypothesis for why an anomaly or pattern occurred.

    Confidence is based on how many evidence signals match the hypothesis
    pattern. Contradicting evidence lowers confidence but does not suppress
    the hypothesis entirely.
    """
    hypothesis_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    domain: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    related_anomalies: List[str] = field(default_factory=list)
    suggested_files_or_systems: List[str] = field(default_factory=list)
    recommended_checks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "domain": self.domain,
            "confidence": self.confidence.value,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "related_anomalies": self.related_anomalies,
            "suggested_files_or_systems": self.suggested_files_or_systems,
            "recommended_checks": self.recommended_checks,
        }
