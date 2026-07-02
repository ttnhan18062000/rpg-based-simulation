"""
E52G — Sovereignty shift WorldEvent emission.

When a region's influence crosses ±100, a SOVEREIGNTY_SHIFT WorldEvent is emitted
into StateUpdate.world_events_add, making it observable via recent_world_events.

Ticket: TCK-20260628-E52G-SOVEREIGNTY-EVENTS
"""
from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate, WorldUpdate
from src.domains.world_emergence.schema import WorldEventCategory


def _region(rid: str, influence: float = 0.0, owner_faction_id=None) -> RegionState:
    return RegionState(
        id=rid,
        name=rid,
        bounds=(0, 0, 100, 100),
        influence=influence,
        owner_faction_id=owner_faction_id,
    )


def _state(regions: dict, tick: int = 1) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=42, regions=regions)


def _run_step22(state: AuthoritativeState, update: StateUpdate | None = None) -> StateUpdate:
    """Run WorldDynamicsSystem.resolve_dynamics at tick=1 with no generator (step 2.2 only)."""
    if update is None:
        update = StateUpdate()
    # Use a mock generator with no-op spawn methods
    class _FakeGen:
        _last_id = 0
        def spawn_monster(self, *a, **kw): raise AssertionError("not expected")
    from src.engine.world_dynamics import WorldDynamicsSystem
    from src.engine.cadence import SystemCadence
    cadence = SystemCadence(world_dynamics=9999)  # prevent cadence-gated sections from running
    return WorldDynamicsSystem.resolve_dynamics(state, update, _FakeGen(), cadence=cadence)


# ---------------------------------------------------------------------------
# SOVEREIGNTY_SHIFT enum value
# ---------------------------------------------------------------------------

def test_sovereignty_shift_category_exists():
    assert WorldEventCategory.SOVEREIGNTY_SHIFT == "SOVEREIGNTY_SHIFT"


# ---------------------------------------------------------------------------
# Sovereignty event emission
# ---------------------------------------------------------------------------

def test_sovereignty_shift_event_emitted_on_hero_takeover():
    region = _region("borderland", influence=110.0, owner_faction_id=None)
    state = _state({"borderland": region}, tick=500)
    upd = _run_step22(state)

    sv_events = [
        e for e in upd.world_events_add
        if e.category == WorldEventCategory.SOVEREIGNTY_SHIFT
    ]
    assert len(sv_events) == 1
    ev = sv_events[0]
    assert ev.region_id == "borderland"
    assert ev.subject == "HERO_GUILD"
    assert ev.tick == 500
    assert ev.severity == pytest.approx(0.9)


def test_sovereignty_shift_event_emitted_on_monster_takeover():
    region = _region("darkwood", influence=-110.0, owner_faction_id=None)
    state = _state({"darkwood": region}, tick=1)
    upd = _run_step22(state)

    sv_events = [
        e for e in upd.world_events_add
        if e.category == WorldEventCategory.SOVEREIGNTY_SHIFT
    ]
    assert len(sv_events) == 1
    assert sv_events[0].subject == "MONSTER_HORDE"


def test_no_sovereignty_event_when_influence_below_threshold():
    region = _region("meadow", influence=50.0)
    state = _state({"meadow": region})
    upd = _run_step22(state)

    sv_events = [
        e for e in upd.world_events_add
        if e.category == WorldEventCategory.SOVEREIGNTY_SHIFT
    ]
    assert sv_events == []


def test_sovereignty_event_payload_contains_influence():
    region = _region("frontier", influence=120.0)
    state = _state({"frontier": region}, tick=2000)
    upd = _run_step22(state)

    sv_events = [
        e for e in upd.world_events_add
        if e.category == WorldEventCategory.SOVEREIGNTY_SHIFT
    ]
    assert len(sv_events) == 1
    assert "influence" in sv_events[0].payload
    assert sv_events[0].payload["influence"] == pytest.approx(120.0)
