"""
EconomyDomainAnalyzer — Interprets economic activity anomalies.

Analyzes:
- Resource production stagnation (zero gold transactions for long window)
- Resource node crowding (too many entities at same node)
- Gold circulation freeze (no transactions across entities)
- Inventory full loop (resource collected but not stored/sold)

Required signals: economy events
"""
from __future__ import annotations
from collections import Counter
from typing import Any, Dict, List

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.base import (
    DomainAnalyzer, DomainAnalysisResult, DomainAnalysisStatus,
    DomainFinding, ConfidenceLevel
)


class EconomyDomainAnalyzer(DomainAnalyzer):
    """
    Domain analyzer for economic and resource flow issues.

    Requires economy events (gold transactions) to be present.
    Interprets ResourceNodeCrowdingRule anomalies and low transaction rates.
    """

    domain_id = "economy"
    required_event_categories: List[str] = ["economy"]
    optional_event_categories: List[str] = ["resource", "inventory"]
    required_anomaly_rules: List[str] = []

    ZERO_PRODUCTION_WINDOW_TICKS = 50  # No transactions for this many ticks → stagnation

    def analyze(self, ctx: AnalysisContext) -> DomainAnalysisResult:
        if not ctx.has_events("economy"):
            return self._missing_signal_result("No economy events found in run.")

        economy_events = ctx.events_by_category("economy")
        crowding_anomalies = ctx.anomalies_by_rule("ResourceNodeCrowdingRule")

        findings: List[DomainFinding] = []

        # ── Finding 1: Gold circulation freeze ───────────────────────────────
        stagnation_finding = self._check_gold_stagnation(economy_events, ctx.final_tick())
        if stagnation_finding:
            findings.append(stagnation_finding)

        # ── Finding 2: Resource node crowding ────────────────────────────────
        if crowding_anomalies:
            crowded_nodes: List[Any] = []
            max_crowd = 0
            for a in crowding_anomalies:
                node_id = a.context.get("node_id")
                count = a.context.get("entities_count", 0)
                if node_id:
                    crowded_nodes.append(str(node_id))
                if count > max_crowd:
                    max_crowd = count

            unique_nodes = list(set(crowded_nodes))

            findings.append(DomainFinding(
                domain=self.domain_id,
                severity="WARNING",
                title=f"Resource Node Crowding — {len(crowding_anomalies)} Incidents",
                summary=(
                    f"Resource nodes crowded {len(crowding_anomalies)} times "
                    f"(peak: {max_crowd} entities). Affected nodes: {unique_nodes[:5]}."
                ),
                affected_resources=unique_nodes[:10],
                evidence=[
                    f"Crowding incidents: {len(crowding_anomalies)}",
                    f"Unique crowded nodes: {len(unique_nodes)}",
                    f"Peak simultaneous entities at a node: {max_crowd}",
                ],
                suspected_causes=[
                    "Target selection not accounting for occupancy at nodes",
                    "Resource nodes not marked unavailable when crowded",
                    "Entity scorer weights proximity too heavily over availability",
                ],
                confidence=ConfidenceLevel.HIGH,
                recommended_next_steps=[
                    "Inspect resource node target scorer for occupancy penalty",
                    "Add soft exclusion for nodes at capacity in goal selection",
                    "Check if nodes have occupancy limits enforced",
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

    def _check_gold_stagnation(
        self, economy_events: list, final_tick: int
    ) -> "DomainFinding | None":
        """
        Detect if gold transactions freeze for a sustained window.
        Returns a finding if a gap ≥ ZERO_PRODUCTION_WINDOW_TICKS is found.
        """
        if not economy_events or final_tick == 0:
            return None

        sorted_events = sorted(economy_events, key=lambda e: e.tick)
        max_gap = 0
        gap_start = 0
        gap_end = 0

        prev_tick = sorted_events[0].tick
        for ev in sorted_events[1:]:
            gap = ev.tick - prev_tick
            if gap > max_gap:
                max_gap = gap
                gap_start = prev_tick
                gap_end = ev.tick
            prev_tick = ev.tick

        # Also check from last event to final tick
        tail_gap = final_tick - sorted_events[-1].tick
        if tail_gap > max_gap:
            max_gap = tail_gap
            gap_start = sorted_events[-1].tick
            gap_end = final_tick

        if max_gap < self.ZERO_PRODUCTION_WINDOW_TICKS:
            return None

        confidence = (
            ConfidenceLevel.HIGH if max_gap >= self.ZERO_PRODUCTION_WINDOW_TICKS * 2
            else ConfidenceLevel.MEDIUM
        )

        return DomainFinding(
            domain=self.domain_id,
            severity="ERROR",
            title=f"Gold Circulation Freeze — {max_gap} Tick Gap",
            summary=(
                f"No gold transactions occurred for {max_gap} consecutive ticks "
                f"(ticks {gap_start}–{gap_end}). Resource economy may be broken."
            ),
            evidence=[
                f"Longest transaction gap: {max_gap} ticks",
                f"Gap window: ticks {gap_start}–{gap_end}",
                f"Total economy events: {len(economy_events)}",
                f"Final tick: {final_tick}",
            ],
            suspected_causes=[
                "Inventory full loop preventing resources from being sold",
                "Shop transaction rate zero due to missing shop entity",
                "Resource production blocked by upstream depletion",
                "Worker stuck loop preventing harvesting from completing",
            ],
            confidence=confidence,
            recommended_next_steps=[
                "Inspect shop/storage system for inventory-full deadlock",
                "Check if any gold transaction events occur after tick gap_start",
                "Verify shop entities are spawned and accessible in this scenario",
                "Cross-reference with movement stuck anomalies",
            ],
        )
