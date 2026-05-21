"""
Root-cause hypothesis rules.

Each HypothesisRule inspects an AnalysisContext and produces zero or more
RootCauseHypothesis objects if its signature pattern matches.

Rules must be:
- Deterministic (same input → same output)
- Non-destructive (read-only)
- Lean toward under-confidence: only raise confidence when multiple
  independent evidence signals co-occur
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.rootcause.models import (
    ConfidenceLevel, RootCauseHypothesis
)


class HypothesisRule(ABC):
    """Abstract base for root-cause hypothesis rules."""

    rule_id: str = ""

    @abstractmethod
    def generate(self, ctx: AnalysisContext) -> List[RootCauseHypothesis]:
        """Generate hypotheses from the analysis context. Return [] if not applicable."""
        ...


# ── Rule 1: Stale Resource Target Selection ───────────────────────────────────

class StaleResourceTargetSelection(HypothesisRule):
    """
    Hypothesis: Workers target depleted/crowded nodes and fail to re-select.

    Signature:
    - ResourceNodeCrowdingRule anomalies present
    - AND NavigationStuckRule anomalies present near crowded nodes
    """
    rule_id = "StaleResourceTargetSelection"

    def generate(self, ctx: AnalysisContext) -> List[RootCauseHypothesis]:
        crowding = ctx.anomalies_by_rule("ResourceNodeCrowdingRule")
        stuck = ctx.anomalies_by_rule("NavigationStuckRule")
        if not crowding:
            return []

        supporting = [f"ResourceNodeCrowdingRule anomalies: {len(crowding)}"]
        contradicting = []
        confidence = ConfidenceLevel.LOW

        if stuck:
            supporting.append(f"NavigationStuckRule anomalies co-present: {len(stuck)}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            contradicting.append("No NavigationStuckRule anomalies — workers may be selecting new targets")

        if len(crowding) >= 5:
            confidence = ConfidenceLevel.HIGH
            supporting.append("High crowding anomaly count (≥5) indicates systemic target selection failure")

        return [RootCauseHypothesis(
            title="Stale Resource Target Selection",
            domain="economy",
            confidence=confidence,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            related_anomalies=["ResourceNodeCrowdingRule", "NavigationStuckRule"],
            suggested_files_or_systems=[
                "src/simulation/goals/", "src/simulation/resources/target_selector.py"
            ],
            recommended_checks=[
                "Check if resource nodes mark themselves unavailable when at capacity",
                "Verify target selector re-evaluates node availability each tick",
                "Inspect occupancy limit enforcement in resource system",
            ],
        )]


# ── Rule 2: Movement Bottleneck or Occupancy Crowding ───────────────────────

class MovementBottleneckOrOccupancyCrowding(HypothesisRule):
    """
    Hypothesis: Navigation paths blocked by terrain or occupancy.

    Signature:
    - NavigationStuckRule anomalies: 3+ entities
    - No ResourceNodeCrowdingRule (distinguish from stale target selection)
    """
    rule_id = "MovementBottleneckOrOccupancyCrowding"

    def generate(self, ctx: AnalysisContext) -> List[RootCauseHypothesis]:
        stuck = ctx.anomalies_by_rule("NavigationStuckRule")
        crowding = ctx.anomalies_by_rule("ResourceNodeCrowdingRule")
        if len(stuck) < 3:
            return []

        stuck_entity_ids = list(set(a.entity_id for a in stuck if a.entity_id))
        stuck_positions = list(set(
            str(a.context.get("position", "")) for a in stuck if a.context.get("position")
        ))

        supporting = [
            f"NavigationStuckRule anomalies: {len(stuck)}",
            f"Unique stuck entities: {len(stuck_entity_ids)}",
        ]
        contradicting = []
        confidence = ConfidenceLevel.MEDIUM

        if len(stuck_positions) <= 2:
            supporting.append(f"Stuck positions concentrated at ≤2 locations: {stuck_positions}")
            confidence = ConfidenceLevel.HIGH

        if crowding:
            contradicting.append("ResourceNodeCrowdingRule present — may be target selection, not terrain")

        return [RootCauseHypothesis(
            title="Movement Bottleneck or Occupancy Crowding",
            domain="movement",
            confidence=confidence,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            related_anomalies=["NavigationStuckRule"],
            suggested_files_or_systems=[
                "src/simulation/movement/pathfinder.py",
                "src/simulation/world/occupancy_grid.py",
            ],
            recommended_checks=[
                "Inspect world map for choke points near stuck positions",
                "Check occupancy grid density limits at stuck coordinates",
                "Verify pathfinder handles occupied tiles correctly",
            ],
        )]


# ── Rule 3: Inventory Full Return Loop Broken ─────────────────────────────────

class InventoryFullReturnLoopBroken(HypothesisRule):
    """
    Hypothesis: Workers harvesting resources but cannot deposit (inventory full
    or storage missing), causing economy to freeze.

    Signature:
    - Economy stagnation (long gap in economy events)
    - AND economy events exist (so workers started producing)
    """
    rule_id = "InventoryFullReturnLoopBroken"

    STAGNATION_TICK_THRESHOLD = 50

    def generate(self, ctx: AnalysisContext) -> List[RootCauseHypothesis]:
        economy_events = ctx.events_by_category("economy")
        if not economy_events:
            return []

        final_tick = ctx.final_tick()
        if final_tick == 0:
            return []

        sorted_events = sorted(economy_events, key=lambda e: e.tick)
        max_gap = 0
        prev_tick = sorted_events[0].tick
        for ev in sorted_events[1:]:
            max_gap = max(max_gap, ev.tick - prev_tick)
            prev_tick = ev.tick
        tail_gap = final_tick - sorted_events[-1].tick
        max_gap = max(max_gap, tail_gap)

        if max_gap < self.STAGNATION_TICK_THRESHOLD:
            return []

        confidence = (
            ConfidenceLevel.HIGH if max_gap >= self.STAGNATION_TICK_THRESHOLD * 2
            else ConfidenceLevel.MEDIUM
        )

        return [RootCauseHypothesis(
            title="Inventory Full Return Loop Broken",
            domain="economy",
            confidence=confidence,
            supporting_evidence=[
                f"Economy events exist (production started: {len(economy_events)} events)",
                f"Longest transaction gap: {max_gap} ticks",
                "Economy active then froze → return/deposit loop likely broken",
            ],
            contradicting_evidence=[],
            related_anomalies=["ResourceNodeCrowdingRule"],
            suggested_files_or_systems=[
                "src/simulation/economy/inventory.py",
                "src/simulation/economy/shop.py",
                "src/simulation/goals/return_to_storage_goal.py",
            ],
            recommended_checks=[
                "Check if shop/storage entities exist and are accessible",
                "Inspect inventory-full handling in harvest goal",
                "Verify return-to-storage goal fires when inventory is full",
                "Check that workers can pathfind to storage/shop from stuck position",
            ],
        )]


# ── Rule 4: Quest Objective Impossible ───────────────────────────────────────

class QuestObjectiveImpossible(HypothesisRule):
    """
    Hypothesis: Quests assigned with targets that do not exist or cannot be reached.

    Signature:
    - QuestStalledRule anomalies present
    - Multiple quests stalled (≥3)
    """
    rule_id = "QuestObjectiveImpossible"

    def generate(self, ctx: AnalysisContext) -> List[RootCauseHypothesis]:
        stalled = ctx.anomalies_by_rule("QuestStalledRule")
        if len(stalled) < 3:
            return []

        stalled_quest_ids = list(set(
            a.context.get("quest_id") for a in stalled if a.context.get("quest_id")
        ))
        confidence = ConfidenceLevel.HIGH if len(stalled_quest_ids) >= 5 else ConfidenceLevel.MEDIUM

        return [RootCauseHypothesis(
            title="Quest Objective Impossible or Unreachable",
            domain="quest",
            confidence=confidence,
            supporting_evidence=[
                f"QuestStalledRule anomalies: {len(stalled)}",
                f"Unique stalled quest IDs: {len(stalled_quest_ids)}",
                "Multiple quests failing suggests systematic, not per-quest problem",
            ],
            contradicting_evidence=[],
            related_anomalies=["QuestStalledRule"],
            suggested_files_or_systems=[
                "src/simulation/quests/quest_assigner.py",
                "src/simulation/quests/objective_validator.py",
                "src/simulation/world/entity_spawner.py",
            ],
            recommended_checks=[
                "Verify quest objective targets are spawned before quest assignment",
                "Check objective reachability validation in quest assigner",
                "Inspect whether quest targets are destroyed after assignment",
                "Review world generation for missing entities required by quests",
            ],
        )]


# ── Rule 5: Governor Pressure from Observability or Work Debt ────────────────

class GovernorPressureFromObservabilityOrWorkDebt(HypothesisRule):
    """
    Hypothesis: The governor entered degraded mode due to observability overhead
    or accumulated worker queue debt.

    Signature:
    - GovernorDegradedLive anomalies ≥ 3
    """
    rule_id = "GovernorPressureFromObservabilityOrWorkDebt"

    def generate(self, ctx: AnalysisContext) -> List[RootCauseHypothesis]:
        governor_anomalies = ctx.anomalies_by_rule("GovernorDegradedLive")
        if len(governor_anomalies) < 3:
            return []

        drop_anomalies = ctx.anomalies_by_rule("EventDropRateHigh")
        supporting = [f"GovernorDegradedLive anomalies: {len(governor_anomalies)}"]
        contradicting = []
        confidence = ConfidenceLevel.MEDIUM

        if drop_anomalies:
            supporting.append(f"EventDropRateHigh also present ({len(drop_anomalies)} anomalies) — stream backpressure likely")
            confidence = ConfidenceLevel.HIGH

        if len(governor_anomalies) >= 8:
            supporting.append("High frequency of degradation events (≥8) indicates sustained system pressure")
            confidence = ConfidenceLevel.HIGH

        return [RootCauseHypothesis(
            title="Governor Pressure from Observability Overhead or Work Debt",
            domain="runtime",
            confidence=confidence,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            related_anomalies=["GovernorDegradedLive", "EventDropRateHigh"],
            suggested_files_or_systems=[
                "src/observability/config.py",
                "src/observability/anomaly/worker.py",
                "src/core/governor.py",
            ],
            recommended_checks=[
                "Try LIGHT or OFF observability mode and compare tick duration",
                "Check worker queue depth during degraded ticks",
                "Review entity count vs hardware profile tick budget",
                "Inspect governor degradation thresholds and hysteresis",
            ],
        )]


# ── Rule 6: Combat Engagement Cannot Resolve ─────────────────────────────────

class CombatEngagementCannotResolve(HypothesisRule):
    """
    Hypothesis: Combatants are locked in infinite combat because death/flee
    conditions are not triggering.

    Signature:
    - CombatNeverEndsRule anomalies present
    """
    rule_id = "CombatEngagementCannotResolve"

    def generate(self, ctx: AnalysisContext) -> List[RootCauseHypothesis]:
        combat_anomalies = ctx.anomalies_by_rule("CombatNeverEndsRule")
        if not combat_anomalies:
            return []

        affected_entity_ids = list(set(
            a.entity_id for a in combat_anomalies if a.entity_id
        ))
        confidence = ConfidenceLevel.HIGH if len(combat_anomalies) >= 3 else ConfidenceLevel.MEDIUM

        return [RootCauseHypothesis(
            title="Combat Engagement Cannot Resolve",
            domain="combat",
            confidence=confidence,
            supporting_evidence=[
                f"CombatNeverEndsRule anomalies: {len(combat_anomalies)}",
                f"Affected entities: {len(affected_entity_ids)}",
            ],
            contradicting_evidence=[],
            related_anomalies=["CombatNeverEndsRule"],
            suggested_files_or_systems=[
                "src/simulation/combat/combat_resolver.py",
                "src/simulation/combat/health_system.py",
                "src/simulation/entities/death_handler.py",
            ],
            recommended_checks=[
                "Verify death/flee condition triggers in combat resolver",
                "Check that HP cannot go below 0 without death event",
                "Inspect damage calculation for zero-damage edge cases",
                "Verify combat_kill event fires and removes entity from combat",
            ],
        )]


# ── Registry of all rules (stable order) ─────────────────────────────────────

ALL_HYPOTHESIS_RULES: List[HypothesisRule] = [
    StaleResourceTargetSelection(),
    MovementBottleneckOrOccupancyCrowding(),
    InventoryFullReturnLoopBroken(),
    QuestObjectiveImpossible(),
    GovernorPressureFromObservabilityOrWorkDebt(),
    CombatEngagementCannotResolve(),
]
