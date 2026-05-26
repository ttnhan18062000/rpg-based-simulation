"""
BalanceDiagnosisEngine — evaluates four balance dimensions post-run.

Dimensions:
1. ACTIVITY — expected activity types are present
2. LIVENESS — started processes resolve (quests complete, combats end)
3. DOMINANCE — no extreme one-sided outcome skew
4. RUNTIME_STABILITY — engine performance is stable
"""
from __future__ import annotations
import logging
from typing import List, Optional

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.balance.models import (
    BalanceDimension, BalanceFinding, ScenarioBalanceSummary
)

logger = logging.getLogger(__name__)


class BalanceDiagnosisEngine:
    """
    Evaluates simulation run balance across four dimensions.
    Non-applicable dimensions are gracefully skipped.
    """

    def diagnose(self, ctx: AnalysisContext) -> ScenarioBalanceSummary:
        findings: List[BalanceFinding] = []

        findings.extend(self._evaluate_activity(ctx))
        findings.extend(self._evaluate_liveness(ctx))
        findings.extend(self._evaluate_dominance(ctx))
        findings.extend(self._evaluate_runtime_stability(ctx))

        return ScenarioBalanceSummary(
            run_id=ctx.run_id,
            scenario_type=ctx.scenario_type,
            findings=findings
        )

    # ── ACTIVITY dimension ────────────────────────────────────────────────────

    def _evaluate_activity(self, ctx: AnalysisContext) -> List[BalanceFinding]:
        """
        Detect expected activity types completely absent.
        Driven by expectation pack if available.
        """
        findings = []
        if ctx.expectation_pack is None:
            return findings  # No pack — cannot evaluate expected signals

        pack = ctx.expectation_pack
        for signal in pack.required_signals:
            if not ctx.has_events(signal):
                findings.append(BalanceFinding(
                    dimension=BalanceDimension.ACTIVITY,
                    severity="ERROR",
                    summary=(
                        f"Expected activity type '{signal}' absent from simulation run. "
                        f"Scenario type '{ctx.scenario_type}' requires this signal."
                    ),
                    metric_values={"events_of_type": 0.0},
                    scenario_type=ctx.scenario_type,
                    evidence=[
                        f"Scenario '{ctx.scenario_type}' requires signal: {signal}",
                        f"No events found with category '{signal}'",
                    ],
                    recommendation=(
                        f"Verify that '{signal}' system is active and emitting events for this scenario."
                    ),
                ))
        return findings

    # ── LIVENESS dimension ────────────────────────────────────────────────────

    def _evaluate_liveness(self, ctx: AnalysisContext) -> List[BalanceFinding]:
        """
        Detect started processes (quests, combats) that never resolve.
        """
        findings = []

        # Quest liveness
        quest_events = ctx.events_by_category("quest")
        if quest_events:
            started_ids: set = set()
            completed_ids: set = set()
            for ev in quest_events:
                qid = ev.payload.get("quest_id")
                status = ev.payload.get("status")
                if qid and status == "started":
                    started_ids.add(qid)
                elif qid and status == "completed":
                    completed_ids.add(qid)

            never_resolved = started_ids - completed_ids
            if len(never_resolved) > len(started_ids) * 0.5 and len(started_ids) >= 3:
                findings.append(BalanceFinding(
                    dimension=BalanceDimension.LIVENESS,
                    severity="WARNING",
                    summary=(
                        f"{len(never_resolved)} of {len(started_ids)} quests never resolved "
                        f"({len(never_resolved)/max(len(started_ids),1):.0%} non-resolution rate)."
                    ),
                    metric_values={
                        "quests_started": float(len(started_ids)),
                        "quests_completed": float(len(completed_ids)),
                        "quests_unresolved": float(len(never_resolved)),
                    },
                    scenario_type=ctx.scenario_type,
                    evidence=[
                        f"Quests started: {len(started_ids)}",
                        f"Quests completed: {len(completed_ids)}",
                        f"Quests never resolved: {len(never_resolved)}",
                    ],
                    recommendation="Inspect quest objective reachability and quest timeout logic.",
                ))

        return findings

    # ── DOMINANCE dimension ───────────────────────────────────────────────────

    def _evaluate_dominance(self, ctx: AnalysisContext) -> List[BalanceFinding]:
        """
        Detect extreme one-sided outcomes.
        Currently skipped unless combat events are present with kill data.
        """
        combat_events = ctx.events_by_type("combat_kill")
        if not combat_events:
            return []  # No kill data — skip this dimension

        faction_kills: dict = {}
        for ev in combat_events:
            faction = ev.payload.get("killer_faction") or ev.payload.get("faction")
            if faction:
                faction_kills[faction] = faction_kills.get(faction, 0) + 1

        if len(faction_kills) < 2:
            return []  # Only one faction — cannot compute balance

        total_kills = sum(faction_kills.values())
        if total_kills == 0:
            return []

        max_share = max(faction_kills.values()) / total_kills
        if max_share > 0.85:
            dominant_faction = max(faction_kills, key=faction_kills.get)
            return [BalanceFinding(
                dimension=BalanceDimension.DOMINANCE,
                severity="WARNING",
                summary=(
                    f"Faction '{dominant_faction}' accounts for {max_share:.0%} of all kills. "
                    "Extreme dominance may indicate balance or spawn imbalance."
                ),
                metric_values={
                    "dominant_faction_kill_share": max_share,
                    "total_kills": float(total_kills),
                },
                scenario_type=ctx.scenario_type,
                evidence=[
                    f"Kill distribution: {dict(faction_kills)}",
                    f"Dominant faction: '{dominant_faction}' at {max_share:.0%}",
                ],
                recommendation="Review faction starting conditions, spawn counts, and AI strength balance.",
            )]

        return []

    # ── RUNTIME_STABILITY dimension ───────────────────────────────────────────

    def _evaluate_runtime_stability(self, ctx: AnalysisContext) -> List[BalanceFinding]:
        """
        Detect sustained runtime degradation.
        """
        governor_anomalies = ctx.anomalies_by_rule("GovernorDegradedLive")
        drop_anomalies = ctx.anomalies_by_rule("EventDropRateHigh")

        if not governor_anomalies and not drop_anomalies:
            return []

        findings = []
        total_runtime_issues = len(governor_anomalies) + len(drop_anomalies)

        if total_runtime_issues >= 5:
            severity = "ERROR" if total_runtime_issues >= 10 else "WARNING"
            findings.append(BalanceFinding(
                dimension=BalanceDimension.RUNTIME_STABILITY,
                severity=severity,
                summary=(
                    f"Runtime instability detected: {len(governor_anomalies)} governor degradation events "
                    f"+ {len(drop_anomalies)} event drop incidents."
                ),
                metric_values={
                    "governor_degraded_count": float(len(governor_anomalies)),
                    "event_drop_count": float(len(drop_anomalies)),
                    "total_runtime_issues": float(total_runtime_issues),
                },
                scenario_type=ctx.scenario_type,
                evidence=[
                    f"GovernorDegradedLive anomalies: {len(governor_anomalies)}",
                    f"EventDropRateHigh anomalies: {len(drop_anomalies)}",
                ],
                recommendation=(
                    "Reduce observability overhead or entity count. "
                    "Profile tick loop phases. Check worker queue drain rate."
                ),
            ))

        return findings
