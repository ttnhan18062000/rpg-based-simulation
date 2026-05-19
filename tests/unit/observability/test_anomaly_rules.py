from __future__ import annotations
import pytest
from src.observability.events import SimulationEvent
from src.observability.anomaly.rules import (
    HardLawViolationRule, NavigationStuckRule, QuestStalledRule,
    CombatNeverEndsRule, ResourceNodeCrowdingRule
)

def test_hard_law_violation_rule():
    rule = HardLawViolationRule()
    events = [
        SimulationEvent(
            event_type="InvariantViolation", event_category="hard_law", tick=10,
            severity="CRITICAL", source_system="hard_law_monitor", message="Breached HP law",
            entity_id=1, payload={"hp": -10}
        )
    ]
    anomalies = rule.evaluate(events)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "HardLawViolationRule"
    assert anomalies[0].severity == "CRITICAL"
    assert anomalies[0].entity_id == 1
    assert anomalies[0].tick_detected == 10
    assert "Breached HP law" in anomalies[0].message

def test_navigation_stuck_rule():
    rule = NavigationStuckRule(tick_threshold=30)
    events = []
    # Emit movement events for entity 1 where position stays at (10, 20)
    for t in range(0, 40, 10):
        events.append(SimulationEvent(
            event_type="movement", event_category="movement", tick=t,
            severity="INFO", source_system="locomotion_system", message="moved",
            entity_id=1, payload={"end_pos": (10.0, 20.0)}
        ))
    
    anomalies = rule.evaluate(events)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "NavigationStuckRule"
    assert anomalies[0].severity == "ERROR"
    assert anomalies[0].entity_id == 1
    assert anomalies[0].tick_detected == 30

def test_quest_stalled_rule():
    rule = QuestStalledRule(tick_threshold=50)
    events = [
        # Quest started at tick 10
        SimulationEvent(
            event_type="quest_event", event_category="quest", tick=10,
            severity="INFO", source_system="quest_system", message="quest started",
            entity_id=1, payload={"quest_id": "quest_99", "status": "started"}
        ),
        # Final tick event to mark time progression
        SimulationEvent(
            event_type="info", event_category="lifecycle", tick=70,
            severity="INFO", source_system="kernel", message="running"
        )
    ]

    anomalies = rule.evaluate(events)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "QuestStalledRule"
    assert anomalies[0].severity == "WARNING"
    assert anomalies[0].entity_id == 1
    assert anomalies[0].tick_detected == 70
    assert anomalies[0].context["duration_ticks"] == 60

def test_combat_never_ends_rule():
    rule = CombatNeverEndsRule(tick_threshold=30)
    events = []
    # Continuous combat damage without killer resolution
    for t in range(0, 35, 5):
        events.append(SimulationEvent(
            event_type="combat_damage", event_category="combat", tick=t,
            severity="INFO", source_system="combat_system", message="damaged",
            entity_id=1, payload={"damage": 5}
        ))
    
    anomalies = rule.evaluate(events)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "CombatNeverEndsRule"
    assert anomalies[0].severity == "ERROR"
    assert anomalies[0].entity_id == 1
    assert anomalies[0].tick_detected == 30

def test_resource_crowding_rule():
    rule = ResourceNodeCrowdingRule(entity_limit=2)
    # 3 entities harvesting node "gold_node_1" in the same tick (tick 5)
    events = [
        SimulationEvent(
            event_type="gold_transaction", event_category="resource", tick=5,
            severity="INFO", source_system="economy_system", message="harvested",
            entity_id=1, payload={"target_id": "gold_node_1"}
        ),
        SimulationEvent(
            event_type="gold_transaction", event_category="resource", tick=5,
            severity="INFO", source_system="economy_system", message="harvested",
            entity_id=2, payload={"target_id": "gold_node_1"}
        ),
        SimulationEvent(
            event_type="gold_transaction", event_category="resource", tick=5,
            severity="INFO", source_system="economy_system", message="harvested",
            entity_id=3, payload={"target_id": "gold_node_1"}
        )
    ]
    anomalies = rule.evaluate(events)
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "ResourceNodeCrowdingRule"
    assert anomalies[0].severity == "WARNING"
    assert anomalies[0].tick_detected == 5
    assert anomalies[0].context["entities_count"] == 3
