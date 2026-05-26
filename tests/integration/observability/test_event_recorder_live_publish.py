from __future__ import annotations
import os
import shutil
import pytest
from src.observability.event_recorder import EventRecorder
from src.observability.live.event_publisher import LiveEventPublisher, LiveEventSubscriber, SubscriptionFilter
from src.observability.events import SimulationEvent

@pytest.fixture(autouse=True)
def clean_run_dir():
    run_dir = "tests/run_data_live_publish_test"
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    LiveEventPublisher.reset_instance()
    yield run_dir
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    LiveEventPublisher.reset_instance()

def test_event_recorder_integration(clean_run_dir):
    run_dir = clean_run_dir
    recorder = EventRecorder(run_dir=run_dir, max_events=10)
    
    # 1. Register subscriber with the publisher
    pub = LiveEventPublisher.get_instance()
    filt = SubscriptionFilter(event_category="combat")
    sub = LiveEventSubscriber(filt)
    pub.register(sub)
    
    # 2. Record matching event
    ev1 = SimulationEvent(
        event_type="swing_sword",
        event_category="combat",
        tick=5,
        severity="INFO",
        source_system="combat_system",
        message="swinging sword"
    )
    recorder.record(ev1)
    
    # 3. Record non-matching event
    ev2 = SimulationEvent(
        event_type="buy_potion",
        event_category="economy",
        tick=6,
        severity="INFO",
        source_system="trade_system",
        message="buying potion"
    )
    recorder.record(ev2)
    
    # Verify file-system storage works
    assert os.path.exists(os.path.join(run_dir, "simulation_events.jsonl"))
    
    # Verify memory buffers are populated
    assert len(recorder.events) == 2
    
    # Verify live event publication routing
    live_events = sub.get_events()
    assert len(live_events) == 1
    assert live_events[0].event_type == "swing_sword"
    
    # Clean up
    recorder.shutdown()

def test_event_recorder_publisher_disabled(clean_run_dir):
    run_dir = clean_run_dir
    recorder = EventRecorder(run_dir=run_dir, max_events=10)
    
    # Disable the live event publisher
    pub = LiveEventPublisher.get_instance()
    pub.enabled = False
    
    sub = LiveEventSubscriber(SubscriptionFilter())
    pub.register(sub)
    
    ev = SimulationEvent(
        event_type="level_up",
        event_category="lifecycle",
        tick=1,
        severity="CRITICAL",
        source_system="sys",
        message="level up"
    )
    recorder.record(ev)
    
    # Memory and disk storage still active
    assert len(recorder.events) == 1
    assert os.path.exists(os.path.join(run_dir, "simulation_events.jsonl"))
    
    # No live events published
    assert len(sub.get_events()) == 0
    
    recorder.shutdown()
