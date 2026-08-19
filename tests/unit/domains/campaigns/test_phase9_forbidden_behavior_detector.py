from src.domains.campaigns.schema import CampaignEvent
from src.domains.campaigns.forbidden import ForbiddenBehaviorDetector


def test_action_after_death_is_detected():
    events = [
        CampaignEvent("e1", 10, 1, "lifecycle", "died", {}),
        CampaignEvent("e2", 11, 1, "movement", "scout_location", {}),
    ]
    detector = ForbiddenBehaviorDetector()
    violations = detector.detect(events)
    assert len(violations) == 1
    assert violations[0].rule_violated == "action_after_death"
    assert violations[0].entity_id == 1


def test_repeated_failed_action_loop_is_detected():
    events = [
        CampaignEvent("e1", 1, 1, "action", "failed_action", {"action_name": "attack"}),
        CampaignEvent("e2", 2, 1, "action", "failed_action", {"action_name": "attack"}),
        CampaignEvent("e3", 3, 1, "action", "failed_action", {"action_name": "attack"}),
        CampaignEvent("e4", 4, 1, "action", "failed_action", {"action_name": "attack"}),
    ]
    detector = ForbiddenBehaviorDetector()
    violations = detector.detect(events)
    assert len(violations) == 1
    assert violations[0].rule_violated == "repeated_same_failed_action_forever"


def test_hidden_knowledge_usage_is_detected():
    events = [
        CampaignEvent("e1", 1, 1, "action", "use_hidden_knowledge", {}),
    ]
    detector = ForbiddenBehaviorDetector()
    violations = detector.detect(events)
    assert len(violations) == 1
    assert violations[0].rule_violated == "omniscient_hidden_knowledge"
