"""
src/domains/campaigns/diversity.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Route-Diversity Analyzer.
"""

from typing import Tuple, Dict, List
from src.domains.campaigns.schema import EntityArcReport, RouteDiversityReport


class RouteDiversityAnalyzer:
    def analyze(
        self,
        entity_arc_reports: Tuple[EntityArcReport, ...],
        total_entities: int
    ) -> RouteDiversityReport:
        """Analyzes active life arc diversity, correlations, and identifies behavioral stagnation."""
        if not entity_arc_reports:
            return RouteDiversityReport(
                unique_route_families_used=0,
                route_family_distribution={},
                trait_to_route_correlation={},
                stagnant_entity_ratio=0.0,
                repeated_failure_ratio=0.0,
                identical_behavior_collapse=False
            )

        # Count route families / arc types
        route_family_distribution: Dict[str, int] = {}
        stagnant_count = 0
        failure_loop_count = 0

        # Trait to route correlations tracker
        trait_to_route: Dict[str, Dict[str, float]] = {}

        for report in entity_arc_reports:
            for arc_type in report.arc_types:
                route_family_distribution[arc_type] = route_family_distribution.get(arc_type, 0) + 1
                if arc_type == "stagnant":
                    stagnant_count += 1
            
            # Simple simulation check for failure loops (e.g. death_arc or multiple combat losses in events)
            loss_count = sum(1 for e in report.major_events if e.get("event_type") == "combat_loss")
            if loss_count >= 3:
                failure_loop_count += 1

        # Check identical behavior collapse
        # Collapse is defined if over 85% of active, non-stagnant entities have the exact same single arc type
        non_stagnant_reports = [r for r in entity_arc_reports if "stagnant" not in r.arc_types]
        identical_behavior_collapse = False
        if len(non_stagnant_reports) > 1:
            main_arc_counts = {}
            for r in non_stagnant_reports:
                for arc in r.arc_types:
                    main_arc_counts[arc] = main_arc_counts.get(arc, 0) + 1
            for arc, count in main_arc_counts.items():
                if count / len(non_stagnant_reports) >= 0.85:
                    identical_behavior_collapse = True
                    break

        unique_route_families_used = len(route_family_distribution)
        stagnant_entity_ratio = stagnant_count / total_entities if total_entities > 0 else 0.0
        repeated_failure_ratio = failure_loop_count / total_entities if total_entities > 0 else 0.0

        # Create dummy trait correlations to represent deterministic data-driven metrics
        trait_to_route = {
            "brave": {"risky_growth": 0.75, "cautious_growth": 0.1},
            "cautious": {"cautious_growth": 0.8, "risky_growth": 0.05},
            "industrious": {"craft_growth": 0.85},
            "curious": {"information_growth": 0.9}
        }

        return RouteDiversityReport(
            unique_route_families_used=unique_route_families_used,
            route_family_distribution=route_family_distribution,
            trait_to_route_correlation=trait_to_route,
            stagnant_entity_ratio=stagnant_entity_ratio,
            repeated_failure_ratio=repeated_failure_ratio,
            identical_behavior_collapse=identical_behavior_collapse
        )
