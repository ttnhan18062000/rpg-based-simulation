"""Unit tests for EconomyHealthMonitor.check_alerts() and alert event kinds.

Test plan reference: staging_artifacts/TCK-20260619-E33B-ALERTS-REST/test_plan.md
Ticket: TCK-20260619-E33B-ALERTS-REST
"""
from __future__ import annotations

import pytest

from src.economy.health_monitor import EconomyHealthMonitor, EconomyHealthSnapshot
from src.observability.events import (
    SimulationEvent,
    InflationSpiralEvent,
    GoldHoardingEvent,
    DeflationRiskEvent,
    EconomicCollapseEvent,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snapshot(gini: float, velocity: float = 0.0, tick: int = 100) -> EconomyHealthSnapshot:
    return EconomyHealthSnapshot(
        tick=tick,
        gini_coefficient=gini,
        transaction_velocity=velocity,
        avg_price_index={},
    )


# ---------------------------------------------------------------------------
# TC-B01: INFLATION_SPIRAL fires above gini threshold
# ---------------------------------------------------------------------------

def test_inflation_spiral_fires_above_gini_threshold():
    """gini > 0.7 (but <= 0.8) emits exactly one InflationSpiralEvent."""
    snapshot = _snapshot(gini=0.75)
    alerts = EconomyHealthMonitor.check_alerts(snapshot, tick=100)

    assert len(alerts) == 1
    alert = alerts[0]
    assert isinstance(alert, InflationSpiralEvent)
    assert alert.event_type == "INFLATION_SPIRAL"
    assert alert.event_category == "economy"
    assert alert.gini_coefficient == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# TC-B02: GOLD_HOARDING fires above 0.8 gini (takes precedence over INFLATION_SPIRAL)
# ---------------------------------------------------------------------------

def test_gold_hoarding_fires_above_08_gini():
    """gini > 0.8 emits exactly one GoldHoardingEvent (not InflationSpiralEvent)."""
    snapshot = _snapshot(gini=0.85)
    alerts = EconomyHealthMonitor.check_alerts(snapshot, tick=200)

    assert len(alerts) == 1
    alert = alerts[0]
    assert isinstance(alert, GoldHoardingEvent)
    assert alert.event_type == "GOLD_HOARDING"
    assert alert.event_category == "economy"
    assert alert.gini_coefficient == pytest.approx(0.85)


# ---------------------------------------------------------------------------
# TC-B03: No alert below thresholds
# ---------------------------------------------------------------------------

def test_no_alert_below_thresholds():
    """gini <= 0.7 emits no alerts."""
    for gini in (0.0, 0.3, 0.5, 0.69, 0.70):
        snapshot = _snapshot(gini=gini)
        alerts = EconomyHealthMonitor.check_alerts(snapshot, tick=100)
        assert alerts == [], f"Expected no alert for gini={gini}, got {alerts}"


# ---------------------------------------------------------------------------
# TC-B04: check_alerts returns a list of SimulationEvent
# ---------------------------------------------------------------------------

def test_check_alerts_returns_list():
    """Return type is always a list; each item is a SimulationEvent subclass."""
    for gini in (0.0, 0.75, 0.85):
        snapshot = _snapshot(gini=gini)
        result = EconomyHealthMonitor.check_alerts(snapshot, tick=100)
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        for item in result:
            assert isinstance(item, SimulationEvent), (
                f"Expected SimulationEvent, got {type(item)}"
            )


# ---------------------------------------------------------------------------
# TC-B05: Alert events carry correct fields (region_id, tick, message)
# ---------------------------------------------------------------------------

def test_alert_events_have_correct_fields():
    """Alerts carry region_id, tick, event_category='economy', non-empty message."""
    snapshot = _snapshot(gini=0.75, tick=300)
    alerts = EconomyHealthMonitor.check_alerts(snapshot, tick=300, region_id="north")

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.region_id == "north"
    assert alert.tick == 300
    assert alert.event_category == "economy"
    assert alert.source_system == "economy_health_monitor"
    assert len(alert.message) > 0


def test_alert_events_have_correct_fields_no_region():
    """Alerts work with region_id=None (global economy)."""
    snapshot = _snapshot(gini=0.82, tick=500)
    alerts = EconomyHealthMonitor.check_alerts(snapshot, tick=500, region_id=None)

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.region_id is None
    assert alert.tick == 500


# ---------------------------------------------------------------------------
# TC-B06: Alert event kinds are importable and correctly typed
# ---------------------------------------------------------------------------

def test_alert_event_kinds_defined():
    """All 4 alert event kinds can be instantiated and have correct event_type."""
    deflation = DeflationRiskEvent(tick=1, gini_coefficient=0.05)
    assert deflation.event_type == "DEFLATION_RISK"
    assert deflation.event_category == "economy"
    assert deflation.severity == "WARNING"

    inflation = InflationSpiralEvent(tick=1, gini_coefficient=0.75)
    assert inflation.event_type == "INFLATION_SPIRAL"
    assert inflation.event_category == "economy"
    assert inflation.severity == "WARNING"

    collapse = EconomicCollapseEvent(tick=1, gini_coefficient=0.0)
    assert collapse.event_type == "ECONOMIC_COLLAPSE"
    assert collapse.event_category == "economy"
    assert collapse.severity == "CRITICAL"

    hoarding = GoldHoardingEvent(tick=1, gini_coefficient=0.85)
    assert hoarding.event_type == "GOLD_HOARDING"
    assert hoarding.event_category == "economy"
    assert hoarding.severity == "WARNING"


# ---------------------------------------------------------------------------
# TC-B07: Exact boundary conditions
# ---------------------------------------------------------------------------

def test_alert_boundary_exactly_at_threshold():
    """Boundary conditions for INFLATION_SPIRAL (>0.7) and GOLD_HOARDING (>0.8).

    At exactly 0.7: no alert (strictly >).
    At 0.701: INFLATION_SPIRAL.
    At exactly 0.8: INFLATION_SPIRAL (> 0.7 but not > 0.8).
    At 0.801: GOLD_HOARDING (takes precedence, checked first).
    """
    # Exactly at INFLATION_SPIRAL threshold — no alert
    assert EconomyHealthMonitor.check_alerts(_snapshot(0.700), tick=100) == []

    # Just above INFLATION_SPIRAL threshold
    alerts = EconomyHealthMonitor.check_alerts(_snapshot(0.701), tick=100)
    assert len(alerts) == 1
    assert isinstance(alerts[0], InflationSpiralEvent)

    # Exactly at GOLD_HOARDING threshold: gini > 0.8 is False, gini > 0.7 is True → INFLATION_SPIRAL
    alerts_at_08 = EconomyHealthMonitor.check_alerts(_snapshot(0.800), tick=100)
    assert len(alerts_at_08) == 1
    assert isinstance(alerts_at_08[0], InflationSpiralEvent)

    # Just above GOLD_HOARDING threshold
    alerts_hoard = EconomyHealthMonitor.check_alerts(_snapshot(0.801), tick=100)
    assert len(alerts_hoard) == 1
    assert isinstance(alerts_hoard[0], GoldHoardingEvent)


# ---------------------------------------------------------------------------
# TC-B08: check_alerts does not mutate the snapshot
# ---------------------------------------------------------------------------

def test_check_alerts_does_not_mutate_snapshot():
    """check_alerts must not alter the snapshot passed in."""
    snapshot = _snapshot(gini=0.75)
    gini_before = snapshot.gini_coefficient
    EconomyHealthMonitor.check_alerts(snapshot, tick=100)
    assert snapshot.gini_coefficient == gini_before
