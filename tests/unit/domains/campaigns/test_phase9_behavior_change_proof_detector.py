from src.domains.campaigns.schema import CampaignEvent
from src.domains.campaigns.behavior_change import BehaviorChangeProofDetector


def test_loss_then_avoidance_creates_behavior_change_proof():
    events = [
        CampaignEvent("e1", 1, 1, "combat", "combat_loss", {"target": "wolf"}),
        CampaignEvent("e2", 5, 1, "movement", "avoided_danger", {"reason": "avoid_wolf"}),
    ]
    detector = BehaviorChangeProofDetector()
    proofs = detector.detect(events)
    assert len(proofs) == 1
    assert proofs[0].change_kind == "avoidance"
    assert proofs[0].cause_event_id == "e1"
    assert proofs[0].later_event_id == "e2"


def test_info_learned_then_route_change_creates_proof():
    events = [
        CampaignEvent("e1", 1, 1, "information", "asked_guide", {"topic": "iron_node"}),
        CampaignEvent("e2", 10, 1, "movement", "route_changed", {"reason": "go_to_iron_node"}),
    ]
    detector = BehaviorChangeProofDetector()
    proofs = detector.detect(events)
    assert len(proofs) == 1
    assert proofs[0].change_kind == "route_adaptation"


def test_upgrade_then_harder_quest_creates_proof():
    events = [
        CampaignEvent("e1", 2, 1, "progression", "item_crafted", {"item": "iron_sword"}),
        CampaignEvent("e2", 8, 1, "quest", "quest_completed", {"difficulty": "hard"}),
    ]
    detector = BehaviorChangeProofDetector()
    proofs = detector.detect(events)
    assert len(proofs) == 1
    assert proofs[0].change_kind == "combat_progression"


def test_betrayal_then_partner_rejection_creates_proof():
    events = [
        CampaignEvent("e1", 2, 1, "social", "betrayed_by_partner", {"partner_id": 2}),
        CampaignEvent("e2", 8, 1, "social", "partner_rejected", {"partner_id": 2}),
    ]
    detector = BehaviorChangeProofDetector()
    proofs = detector.detect(events)
    assert len(proofs) == 1
    assert proofs[0].change_kind == "cooperation_rejection"


def test_same_action_without_later_change_does_not_create_proof():
    events = [
        CampaignEvent("e1", 2, 1, "combat", "combat_loss", {"target": "wolf"}),
        CampaignEvent("e2", 8, 1, "combat", "combat_loss", {"target": "wolf"}),
    ]
    detector = BehaviorChangeProofDetector()
    proofs = detector.detect(events)
    # No avoidance or cooperative changes, so no behavior change proof of learning
    assert len(proofs) == 0


def test_proof_requires_temporal_order():
    # If avoidance occurs BEFORE loss, it is not a behavior change proof caused by the loss
    events = [
        CampaignEvent("e2", 1, 1, "movement", "avoided_danger", {"reason": "avoid_wolf"}),
        CampaignEvent("e1", 5, 1, "combat", "combat_loss", {"target": "wolf"}),
    ]
    detector = BehaviorChangeProofDetector()
    proofs = detector.detect(events)
    assert len(proofs) == 0
