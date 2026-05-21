"""
RootCauseEngine — runs all hypothesis rules and returns ranked results.

For each hypothesis rule:
1. Generate hypotheses from the context
2. Rank by confidence (HIGH > MEDIUM > LOW)
3. Return top N per domain (default: 3)
4. Catch exceptions per rule — a failing rule does not crash the engine
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.rootcause.models import (
    ConfidenceLevel, RootCauseHypothesis
)
from src.observability.understanding.rootcause.rules import (
    ALL_HYPOTHESIS_RULES, HypothesisRule
)

logger = logging.getLogger(__name__)


@dataclass
class RootCauseEngineResult:
    """Aggregated output from the root-cause engine."""
    hypotheses: List[RootCauseHypothesis] = field(default_factory=list)
    failed_rules: List[str] = field(default_factory=list)

    def top_by_confidence(self, n: int = 3) -> List[RootCauseHypothesis]:
        """Return top N hypotheses ranked by confidence."""
        return sorted(
            self.hypotheses,
            key=lambda h: h.confidence.rank,
            reverse=True
        )[:n]

    def to_dict(self) -> dict:
        return {
            "total_hypotheses": len(self.hypotheses),
            "failed_rules": self.failed_rules,
            "hypotheses": [h.to_dict() for h in self.top_by_confidence(10)],
        }


class RootCauseEngine:
    """
    Runs all hypothesis rules against an AnalysisContext and returns
    ranked root-cause hypotheses.

    Design rules:
    - Never raises exceptions (all rule errors are caught and logged)
    - Deduplicates hypotheses with the same title (keeps highest confidence)
    - Top hypotheses are ranked by confidence level, then insertion order
    """

    def __init__(
        self,
        rules: Optional[List[HypothesisRule]] = None,
        top_n: int = 3
    ) -> None:
        self._rules = rules if rules is not None else ALL_HYPOTHESIS_RULES
        self._top_n = top_n

    def run(self, ctx: AnalysisContext) -> RootCauseEngineResult:
        """Run all hypothesis rules against the context and return ranked output."""
        all_hypotheses: List[RootCauseHypothesis] = []
        failed_rules: List[str] = []

        for rule in self._rules:
            try:
                hypotheses = rule.generate(ctx)
                all_hypotheses.extend(hypotheses)
            except Exception as exc:
                logger.error(
                    f"HypothesisRule '{rule.rule_id}' raised an exception: {exc}",
                    exc_info=True
                )
                failed_rules.append(rule.rule_id)

        # Deduplicate by title, keeping the highest-confidence version
        deduped: Dict[str, RootCauseHypothesis] = {}
        for h in all_hypotheses:
            key = h.title
            if key not in deduped or h.confidence.rank > deduped[key].confidence.rank:
                deduped[key] = h

        ranked = sorted(deduped.values(), key=lambda h: h.confidence.rank, reverse=True)

        return RootCauseEngineResult(
            hypotheses=ranked,
            failed_rules=failed_rules
        )
