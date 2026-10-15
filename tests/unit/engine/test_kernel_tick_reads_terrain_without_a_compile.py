"""D72/D75: the terrain catalog is warmed with the other content singletons, so a kernel that was handed a state it did not compile in this process (a replay,
a saved state, the live server) can read a terrain cost inside a tick without loading the catalog there (WORLD-CAT-004, ContentHotPathViolation).
(TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1)"""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.content.terrain_cost import reset_terrain_costs
from src.content.warmup import ContentWarmupService
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world


def _moved(world: str, seed: int, ticks: int) -> int:
    state = compile_world(world, seed)  # the compile warms the terrain cache; a fresh process handed a saved state would not have had it
    reset_terrain_costs()
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(seed), flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    start = {eid: e.navigation.position for eid, e in state.entities.items()}
    for _ in range(ticks):
        kernel.tick_once()
    moved = sum(1 for eid, e in kernel._state.entities.items() if eid in start and e.navigation.position != start[eid])
    kernel.shutdown()
    return moved


def test_a_kernel_tick_on_a_state_that_was_not_compiled_in_process_does_not_raise():
    assert _moved("frontier_living_world", 42, 80) > 0  # entities walked, so the movement pre-check read terrain costs inside the ticks


def test_warmup_installs_the_terrain_catalog_and_reset_clears_it():
    from src.content import terrain_cost as tc

    reset_terrain_costs()
    assert tc._costs_cache is None
    ContentWarmupService.warmup()
    assert tc._costs_cache is not None and "forest" in tc._costs_cache
    ContentWarmupService.reset()
    assert tc._costs_cache is None
