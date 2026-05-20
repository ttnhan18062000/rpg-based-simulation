from __future__ import annotations
import pytest
from src.observability.live.event_publisher import LiveEventPublisher, LiveEventSubscriber, SubscriptionFilter
from src.observability.events import SimulationEvent

@pytest.fixture(autouse=True)
def reset_publisher():
    LiveEventPublisher.reset_instance()
    yield
    LiveEventPublisher.reset_instance()

def test_publisher_registration():
    pub = LiveEventPublisher.get_instance()
    filt = SubscriptionFilter()
    sub1 = LiveEventSubscriber(filt)
    sub2 = LiveEventSubscriber(filt)
    
    assert len(pub.subscribers) == 0
    
    pub.register(sub1)
    pub.register(sub2)
    assert len(pub.subscribers) == 2
    
    # Avoid duplicate registrations
    pub.register(sub1)
    assert len(pub.subscribers) == 2
    
    pub.unregister(sub1)
    assert len(pub.subscribers) == 1
    assert sub2 in pub.subscribers

def test_publisher_subscription_routing():
    pub = LiveEventPublisher.get_instance()
    
    sub_combat = LiveEventSubscriber(SubscriptionFilter(event_category="combat"))
    sub_quest = LiveEventSubscriber(SubscriptionFilter(event_category="quest"))
    
    pub.register(sub_combat)
    pub.register(sub_quest)
    
    ev_combat = SimulationEvent(
        event_type="hit",
        event_category="combat",
        tick=1,
        severity="INFO",
        source_system="combat_system",
        message="hit msg"
    )
    ev_quest = SimulationEvent(
        event_type="quest_accept",
        event_category="quest",
        tick=2,
        severity="INFO",
        source_system="quest_system",
        message="quest msg"
    )
    
    pub.publish(ev_combat)
    pub.publish(ev_quest)
    
    combat_events = sub_combat.get_events()
    quest_events = sub_quest.get_events()
    
    assert len(combat_events) == 1
    assert combat_events[0].event_type == "hit"
    
    assert len(quest_events) == 1
    assert quest_events[0].event_type == "quest_accept"

def test_subscriber_backpressure_eviction():
    # Set bounded capacity to 3
    filt = SubscriptionFilter()
    sub = LiveEventSubscriber(filt, capacity=3)
    
    # 1. Fill queue with INFO/DEBUG events
    ev1 = SimulationEvent(event_type="ev1", event_category="social", tick=1, severity="INFO", source_system="sys", message="1")
    ev2 = SimulationEvent(event_type="ev2", event_category="social", tick=2, severity="DEBUG", source_system="sys", message="2")
    ev3 = SimulationEvent(event_type="ev3", event_category="social", tick=3, severity="INFO", source_system="sys", message="3")
    
    sub.push(ev1)
    sub.push(ev2)
    sub.push(ev3)
    
    assert len(sub.queue) == 3
    assert sub.dropped_count == 0
    
    # 2. Push a fourth event - should evict ev2 (first DEBUG/INFO event found in search, index 1)
    ev4 = SimulationEvent(event_type="ev4", event_category="social", tick=4, severity="WARNING", source_system="sys", message="4")
    sub.push(ev4)
    
    assert len(sub.queue) == 3
    assert sub.dropped_count == 1
    # Queue should contain ev1, ev3, ev4 (ev2 was evicted)
    queued_types = [e.event_type for e in sub.queue]
    assert "ev2" not in queued_types
    assert queued_types == ["ev1", "ev3", "ev4"]

def test_subscriber_high_severity_preservation():
    # Set capacity to 2
    filt = SubscriptionFilter()
    sub = LiveEventSubscriber(filt, capacity=2)
    
    ev_crit1 = SimulationEvent(event_type="crit1", event_category="social", tick=1, severity="CRITICAL", source_system="sys", message="1")
    ev_crit2 = SimulationEvent(event_type="crit2", event_category="social", tick=2, severity="CRITICAL", source_system="sys", message="2")
    
    sub.push(ev_crit1)
    sub.push(ev_crit2)
    
    # Push low severity event - since queue is full of CRITICAL and has no low severity to evict,
    # it pops the oldest (crit1) to make space.
    ev_info = SimulationEvent(event_type="info1", event_category="social", tick=3, severity="INFO", source_system="sys", message="3")
    sub.push(ev_info)
    
    assert len(sub.queue) == 2
    assert sub.dropped_count == 1
    queued_types = [e.event_type for e in sub.queue]
    assert queued_types == ["crit2", "info1"]

def test_slow_subscriber_disconnection():
    pub = LiveEventPublisher.get_instance()
    filt = SubscriptionFilter()
    sub = LiveEventSubscriber(filt, capacity=1)
    pub.register(sub)
    
    # Push 50 events to force subscriber drop limit (threshold = 50 drops)
    # Since capacity is 1, each subsequent push drops 1 event.
    for i in range(52):
        ev = SimulationEvent(event_type=f"e_{i}", event_category="social", tick=i, severity="INFO", source_system="sys", message="msg")
        pub.publish(ev)
        
    # The subscriber should have disconnect_flag set to True
    assert sub.disconnect_flag
    
    # Future publish triggers automatic unregistration from the publisher list
    ev_extra = SimulationEvent(event_type="extra", event_category="social", tick=99, severity="INFO", source_system="sys", message="msg")
    pub.publish(ev_extra)
    
    # Sub should be cleanly removed from the publisher's subscriber list
    assert sub not in pub.subscribers
