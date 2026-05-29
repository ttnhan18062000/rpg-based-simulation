from __future__ import annotations
import pytest
from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.behavior_episode import BehaviorEpisode
from src.observability.behavior.pattern_detectors import (
    RepeatedFailureLoopDetector,
    BehaviorChangeProofDetector,
    HiddenKnowledgeSuspicionDetector,
)


def test_repeated_failure_loop_detected():
    episodes = [
        BehaviorEpisode("ep1", "run_1", 12, "combat_episode", 5, 10, None, (), "failure", (), ""),
        BehaviorEpisode("ep2", "run_1", 12, "combat_episode", 15, 20, None, (), "failure", (), ""),
        BehaviorEpisode("ep3", "run_1", 12, "combat_episode", 25, 30, None, (), "failure", (), ""),
    ]

    detector = RepeatedFailureLoopDetector()
    findings = detector.detect(12, [], episodes)

    assert len(findings) == 1
    assert findings[0].finding_type == "repeated_failure_loop"
    assert findings[0].severity == "WARNING"
    assert findings[0].affected_entities == (12,)
    assert findings[0].tick_range == (5, 30)


def test_behavior_change_proof_detected():
    episodes = [
        BehaviorEpisode("ep4", "run_1", 12, "failure_response_episode", 2, 8, None, (), "resolved", (), ""),
    ]

    detector = BehaviorChangeProofDetector()
    findings = detector.detect(12, [], episodes)

    assert len(findings) == 1
    assert findings[0].finding_type == "successful_adaptation"
    assert findings[0].severity == "INFO"


def test_hidden_knowledge_suspicion_detected():
    events = [
        BehaviorEvent("run_1", 2, 12, "avoidance", "threat", source_event_ids=("raw1",)),
        BehaviorEvent("run_1", 4, 12, "avoidance", "threat", source_event_ids=("raw2",)),
        BehaviorEvent("run_1", 6, 12, "avoidance", "threat", source_event_ids=("raw3",)),
    ]

    detector = HiddenKnowledgeSuspicionDetector()
    findings = detector.detect(12, events, [])

    assert len(findings) == 1
    assert findings[0].finding_type == "hidden_knowledge_suspicion"
    assert findings[0].severity == "ERROR"
    assert findings[0].evidence_event_ids == ("raw1", "raw2", "raw3")
