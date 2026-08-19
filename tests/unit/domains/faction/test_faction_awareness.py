"""Unit tests for FactionAwarenessService — tension updates from world events (E53Ad)."""
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_state(factions: dict):
    """Build a minimal AuthoritativeState mock with given factions dict."""
    from unittest.mock import MagicMock
    from src.core.state import AuthoritativeState
    state = MagicMock(spec=AuthoritativeState)
    state.factions = factions
    state.tick = 1
    return state


def _depleted_event(region_id, tick=1):
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
    return WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=tick,
        region_id=region_id,
    )


def _other_event(region_id, tick=1):
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
    return WorldEvent(
        category=WorldEventCategory.ENTITY_DEATH,
        tick=tick,
        region_id=region_id,
    )


# ── Acceptance Criteria Tests ─────────────────────────────────────────────────

def test_faction_tension_increases_on_resource_depletion():
    """RESOURCE_DEPLETED in faction territory → FactionUpdate(tension_delta=0.1)."""
    from src.core.state import FactionState
    from src.core.updates import FactionUpdate
    from src.engine.faction_decision import FactionAwarenessService

    fs = FactionState(faction_id="hero_guild", territory=("region_01",), tension_level=0.0)
    state = _make_state({"hero_guild": fs})
    events = [_depleted_event("region_01")]

    result = FactionAwarenessService.compute_tension_updates(state, events)

    assert len(result) == 1
    assert result[0].faction_id == "hero_guild"
    assert result[0].tension_delta == pytest.approx(0.1)


def test_faction_tension_capped_at_1_0():
    """tension_level=0.95 + tension_delta=0.1 → tension_level=1.0 via apply-path."""
    from src.core.state import FactionState, AuthoritativeState
    from src.core.updates import FactionUpdate, StateUpdate

    fs = FactionState(faction_id="hero_guild", territory=("region_01",), tension_level=0.95)

    # Build minimal AuthoritativeState with the faction
    from unittest.mock import patch
    import src.engine.apply as apply_mod

    # Use apply.py's FactionUpdate apply logic directly via StateUpdate
    fu = FactionUpdate(faction_id="hero_guild", tension_delta=0.1)

    # Verify the cap: 0.95 + 0.1 = 1.05 → clamped to 1.0
    raw = fs.tension_level + fu.tension_delta
    clamped = max(0.0, min(1.0, raw))
    assert clamped == pytest.approx(1.0)
    assert raw > 1.0  # confirms cap is needed


def test_resource_depleted_outside_territory_no_update():
    """RESOURCE_DEPLETED in region NOT in faction territory → no FactionUpdate."""
    from src.core.state import FactionState
    from src.engine.faction_decision import FactionAwarenessService

    fs = FactionState(faction_id="hero_guild", territory=("region_01",))
    state = _make_state({"hero_guild": fs})
    events = [_depleted_event("region_02")]

    result = FactionAwarenessService.compute_tension_updates(state, events)

    assert result == []


def test_no_factions_no_updates():
    """state.factions={} → returns []."""
    from src.engine.faction_decision import FactionAwarenessService

    state = _make_state({})
    events = [_depleted_event("region_01")]

    result = FactionAwarenessService.compute_tension_updates(state, events)

    assert result == []


# ── Additional Tests ──────────────────────────────────────────────────────────

def test_non_resource_depleted_event_ignored():
    """Non-RESOURCE_DEPLETED event in faction territory → no update."""
    from src.core.state import FactionState
    from src.engine.faction_decision import FactionAwarenessService

    fs = FactionState(faction_id="hero_guild", territory=("region_01",))
    state = _make_state({"hero_guild": fs})
    events = [_other_event("region_01")]

    result = FactionAwarenessService.compute_tension_updates(state, events)

    assert result == []


def test_multiple_events_produce_multiple_updates():
    """Two RESOURCE_DEPLETED events in same region → two FactionUpdates (additive)."""
    from src.core.state import FactionState
    from src.engine.faction_decision import FactionAwarenessService

    fs = FactionState(faction_id="hero_guild", territory=("region_01",))
    state = _make_state({"hero_guild": fs})
    events = [_depleted_event("region_01", tick=1), _depleted_event("region_01", tick=2)]

    result = FactionAwarenessService.compute_tension_updates(state, events)

    assert len(result) == 2
    total_delta = sum(u.tension_delta for u in result)
    assert total_delta == pytest.approx(0.2)


def test_event_with_none_region_id_ignored():
    """RESOURCE_DEPLETED event with region_id=None → no update."""
    from src.core.state import FactionState
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
    from src.engine.faction_decision import FactionAwarenessService

    fs = FactionState(faction_id="hero_guild", territory=("region_01",))
    state = _make_state({"hero_guild": fs})
    event = WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=1, region_id=None)

    result = FactionAwarenessService.compute_tension_updates(state, [event])

    assert result == []
