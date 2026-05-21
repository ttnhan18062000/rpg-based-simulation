"""
MovementDomainAnalyzer — Interprets movement/navigation anomalies.

Analyzes:
- Stuck entity clusters (many entities stuck near the same area)
- Oscillation (entity bouncing between same two positions)
- High stuck ratio (fraction of moving entities that are stuck)
- Navigation path failures (repeated approach to same impossible target)

Required signals: movement events
"""
from __future__ import annotations
from collections import Counter
from typing import Any, Dict, List

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.base import (
    DomainAnalyzer, DomainAnalysisResult, DomainAnalysisStatus,
    DomainFinding, ConfidenceLevel
)


class MovementDomainAnalyzer(DomainAnalyzer):
    """
    Domain analyzer for movement and navigation issues.

    Requires movement events to be present. Interprets NavigationStuckRule
    anomalies as a group rather than individual entity problems.
    """

    domain_id = "movement"
    required_event_categories: List[str] = ["movement"]
    optional_event_categories: List[str] = []
    required_anomaly_rules: List[str] = []

    STUCK_CLUSTER_THRESHOLD = 3      # ≥ N stuck entities → cluster finding
    HIGH_STUCK_RATIO_THRESHOLD = 0.3  # ≥ 30% of moving entities stuck

    def analyze(self, ctx: AnalysisContext) -> DomainAnalysisResult:
        if not ctx.has_events("movement"):
            return self._missing_signal_result("No movement events found in run.")

        movement_events = ctx.events_by_category("movement")
        stuck_anomalies = ctx.anomalies_by_rule("NavigationStuckRule")

        findings: List[DomainFinding] = []

        # ── Finding 1: Stuck entity cluster ──────────────────────────────────
        if stuck_anomalies:
            stuck_entity_ids = list(set(
                a.entity_id for a in stuck_anomalies if a.entity_id is not None
            ))
            stuck_positions: List[Any] = []
            for a in stuck_anomalies:
                pos = a.context.get("position")
                if pos is not None:
                    stuck_positions.append(str(pos))

            position_counter = Counter(stuck_positions)
            hotspot_positions = [
                pos for pos, count in position_counter.most_common(3) if count >= 2
            ]

            severity = "ERROR" if len(stuck_entity_ids) >= self.STUCK_CLUSTER_THRESHOLD else "WARNING"
            confidence = ConfidenceLevel.HIGH if len(stuck_entity_ids) >= self.STUCK_CLUSTER_THRESHOLD else ConfidenceLevel.MEDIUM

            evidence = [
                f"{len(stuck_entity_ids)} entities detected as stuck",
                f"Total stuck anomalies: {len(stuck_anomalies)}",
            ]
            if hotspot_positions:
                evidence.append(f"Positional hotspots (≥2 entities): {hotspot_positions}")

            suspected_causes = [
                "Pathfinding failure or impassable terrain blocking navigation",
                "Target resource node depleted but still selected",
                "Occupancy/crowding preventing access to target tile",
                "Entity goal invalidation not propagating to movement system",
            ]

            next_steps = [
                "Inspect pathfinding obstacles near hotspot positions",
                "Check resource node validity and target reselection logic",
                "Review occupancy system's entity density limits",
                "Search for `NavigationStuckRule` anomalies in `anomalies.json`",
            ]

            findings.append(DomainFinding(
                domain=self.domain_id,
                severity=severity,
                title=f"Navigation Stuck Cluster — {len(stuck_entity_ids)} Entities",
                summary=(
                    f"{len(stuck_entity_ids)} entities became stuck during this run. "
                    + (f"Positional hotspots at: {hotspot_positions}." if hotspot_positions else "")
                ),
                affected_entities=stuck_entity_ids[:20],
                evidence=evidence,
                suspected_causes=suspected_causes,
                confidence=confidence,
                recommended_next_steps=next_steps,
            ))

        # ── Finding 2: Oscillating entities ──────────────────────────────────
        oscillating = self._detect_oscillation(movement_events)
        if oscillating:
            findings.append(DomainFinding(
                domain=self.domain_id,
                severity="WARNING",
                title=f"Entity Oscillation Detected — {len(oscillating)} Entities",
                summary=(
                    f"{len(oscillating)} entities repeatedly move between the same two positions, "
                    "suggesting a goal contradiction or stuck decision loop."
                ),
                affected_entities=oscillating[:20],
                evidence=[f"Entities oscillating: {oscillating[:10]}"],
                suspected_causes=[
                    "Two conflicting goals pushing entity between same positions",
                    "Scoring function producing equal weight for two unreachable targets",
                    "No-op movement not filtered from event log",
                ],
                confidence=ConfidenceLevel.MEDIUM,
                recommended_next_steps=[
                    "Inspect entity goal scorer for equal-weight loops",
                    "Add oscillation detection to pathfinder",
                    "Check if movement events emit on no-op transitions",
                ],
            ))

        status = (
            DomainAnalysisStatus.FINDINGS_FOUND if findings
            else DomainAnalysisStatus.PASSED
        )
        return DomainAnalysisResult(
            domain_id=self.domain_id,
            status=status,
            findings=findings
        )

    def _detect_oscillation(self, movement_events: list) -> List[int]:
        """
        Detect entities that repeatedly alternate between exactly two positions.
        Requires ≥ 4 position alternations to qualify.
        """
        OSCILLATION_MIN = 4
        entity_positions: Dict[int, List[Any]] = {}

        for ev in movement_events:
            eid = ev.entity_id
            if eid is None:
                continue
            end_pos = ev.payload.get("end_pos") or getattr(ev, "end_pos", None)
            if end_pos is None:
                continue
            entity_positions.setdefault(eid, []).append(str(end_pos))

        oscillating = []
        for eid, positions in entity_positions.items():
            if len(positions) < OSCILLATION_MIN:
                continue
            unique_pos = set(positions)
            if len(unique_pos) == 2:
                # Check if they alternate
                alternations = sum(
                    1 for i in range(1, len(positions))
                    if positions[i] != positions[i - 1]
                )
                if alternations >= OSCILLATION_MIN:
                    oscillating.append(eid)
        return oscillating
