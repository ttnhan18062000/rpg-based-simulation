"""Conservation over a pinned run (EXCH-02): no phase creates or destroys coin. The world total (entity purses alive or dead, building
purses, corpses and treasuries) changes only by declared world-creation coin, here the purse a runtime spawn arrives with."""
from __future__ import annotations

import pytest

from src.config.profiles import PROD_SMALL
from src.core.treasury import total_coin
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import DEFAULT_SEED, compile_world

TICKS = 300  # past the first tax ticks (the first is on tick 20) and the first fights


def _drift(world: str) -> tuple[float, float]:
    state = compile_world(world)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                    governor=PinnedNormalGovernor(), flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True},
                    executor=LocalSequentialExecutor())
    try:
        start, seen, created = total_coin(kernel.state), set(kernel.state.entities), 0.0
        for _ in range(TICKS):
            kernel.tick_once()
            for eid, e in kernel.state.entities.items():
                if eid not in seen:
                    seen.add(eid)
                    created += e.inventory.gold  # a spawn's declared purse is world-creation coin
        return total_coin(kernel.state) - (start + created), start
    finally:
        kernel.shutdown()


@pytest.mark.parametrize("world", ["frontier_living_world", "urban_political"])
def test_no_tick_creates_or_destroys_coin(world):
    drift, start = _drift(world)
    assert drift == 0.0, f"{world}: {drift:+.1f} coin appeared (+) or vanished (-) over {TICKS} ticks (start {start:.0f})"
