import pytest
from src.engine.intent.action_intent import IntentTrace
from src.testing.route_family_classifier import RouteFamilyClassifier


def test_classify_route_families():
    """Verify RouteFamilyClassifier classifies list of traces correctly."""
    traces = [
        IntentTrace("ASK_INFORMATION", 1, "selected", "opp1", (), "SUCCESS"),
        IntentTrace("REST_AT_INN", 1, "selected", "opp2", (), "SUCCESS"),
        IntentTrace("BUY_ITEM", 1, "selected", "opp3", (), "SUCCESS"),
    ]
    
    families = RouteFamilyClassifier.classify(traces)
    assert "ask_information" in families
    assert "recover" in families
    assert "buy_upgrade" in families


def test_classify_defer_with_reason():
    """Verify RouteFamilyClassifier classifies failed requirements as defer_with_reason."""
    traces = [
        IntentTrace("REQUEST_CRAFT", 1, "selected", "opp1", (), "FAILED_REQUIREMENTS: missing items"),
    ]
    families = RouteFamilyClassifier.classify(traces)
    assert "defer_with_reason" in families


def test_detect_infinite_same_failed_action():
    """Verify infinite same failed action is detected on 3+ consecutive failures of same kind."""
    # 1. Normal trace (under 3 failures)
    traces_ok = [
        IntentTrace("BUY_ITEM", 1, "selected", "opp1", (), "FAILED_REQUIREMENTS"),
        IntentTrace("BUY_ITEM", 1, "selected", "opp1", (), "FAILED_REQUIREMENTS"),
        IntentTrace("REST_AT_INN", 1, "selected", "opp2", (), "SUCCESS"),
    ]
    assert len(RouteFamilyClassifier.detect_forbidden(traces_ok)) == 0

    # 2. Triggering trace (3 consecutive failures of same kind)
    traces_bad = [
        IntentTrace("BUY_ITEM", 1, "selected", "opp1", (), "FAILED_REQUIREMENTS"),
        IntentTrace("BUY_ITEM", 1, "selected", "opp1", (), "FAILED_REQUIREMENTS"),
        IntentTrace("BUY_ITEM", 1, "selected", "opp1", (), "FAILED_REQUIREMENTS"),
    ]
    assert "infinite_same_failed_action" in RouteFamilyClassifier.detect_forbidden(traces_bad)


def test_detect_omniscient_hidden_source():
    """Verify gathering secret moon_resin without known leads is flagged as forbidden."""
    # 1. Has lead -> OK
    traces = [
        {"intent_kind": "HARVEST_RESOURCE", "target_id": "node_resin", "execution_result": "SUCCESS"},
    ]
    assert len(RouteFamilyClassifier.detect_forbidden(traces, known_leads={"moon_resin"})) == 0

    # 2. No lead -> Forbidden
    assert "omniscient_hidden_source" in RouteFamilyClassifier.detect_forbidden(traces, known_leads=set())
