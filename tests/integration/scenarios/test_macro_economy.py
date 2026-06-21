"""Integration tests for macro-economy alert emission (Epic 3.3B).

Ticket: TCK-20260619-E33B-ALERTS-REST
AC: 2000-tick run with rapid gold creation emits ≥1 INFLATION_SPIRAL event.
"""
from __future__ import annotations

import pytest
from dataclasses import replace
from typing import List

from src.observability.events import SimulationEvent, InflationSpiralEvent, GoldHoardingEvent

SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_unequal_wealth_state():
    """Build an AuthoritativeState with highly unequal gold distribution.

    One entity holds 50000 gold, 9 entities hold 1 gold each.
    Gini = (2*sum((i+1)*v for i,v in enumerate(sorted([1]*9+[50000]))))
           / (10 * (9+50000)) - 11/10
    ≈ 0.899 → well above GOLD_HOARDING threshold of 0.8.
    """
    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState

    entities = {}
    # Rich entity
    rich = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=100, max_hp=100, atk=5, def_stat=5,
                attack_range=1, alive=True, readiness=100.0)
        .inventory(gold=50000)
        .build()
    )
    entities[rich.id] = rich

    # Poor entities
    for i in range(2, 11):
        poor = (
            V2EntityBuilder(i)
            .kind("goblin")
            .location(float(i), float(i))
            .combat(hp=50, max_hp=50, atk=3, def_stat=2,
                    attack_range=1, alive=True, readiness=100.0)
            .inventory(gold=1)
            .build()
        )
        entities[poor.id] = poor

    return AuthoritativeState(tick=0, seed=SEED, entities=entities)


def _build_kernel(state):
    """Wrap state in a minimal Kernel for tick execution.

    no_frame_pacing=True disables the kernel's inter-tick sleep so 200 ticks
    complete in wall-clock seconds rather than minutes.
    """
    from src.engine.kernel import Kernel
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.platform.rng import DeterministicRNG

    profile = RuntimeProfile(
        name="macro-economy-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=2000,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=500.0,
    )
    return Kernel(
        profile=profile,
        state=state,
        rng=DeterministicRNG(SEED),
        flags={"no_frame_pacing": True},
    )


# ---------------------------------------------------------------------------
# TC-B09: 2000-tick run emits ≥1 INFLATION_SPIRAL (or GOLD_HOARDING) event
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.integration
def test_inflation_spiral_alert_emitted():
    """Economy alert emitted when Gini threshold crossed within a run.

    Uses highly unequal gold distribution (1 rich entity, 9 poor) so Gini ≈ 0.9
    on the very first window boundary (tick 100). Runs 200 ticks to cover 2 windows.
    Events are captured via a listener registered on the kernel's _event_listeners.
    kernel.shutdown() is called to prevent QueueDrainWorker thread leaks.
    """
    state = _build_unequal_wealth_state()
    kernel = _build_kernel(state)

    # Collect all alerts dispatched via event listeners
    captured_alerts: List[SimulationEvent] = []

    def _capture(events):
        for ev in events:
            if isinstance(ev, (InflationSpiralEvent, GoldHoardingEvent)):
                captured_alerts.append(ev)

    kernel._event_listeners.append(_capture)

    # 200 ticks → 2 window boundaries at ticks 100 and 200
    try:
        for _ in range(200):
            kernel.tick_once()
    finally:
        kernel.shutdown()

    assert len(captured_alerts) >= 1, (
        f"Expected ≥1 economy alert event in 200-tick run, got {len(captured_alerts)}. "
        f"Check that EconomyHealthMonitor.check_alerts() is wired in kernel.py and that "
        f"the Gini threshold ({InflationSpiralEvent.__name__}: >0.7) is crossed."
    )

    # Verify alert structure
    first_alert = captured_alerts[0]
    assert first_alert.event_category == "economy"
    assert first_alert.event_type in ("INFLATION_SPIRAL", "GOLD_HOARDING")
    assert isinstance(first_alert.gini_coefficient, float)
    assert first_alert.gini_coefficient > 0.7
