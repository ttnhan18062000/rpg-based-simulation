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


def _diversity():
    return RouteDiversityReport(0, {}, {}, 0.0, 0.0, False)


def test_new_fields_default_partial_when_no_death_occurs():
    reports = [EntityArcReport(1, ("craft_growth",), (), (), ())]
    scorecard = CampaignScorecardEvaluator().evaluate(tuple(reports), (), _diversity())
    assert scorecard.reputation_inheritance_check == "partial"
    assert scorecard.nemesis_transfer_check == "partial"


def test_reputation_inheritance_check_fails_when_seed_unset_after_death_with_heir():
    died_event = {
        "tick": 50,
        "event_type": "died",
        "details": {"heir_entity_id": 2},  # inherited_reputation_seed deliberately absent
    }
    reports = [EntityArcReport(1, ("death_arc",), (died_event,), (), ("e1",))]
    scorecard = CampaignScorecardEvaluator().evaluate(tuple(reports), (), _diversity())
    assert scorecard.reputation_inheritance_check == "fail"


def test_reputation_inheritance_check_passes_when_seed_present():
    died_event = {
        "tick": 50,
        "event_type": "died",
        "details": {"heir_entity_id": 2, "inherited_reputation_seed": 0.8},
    }
    reports = [EntityArcReport(1, ("death_arc",), (died_event,), (), ("e1",))]
    scorecard = CampaignScorecardEvaluator().evaluate(tuple(reports), (), _diversity())
    assert scorecard.reputation_inheritance_check == "pass"


def test_nemesis_transfer_check_passes_and_fails_correctly():
    pass_event = {
        "tick": 50,
        "event_type": "died",
        "details": {"heir_entity_id": 2, "had_nemesis": True, "nemesis_transferred": True},
    }
    reports_pass = [EntityArcReport(1, ("death_arc",), (pass_event,), (), ("e1",))]
    scorecard_pass = CampaignScorecardEvaluator().evaluate(tuple(reports_pass), (), _diversity())
    assert scorecard_pass.nemesis_transfer_check == "pass"

    fail_event = {
        "tick": 60,
        "event_type": "died",
        "details": {"heir_entity_id": 3, "had_nemesis": True, "nemesis_transferred": False},
    }
    reports_fail = [EntityArcReport(1, ("death_arc",), (fail_event,), (), ("e2",))]
    scorecard_fail = CampaignScorecardEvaluator().evaluate(tuple(reports_fail), (), _diversity())
    assert scorecard_fail.nemesis_transfer_check == "fail"
