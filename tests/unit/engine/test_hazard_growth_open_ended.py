"""Trauma-driven hazard growth works across the whole hazard domain (owner decision 12).

``hazard_level`` is open-ended: authored values run to 4.0. The growth step used to be
``min(1.0, hazard + 0.01)`` written only when greater, so it could never fire for a region authored
at 1.0 or above, which is every combat region.
"""

from __future__ import annotations

import pytest

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate, WorldUpdate
from src.engine.world_dynamics import (
    HAZARD_GROWTH_STEP,
    HAZARD_GROWTH_TRAUMA_THRESHOLD,
    WorldDynamicsSystem,
)


def _grown_hazard(hazard: float, trauma: float, trauma_delta: float = 0.0) -> float | None:
    region = RegionState(
        id="r", name="r", bounds=(0, 0, 10, 10), hazard_level=hazard, trauma_score=trauma
    )
    state = AuthoritativeState(tick=1, seed=1, regions={"r": region})
    update = StateUpdate(world_updates={"r": WorldUpdate(region_id="r", trauma_delta=trauma_delta)}
                         if trauma_delta else {})
    result = WorldDynamicsSystem.resolve_dynamics(state, update, generator=None)
    world_update = result.world_updates.get("r")
    return None if world_update is None else world_update.hazard_level_set


@pytest.mark.parametrize("authored", [0.0, 0.5, 0.99, 1.0, 2.0, 3.0, 4.0])
def test_hazard_grows_above_threshold_for_every_authored_value(authored: float) -> None:
    grown = _grown_hazard(authored, trauma=HAZARD_GROWTH_TRAUMA_THRESHOLD + 1.0)
    assert grown == pytest.approx(authored + HAZARD_GROWTH_STEP)


def test_growth_is_not_capped_at_one() -> None:
    assert _grown_hazard(3.0, trauma=111.0) > 3.0


def test_no_growth_at_or_below_the_threshold() -> None:
    assert _grown_hazard(2.0, trauma=HAZARD_GROWTH_TRAUMA_THRESHOLD) is None
    assert _grown_hazard(0.5, trauma=10.0) is None


def test_trauma_proposed_this_tick_counts_toward_the_threshold() -> None:
    assert _grown_hazard(2.0, trauma=49.5, trauma_delta=1.0) == pytest.approx(2.0 + HAZARD_GROWTH_STEP)
