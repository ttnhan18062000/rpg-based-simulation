"""
cohort_analyzer — Phase 26 cohort analyzer.
Enables grouping behavior scorecards to isolate outcome traits.
"""
from __future__ import annotations
from typing import List, Sequence, Dict
from src.observability.behavior.behavior_scorecard import EntityBehaviorScorecard


class CohortAnalyzer:
    """
    Groups individual EntityBehaviorScorecards based on stable traits/verdicts.
    """
    def group_by_verdict(
        self,
        scorecards: Sequence[EntityBehaviorScorecard]
    ) -> Dict[str, List[EntityBehaviorScorecard]]:
        """Groups scorecards by their final verdict mapping."""
        groups: Dict[str, List[EntityBehaviorScorecard]] = {}
        for sc in scorecards:
            verdict = sc.verdict
            if verdict not in groups:
                groups[verdict] = []
            groups[verdict].append(sc)
        return groups
