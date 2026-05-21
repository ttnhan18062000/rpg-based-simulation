"""
QuestDomainAnalyzer — Interprets quest lifecycle anomalies.

Analyzes:
- Stalled quests (started but no progress for long window)
- Quest completion rate (fraction of started quests that complete)
- Impossible objectives (quests that never progress at all)

Required signals: quest events
"""
from __future__ import annotations
from typing import Any, Dict, List

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.base import (
    DomainAnalyzer, DomainAnalysisResult, DomainAnalysisStatus,
    DomainFinding, ConfidenceLevel
)


class QuestDomainAnalyzer(DomainAnalyzer):
    """
    Domain analyzer for quest and objective lifecycle issues.

    Requires quest events to be present. Interprets QuestStalledRule
    anomalies as a group and identifies impossible objective patterns.
    """

    domain_id = "quest"
    required_event_categories: List[str] = ["quest"]
    optional_event_categories: List[str] = []
    required_anomaly_rules: List[str] = []

    LOW_COMPLETION_RATE_THRESHOLD = 0.2  # < 20% quests completing → problem

    def analyze(self, ctx: AnalysisContext) -> DomainAnalysisResult:
        if not ctx.has_events("quest"):
            return self._missing_signal_result("No quest events found in run.")

        quest_events = ctx.events_by_category("quest")
        stalled_anomalies = ctx.anomalies_by_rule("QuestStalledRule")

        findings: List[DomainFinding] = []

        # ── Finding 1: Stalled quest cluster ─────────────────────────────────
        if stalled_anomalies:
            stalled_quest_ids = list(set(
                a.context.get("quest_id") for a in stalled_anomalies
                if a.context.get("quest_id")
            ))
            stalled_entity_ids = list(set(
                a.entity_id for a in stalled_anomalies if a.entity_id is not None
            ))
            max_stall = max(
                (a.context.get("duration_ticks", 0) for a in stalled_anomalies), default=0
            )

            confidence = (
                ConfidenceLevel.HIGH if len(stalled_quest_ids) >= 3
                else ConfidenceLevel.MEDIUM
            )

            findings.append(DomainFinding(
                domain=self.domain_id,
                severity="WARNING",
                title=f"Quest Stall Cluster — {len(stalled_quest_ids)} Quests",
                summary=(
                    f"{len(stalled_quest_ids)} quests stalled without completion or progress. "
                    f"Longest stall: {max_stall} ticks. "
                    f"Affected entities: {len(stalled_entity_ids)}."
                ),
                affected_entities=stalled_entity_ids[:20],
                affected_quests=stalled_quest_ids[:10],
                evidence=[
                    f"Stalled quests: {len(stalled_quest_ids)}",
                    f"Stalled anomalies: {len(stalled_anomalies)}",
                    f"Longest stall duration: {max_stall} ticks",
                    f"Affected entities: {len(stalled_entity_ids)}",
                ],
                suspected_causes=[
                    "Quest objective target destroyed or missing from world state",
                    "Quest reward gating requires unavailable resource",
                    "Entity assigned to quest has different active goal priority",
                    "Quest system not ticking or receiving state update",
                ],
                confidence=confidence,
                recommended_next_steps=[
                    "Check quest objective validity at quest assignment tick",
                    "Verify quest objective targets still exist in the world state",
                    "Inspect quest priority vs other active goals for assigned entities",
                    "Search `anomalies.json` for QuestStalledRule entries",
                ],
            ))

        # ── Finding 2: Low quest completion rate ─────────────────────────────
        completion_finding = self._check_completion_rate(quest_events)
        if completion_finding:
            findings.append(completion_finding)

        status = (
            DomainAnalysisStatus.FINDINGS_FOUND if findings
            else DomainAnalysisStatus.PASSED
        )
        return DomainAnalysisResult(
            domain_id=self.domain_id,
            status=status,
            findings=findings
        )

    def _check_completion_rate(self, quest_events: list) -> "DomainFinding | None":
        """
        Detect if the ratio of completed quests to started quests is below threshold.
        Only meaningful if ≥ 5 quests were started.
        """
        started: Dict[str, int] = {}  # quest_id → start tick
        completed: Dict[str, int] = {}  # quest_id → completion tick

        for ev in quest_events:
            qid = ev.payload.get("quest_id") or getattr(ev, "quest_id", None)
            status = ev.payload.get("status") or getattr(ev, "status", None)
            if not qid or not status:
                continue
            if status == "started":
                started[qid] = ev.tick
            elif status == "completed":
                completed[qid] = ev.tick

        if len(started) < 5:
            return None  # Not enough data to draw conclusions

        completion_rate = len(completed) / len(started) if started else 0.0
        if completion_rate >= self.LOW_COMPLETION_RATE_THRESHOLD:
            return None

        return DomainFinding(
            domain=self.domain_id,
            severity="WARNING",
            title=f"Low Quest Completion Rate — {completion_rate:.0%}",
            summary=(
                f"Only {len(completed)} of {len(started)} started quests completed "
                f"({completion_rate:.0%} completion rate). "
                "Many quests may have impossible or unreachable objectives."
            ),
            evidence=[
                f"Quests started: {len(started)}",
                f"Quests completed: {len(completed)}",
                f"Completion rate: {completion_rate:.1%}",
            ],
            suspected_causes=[
                "Quests assigned with objectives that cannot be reached in scenario",
                "World state changes invalidate quest objectives mid-run",
                "Quest timeout or cancel logic not firing",
            ],
            confidence=ConfidenceLevel.MEDIUM,
            recommended_next_steps=[
                "Review quest assignment logic for objective reachability validation",
                "Check whether any quests are cancelled vs left stalled",
                "Inspect world generation for objective target availability",
            ],
        )
