"""TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (AC5): the real THROTTLED kernel still runs, on one anchored world, with a coarse band only.

The grade anchors are measured under ``audit_mode`` so they grade the rules and not host speed. That leaves the production path (no ``audit_mode``: the wall-clock
watchdog, the throttle, the replay backlog) without an anchor, so this one slow test keeps it covered. It is NOT an anchor: it reads nothing from
``grade_anchors.json`` and asserts no grade or event count, only that the kernel does not stall or crash, reaches the tick count, makes decisions and keeps a population.
Location: ``tests/unit/worldassembly/`` next to the population-stability tests (the default agreed in the ticket; perf-planner has no live session).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.worldassembly

WORLDS_ROOT = Path(__file__).resolve().parents[3] / "data" / "worlds"
WORLD, SEED, TICKS = "sandbox_world", 42, 150


@pytest.mark.slow
def test_throttled_kernel_does_not_stall_or_crash_and_keeps_a_population() -> None:
    from src.config.profiles import PROD_SMALL
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    state, report = WorldCompiler.compile(WorldRepository(str(WORLDS_ROOT)).load_world(WORLD), SEED)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})  # deliberately no audit_mode
    assert kernel._audit_mode is False
    events = 0
    try:
        for _ in range(TICKS):
            kernel.tick_once()
            events += kernel._current_tick_event_count
        reached = kernel._state.tick
        alive = sum(1 for e in kernel._state.entities.values() if e.combat.alive)
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
    assert reached == TICKS, f"stalled: reached tick {reached} of {TICKS}"
    assert events > 0, "no decisions or events were made in the whole run"
    assert alive > 0, f"population is gone: 0 of {report['entity_count']} alive"
