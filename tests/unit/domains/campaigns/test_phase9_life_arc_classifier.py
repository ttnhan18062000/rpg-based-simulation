from src.domains.campaigns.schema import CampaignEvent, BehaviorChangeProof
from src.domains.campaigns.classifier import LifeArcClassifier


def test_craft_growth_arc_detected_from_trace():
    events = [
        CampaignEvent("1", 1, 1, "progression", "recipe_learned", {"recipe": "iron_sword"}),
        CampaignEvent("2", 5, 1, "progression", "item_crafted", {"item": "iron_sword"}),
    ]
    classifier = LifeArcClassifier()
    report = classifier.classify(1, events, ())
    assert "craft_growth" in report.arc_types
    assert report.entity_id == 1
    assert "1" in report.evidence_event_ids


def test_information_growth_arc_detected_from_trace():
    events = [
        CampaignEvent("1", 1, 1, "information", "rumor_heard", {"topic": "iron_depletion"}),
        CampaignEvent("2", 5, 1, "movement", "route_changed", {"reason": "iron_depletion"}),
    ]
    classifier = LifeArcClassifier()
    report = classifier.classify(1, events, ())
    assert "information_growth" in report.arc_types


def test_failed_adventurer_arc_detected_from_death_with_prior_decisions():
    events = [
        CampaignEvent("1", 1, 1, "combat", "combat_loss", {}),
        CampaignEvent("2", 5, 1, "lifecycle", "died", {}),
    ]
    classifier = LifeArcClassifier()
    report = classifier.classify(1, events, ())
    assert "failed_adventurer" in report.arc_types
    assert "death_arc" in report.arc_types


def test_stagnant_arc_detected_when_no_meaningful_change():
    events = [
        CampaignEvent("1", 1, 1, "movement", "scout_location", {}),
    ]
    classifier = LifeArcClassifier()
    report = classifier.classify(1, events, ())
    assert "stagnant" in report.arc_types
