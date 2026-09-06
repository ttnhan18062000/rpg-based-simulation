"""
src/domains/campaigns/scorecard.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Semantic Campaign Scorecard.
"""

from typing import Tuple
from src.domains.campaigns.schema import (
    CampaignScorecard,
    EntityArcReport,
    ForbiddenBehaviorReport,
    RouteDiversityReport
)


class CampaignScorecardEvaluator:
    def evaluate(
        self,
        entity_arc_reports: Tuple[EntityArcReport, ...],
        forbidden_behaviors: Tuple[ForbiddenBehaviorReport, ...],
        route_diversity: RouteDiversityReport
    ) -> CampaignScorecard:
        """Evaluates life quality, behavioral variety, and forbidden acts to produce a CampaignScorecard."""
        # Counts of behavior change proofs
        total_proofs = sum(len(r.behavior_change_proofs) for r in entity_arc_reports)
        forbidden_count = len(forbidden_behaviors)

        # Basic scorecard rules
        self_model_usage = "pass" if any(len(r.behavior_change_proofs) > 0 for r in entity_arc_reports) else "fail"
        route_decision_quality = "pass" if route_diversity.unique_route_families_used >= 3 else "partial"
        combat_learning = "pass" if any(p.change_kind == "avoidance" or p.change_kind == "social_cooperation" for r in entity_arc_reports for p in r.behavior_change_proofs) else "partial"
        information_learning = "pass" if any(p.change_kind == "route_adaptation" for r in entity_arc_reports for p in r.behavior_change_proofs) else "partial"
        reward_conversion = "pass" if any("craft_growth" in r.arc_types or "risky_growth" in r.arc_types for r in entity_arc_reports) else "fail"
        cooperation_usage = "pass" if any("party_growth" in r.arc_types for r in entity_arc_reports) else "partial"
        
        # Checking world feedback usage (e.g. scarcity_avoidance)
        world_feedback_usage = "pass" if any(p.change_kind == "scarcity_avoidance" for r in entity_arc_reports for p in r.behavior_change_proofs) else "partial"

        # Idea 53/55 Campaign-mode test coverage (TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS):
        # "died" is already in LifeArcClassifier's major_events whitelist. A death's own details
        # dict carries heir_entity_id/inherited_reputation_seed/had_nemesis/nemesis_transferred
        # when the caller populates them from the real on-death dispatch outcome -- this scorer
        # does not itself know about LifecycleSystem, it only reads what the caller reports.
        reputation_inheritance_check = "partial"
        nemesis_transfer_check = "partial"
        for r in entity_arc_reports:
            for e in r.major_events:
                if e.get("event_type") != "died":
                    continue
                details = e.get("details", {})
                if details.get("heir_entity_id") is not None:
                    if details.get("inherited_reputation_seed") is None:
                        reputation_inheritance_check = "fail"
                    elif reputation_inheritance_check != "fail":
                        reputation_inheritance_check = "pass"
                    if details.get("had_nemesis"):
                        if not details.get("nemesis_transferred"):
                            nemesis_transfer_check = "fail"
                        elif nemesis_transfer_check != "fail":
                            nemesis_transfer_check = "pass"

        # Calculate a route diversity score from 0.0 to 1.0
        route_diversity_score = min(1.0, route_diversity.unique_route_families_used / 6.0)

        # Verdict logic
        # Verdict is fail if forbidden behavior occurs, or if too few behavior change proofs, or if identical behavior collapse
        verdict = "pass"
        if forbidden_count > 0:
            verdict = "fail"
        elif total_proofs < 1:
            verdict = "fail"
        elif route_diversity.identical_behavior_collapse:
            verdict = "fail"
        elif route_diversity.stagnant_entity_ratio > 0.5:
            verdict = "fail"

        return CampaignScorecard(
            self_model_usage=self_model_usage,
            route_decision_quality=route_decision_quality,
            combat_learning=combat_learning,
            information_learning=information_learning,
            reward_conversion=reward_conversion,
            cooperation_usage=cooperation_usage,
            world_feedback_usage=world_feedback_usage,
            reputation_inheritance_check=reputation_inheritance_check,
            nemesis_transfer_check=nemesis_transfer_check,
            behavior_change_proofs=total_proofs,
            route_diversity_score=route_diversity_score,
            stagnant_entity_ratio=route_diversity.stagnant_entity_ratio,
            forbidden_behavior_count=forbidden_count,
            verdict=verdict
        )
