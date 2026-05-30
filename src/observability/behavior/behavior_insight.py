"""
behavior_insight — Phase 25 semantic behavior insight model and generator.
Translates structured findings into evidence-backed strategic recommendations.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Sequence
from src.observability.behavior.behavior_finding import BehaviorFinding


@dataclass(frozen=True)
class BehaviorInsight:
    """
    An immutable record representing a high-level compiled behavioral summary.
    """
    insight_id: str
    summary: str
    evidence: str
    affected_entities: tuple[int, ...]
    findings: tuple[str, ...]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "insight_id": self.insight_id,
            "summary": self.summary,
            "evidence": self.evidence,
            "affected_entities": list(self.affected_entities),
            "findings": list(self.findings),
            "recommendation": self.recommendation,
        }


class BehaviorInsightGenerator:
    """
    Rule-based generator compiling multi-entity findings into structured reports.
    """
    def generate(
        self,
        findings: Sequence[BehaviorFinding]
    ) -> List[BehaviorInsight]:
        insights = []
        loop_findings = [f for f in findings if f.finding_type == "repeated_failure_loop"]
        omniscience_findings = [f for f in findings if f.finding_type == "hidden_knowledge_suspicion"]

        if loop_findings:
            entities = set()
            finding_ids = []
            for f in loop_findings:
                entities.update(f.affected_entities)
                finding_ids.append(f.finding_id)
            
            insights.append(BehaviorInsight(
                insight_id="INS-LOOP-DETECTION",
                summary="Entities are stuck in stagnant failure loops",
                evidence=f"{len(loop_findings)} separate failure loops detected across entities: {sorted(list(entities))}",
                affected_entities=tuple(sorted(list(entities))),
                findings=tuple(finding_ids),
                recommendation="Improve fail-state adaptation and check route cooldown intervals."
            ))

        if omniscience_findings:
            entities = set()
            finding_ids = []
            for f in omniscience_findings:
                entities.update(f.affected_entities)
                finding_ids.append(f.finding_id)
            
            insights.append(BehaviorInsight(
                insight_id="INS-OMNISCIENCE-DETECTION",
                summary="Entities are leveraging hidden world knowledge",
                evidence=f"Suspicious avoidance without matching information seeking inquiries on entities: {sorted(list(entities))}",
                affected_entities=tuple(sorted(list(entities))),
                findings=tuple(finding_ids),
                recommendation="Audit spatial perception filters to ensure no world components are leaked."
            ))

        return insights
