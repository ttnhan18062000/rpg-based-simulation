"""
E52E — CalamityPressurePropagator: seasonal calamity_intensity propagation
between adjacent regions.

Ticket: TCK-20260628-E52E-SEASONAL-PROPAGATION
"""
from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, RegionState
from src.world.calamity import CalamityPressurePropagator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INTERVAL = CalamityPressurePropagator.SEASONAL_PROPAGATION_INTERVAL  # 500
FACTOR = CalamityPressurePropagator.PROPAGATION_FACTOR               # 0.15
THRESHOLD = CalamityPressurePropagator.PROPAGATION_THRESHOLD          # 0.10


def _region(rid: str, bounds: tuple, calamity: float = 0.0) -> RegionState:
    return RegionState(id=rid, name=rid, bounds=bounds, calamity_intensity=calamity)


def _state(tick: int, regions: dict) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=42, regions=regions)


# Two regions sharing an edge (gap = 0 ≤ 50): adjacent
_R_A = _region("A", (0, 0, 100, 100))
_R_B = _region("B", (100, 0, 200, 100))
# Region far away (gap = 100 > 50): not adjacent to A
_R_C = _region("C", (200, 0, 300, 100))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_noop_when_not_seasonal_tick():
    r_a = replace(_R_A, calamity_intensity=0.5)
    state = _state(tick=501, regions={"A": r_a, "B": _R_B})
    upd = CalamityPressurePropagator.propagate_seasonal(state)
    assert upd.is_noop()


def test_noop_at_tick_zero():
    r_a = replace(_R_A, calamity_intensity=0.5)
    state = _state(tick=0, regions={"A": r_a, "B": _R_B})
    upd = CalamityPressurePropagator.propagate_seasonal(state)
    assert upd.is_noop()


def test_noop_when_no_region_above_threshold():
    r_a = replace(_R_A, calamity_intensity=THRESHOLD - 0.01)
    state = _state(tick=INTERVAL, regions={"A": r_a, "B": _R_B})
    upd = CalamityPressurePropagator.propagate_seasonal(state)
    assert upd.is_noop()


def test_adjacent_region_receives_propagated_intensity():
    source_intensity = 0.4
    r_a = replace(_R_A, calamity_intensity=source_intensity)
    state = _state(tick=INTERVAL, regions={"A": r_a, "B": _R_B})
    upd = CalamityPressurePropagator.propagate_seasonal(state)

    assert not upd.is_noop()
    assert "B" in upd.world_updates
    expected = min(1.0, _R_B.calamity_intensity + source_intensity * FACTOR)
    assert upd.world_updates["B"].calamity_intensity_set == pytest.approx(expected)


def test_non_adjacent_region_unaffected():
    r_a = replace(_R_A, calamity_intensity=0.8)
    state = _state(tick=INTERVAL, regions={"A": r_a, "B": _R_B, "C": _R_C})
    upd = CalamityPressurePropagator.propagate_seasonal(state)

    # C is far from A (gap = 100 > ADJACENCY_GAP=50) — must not be updated
    assert "C" not in upd.world_updates


def test_intensity_capped_at_one():
    r_a = replace(_R_A, calamity_intensity=1.0)
    r_b = replace(_R_B, calamity_intensity=0.95)
    state = _state(tick=INTERVAL, regions={"A": r_a, "B": r_b})
    upd = CalamityPressurePropagator.propagate_seasonal(state)

    assert upd.world_updates["B"].calamity_intensity_set == pytest.approx(1.0)


def test_source_region_not_self_updated():
    r_a = replace(_R_A, calamity_intensity=0.5)
    state = _state(tick=INTERVAL, regions={"A": r_a, "B": _R_B})
    upd = CalamityPressurePropagator.propagate_seasonal(state)
    # Source region A should not appear in updates — it does not spread to itself
    assert "A" not in upd.world_updates


def test_propagation_runs_at_second_seasonal_tick():
    r_a = replace(_R_A, calamity_intensity=0.3)
    state = _state(tick=INTERVAL * 2, regions={"A": r_a, "B": _R_B})
    upd = CalamityPressurePropagator.propagate_seasonal(state)
    assert not upd.is_noop()
    assert "B" in upd.world_updates
