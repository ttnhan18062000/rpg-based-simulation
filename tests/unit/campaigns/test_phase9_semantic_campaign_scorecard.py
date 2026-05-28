from src.domains.campaigns.schema import EntityArcReport, RouteDiversityReport, BehaviorChangeProof
from src.domains.campaigns.scorecard import CampaignScorecardEvaluator


def test_scorecard_passes_when_required_semantic_proofs_exist():
    proof = BehaviorChangeProof(1, "e1", "e2", "avoidance", "learned", 0.9)
    reports = [
        EntityArcReport(1, ("cautious_growth", "craft_growth"), (), (proof,), ()),
    ]
    diversity = RouteDiversityReport(
        unique_route_families_used=3,
        route_family_distribution={"cautious_growth": 1},
        trait_to_route_correlation={},
        stagnant_entity_ratio=0.0,
        repeated_failure_ratio=0.0,
        identical_behavior_collapse=False
    )
    evaluator = CampaignScorecardEvaluator()
    scorecard = evaluator.evaluate(tuple(reports), (), diversity)
    assert scorecard.verdict == "pass"
    assert scorecard.self_model_usage == "pass"


def test_scorecard_fails_when_forbidden_behavior_detected():
    from src.domains.campaigns.schema import ForbiddenBehaviorReport
    reports = [
        EntityArcReport(1, ("cautious_growth",), (), (), ()),
    ]
    diversity = RouteDiversityReport(3, {}, {}, 0.0, 0.0, False)
    fb = ForbiddenBehaviorReport("action_after_death", 1, 10, (), "Action post death")
    evaluator = CampaignScorecardEvaluator()
    scorecard = evaluator.evaluate(tuple(reports), (fb,), diversity)
    assert scorecard.verdict == "fail"
    assert scorecard.forbidden_behavior_count == 1
