from __future__ import annotations
import pytest
from pydantic import ValidationError
from src.observability.live.event_publisher import SubscriptionFilter
from src.observability.events import SimulationEvent

def test_subscription_filter_matching():
    # 1. Blank filter matches everything
    filt = SubscriptionFilter()
    ev = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=42,
        severity="INFO",
        source_system="combat_system",
        message="test msg"
    )
    assert filt.matches(ev)

    # 2. Filter by type
    filt_type = SubscriptionFilter(event_type="test_event")
    assert filt_type.matches(ev)
    
    filt_type_bad = SubscriptionFilter(event_type="other_event")
    assert not filt_type_bad.matches(ev)

    # 3. Filter by category
    filt_cat = SubscriptionFilter(event_category="combat")
    assert filt_cat.matches(ev)
    
    filt_cat_bad = SubscriptionFilter(event_category="economy")
    assert not filt_cat_bad.matches(ev)

    # 4. Filter by severity_min
    filt_sev = SubscriptionFilter(severity_min="WARNING")
    # ev has INFO, which is lower than WARNING -> should drop
    assert not filt_sev.matches(ev)

    ev_warning = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=42,
        severity="WARNING",
        source_system="combat_system",
        message="test msg"
    )
    assert filt_sev.matches(ev_warning)

    ev_critical = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=42,
        severity="CRITICAL",
        source_system="combat_system",
        message="test msg"
    )
    assert filt_sev.matches(ev_critical)

    # 5. Filter by entity_id
    filt_ent = SubscriptionFilter(entity_id=101)
    ev_no_ent = ev
    assert not filt_ent.matches(ev_no_ent)

    ev_with_ent = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=42,
        severity="INFO",
        source_system="combat_system",
        message="test msg",
        entity_id=101
    )
    assert filt_ent.matches(ev_with_ent)

    ev_with_other_ent = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=42,
        severity="INFO",
        source_system="combat_system",
        message="test msg",
        entity_id=202
    )
    assert not filt_ent.matches(ev_with_other_ent)

    # 6. Filter by region_id and quest_id
    filt_complex = SubscriptionFilter(region_id="forest", quest_id="q123")
    ev_complex = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=42,
        severity="INFO",
        source_system="combat_system",
        message="test msg",
        region_id="forest",
        quest_id="q123"
    )
    assert filt_complex.matches(ev_complex)

    ev_complex_bad = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=42,
        severity="INFO",
        source_system="combat_system",
        message="test msg",
        region_id="desert",
        quest_id="q123"
    )
    assert not filt_complex.matches(ev_complex_bad)

def test_subscription_filter_extra_forbidden():
    # Verify that unknown filters are rejected by Pydantic's extra=forbid configuration
    with pytest.raises(ValidationError):
        SubscriptionFilter(unknown_field="hello")
