from __future__ import annotations
import pytest
from src.observability.behavior.behavior_finding import BehaviorFinding
from src.observability.behavior.behavior_insight import BehaviorInsightGenerator


def test_behavior_insight_contains_evidence_and_recommendation():
    findings = [
        BehaviorFinding(
            finding_id="f1",
            finding_type="repeated_failure_loop",
            severity="WARNING",
            summary="Loop",
            affected_entities=(12,),
            tick_range=(5, 30),
            evidence_event_ids=(),
            evidence_episode_ids=("ep1", "ep2", "ep3"),
            suggested_systems=(),
            recommendation="Adapt"
        ),
        BehaviorFinding(
            finding_id="f2",
            finding_type="hidden_knowledge_suspicion",
            severity="ERROR",
            summary="Omni",
            affected_entities=(15,),
            tick_range=None,
            evidence_event_ids=("raw1",),
            evidence_episode_ids=(),
            suggested_systems=(),
            recommendation="Audit"
        ),
    ]

    generator = BehaviorInsightGenerator()
    insights = generator.generate(findings)

    assert len(insights) == 2
    
    # 1. Loop Insight
    loop_ins = [ins for ins in insights if ins.insight_id == "INS-LOOP-DETECTION"][0]
    assert loop_ins.affected_entities == (12,)
    assert "Loop" in loop_ins.findings or "f1" in loop_ins.findings
    assert "stagnant" in loop_ins.summary

    # 2. Omniscience Insight
    omni_ins = [ins for ins in insights if ins.insight_id == "INS-OMNISCIENCE-DETECTION"][0]
    assert omni_ins.affected_entities == (15,)
