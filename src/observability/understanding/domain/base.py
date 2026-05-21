"""
Domain Analyzer base classes and registry.

Each domain analyzer:
- Declares required signals (event categories / anomaly rule names)
- Declares optional signals
- Returns a DomainAnalysisResult with DomainFinding items
- Returns SKIPPED_MISSING_SIGNAL if required signals are absent (no crash)
- Produces deterministic output for the same input
"""
from __future__ import annotations
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.observability.understanding.context import AnalysisContext

logger = logging.getLogger(__name__)


# ── Finding confidence ────────────────────────────────────────────────────────

class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ── Domain finding model ──────────────────────────────────────────────────────

@dataclass
class DomainFinding:
    """
    A structured interpretation finding from a domain analyzer.

    Unlike raw Anomaly objects (which are detection artifacts), a DomainFinding
    represents an interpreted conclusion with evidence, suspected causes, and
    investigation guidance.
    """
    finding_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    domain: str = ""
    severity: str = "WARNING"          # WARNING / ERROR / CRITICAL
    title: str = ""
    summary: str = ""
    affected_entities: List[int] = field(default_factory=list)
    affected_regions: List[str] = field(default_factory=list)
    affected_resources: List[str] = field(default_factory=list)
    affected_quests: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    suspected_causes: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    recommended_next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "domain": self.domain,
            "severity": self.severity,
            "title": self.title,
            "summary": self.summary,
            "affected_entities": self.affected_entities,
            "affected_regions": self.affected_regions,
            "affected_resources": self.affected_resources,
            "affected_quests": self.affected_quests,
            "evidence": self.evidence,
            "suspected_causes": self.suspected_causes,
            "confidence": self.confidence.value,
            "recommended_next_steps": self.recommended_next_steps,
        }


# ── Analysis result ───────────────────────────────────────────────────────────

class DomainAnalysisStatus(str, Enum):
    PASSED = "PASSED"                           # Analyzed, no findings
    FINDINGS_FOUND = "FINDINGS_FOUND"           # Analyzed, findings generated
    SKIPPED_MISSING_SIGNAL = "SKIPPED_MISSING_SIGNAL"  # Required signals absent
    FAILED = "FAILED"                           # Analyzer raised an exception


@dataclass
class DomainAnalysisResult:
    """Result from a single domain analyzer execution."""
    domain_id: str
    status: DomainAnalysisStatus
    findings: List[DomainFinding] = field(default_factory=list)
    skipped_reason: Optional[str] = None
    error_message: Optional[str] = None
    analyzer_runtime_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "status": self.status.value,
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "skipped_reason": self.skipped_reason,
            "error_message": self.error_message,
            "analyzer_runtime_ms": round(self.analyzer_runtime_ms, 3),
        }


# ── Domain analyzer abstract base ─────────────────────────────────────────────

class DomainAnalyzer(ABC):
    """
    Abstract base for all domain analyzers.

    Subclasses must declare:
    - domain_id: stable string identifier
    - required_event_categories: event categories that must be present
    - optional_event_categories: event categories that enrich analysis if present

    Subclasses implement analyze() which receives a fully populated
    AnalysisContext and returns a DomainAnalysisResult.
    """

    domain_id: str = ""
    required_event_categories: List[str] = []
    optional_event_categories: List[str] = []
    required_anomaly_rules: List[str] = []

    def _has_required_signals(self, ctx: AnalysisContext) -> bool:
        """Check whether required event categories are present in context."""
        for cat in self.required_event_categories:
            if not ctx.has_events(cat):
                return False
        for rule in self.required_anomaly_rules:
            if not ctx.anomalies_by_rule(rule):
                return False
        return True

    def _missing_signal_result(self, reason: str) -> DomainAnalysisResult:
        return DomainAnalysisResult(
            domain_id=self.domain_id,
            status=DomainAnalysisStatus.SKIPPED_MISSING_SIGNAL,
            skipped_reason=reason
        )

    @abstractmethod
    def analyze(self, ctx: AnalysisContext) -> DomainAnalysisResult:
        """Run domain analysis against the given context."""
        ...


# ── Registry ──────────────────────────────────────────────────────────────────

class DomainAnalyzerRegistry:
    """
    Registry that runs multiple domain analyzers in stable order and collects
    results. A failed analyzer is reported without corrupting the others.
    """

    def __init__(self) -> None:
        self._analyzers: List[DomainAnalyzer] = []

    def register(self, analyzer: DomainAnalyzer) -> None:
        """Register a domain analyzer. Order of registration = execution order."""
        self._analyzers.append(analyzer)

    def run_all(self, ctx: AnalysisContext) -> List[DomainAnalysisResult]:
        """
        Run all registered analyzers against the given context.
        Failed analyzers are caught and recorded, not propagated.
        """
        results: List[DomainAnalysisResult] = []
        for analyzer in self._analyzers:
            t0 = time.perf_counter_ns()
            try:
                result = analyzer.analyze(ctx)
                result.analyzer_runtime_ms = (time.perf_counter_ns() - t0) / 1e6
            except Exception as exc:
                runtime_ms = (time.perf_counter_ns() - t0) / 1e6
                logger.error(
                    f"DomainAnalyzer '{analyzer.domain_id}' raised an exception: {exc}",
                    exc_info=True
                )
                result = DomainAnalysisResult(
                    domain_id=analyzer.domain_id,
                    status=DomainAnalysisStatus.FAILED,
                    error_message=str(exc),
                    analyzer_runtime_ms=runtime_ms
                )
            results.append(result)
        return results

    @classmethod
    def default(cls) -> "DomainAnalyzerRegistry":
        """Build a registry with all four standard Phase 8 domain analyzers."""
        from src.observability.understanding.domain.movement import MovementDomainAnalyzer
        from src.observability.understanding.domain.economy import EconomyDomainAnalyzer
        from src.observability.understanding.domain.quest import QuestDomainAnalyzer
        from src.observability.understanding.domain.runtime import RuntimeDomainAnalyzer
        reg = cls()
        reg.register(MovementDomainAnalyzer())
        reg.register(EconomyDomainAnalyzer())
        reg.register(QuestDomainAnalyzer())
        reg.register(RuntimeDomainAnalyzer())
        return reg
