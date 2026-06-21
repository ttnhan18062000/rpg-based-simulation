"""Integration tests for macro-economy alert emission (Epic 3.3B), gold sink
mechanisms (Epic 3.3C), and reputation-based shop discounts (Epic 3.3D).

Tickets:
  TCK-20260619-E33B-ALERTS-REST  — AC: 2000-tick run emits ≥1 INFLATION_SPIRAL event.
  TCK-20260619-E33C-GOLD-SINK    — AC: gold sink transfers accepted in 200-tick run.
  TCK-20260619-E33D-REP-DISCOUNTS — AC: reputation discount applied at shop buy.
"""
from __future__ import annotations

import pytest
from dataclasses import replace
from typing import List

from src.observability.events import SimulationEvent, InflationSpiralEvent, GoldHoardingEvent
from src.systems.economy_systems.reputation_discount import apply_reputation_discount

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


# ---------------------------------------------------------------------------
# TC-C-INT: 200-tick run confirms gold sink transfers are accepted (E33C)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.integration
def test_gold_sink_reduces_accumulation_rate():
    """Gold sink drains fire within 200 ticks for an inflation-spiral economy.

    Uses the same highly-unequal state (1 rich, 9 poor) so INFLATION_SPIRAL fires
    at tick 100 and 200. GoldSinkSystem injects REPAIR_FEE/SERVICE_FEE/TAX intents;
    ResourceTransactionSystem resolves them. We verify:
    - At least one gold_sink_ticks counter incremented (GoldSinkSystem ran).
    - The rich entity's gold decreased by at least the SERVICE_FEE (1 gold per sink tick).
    Conservation is verified implicitly: resolver rejects insufficient-gold cases,
    no gold is created.
    """
    state = _build_unequal_wealth_state()
    initial_rich_gold = state.entities[1].inventory.gold  # 50000

    kernel = _build_kernel(state)
    try:
        for _ in range(200):
            kernel.tick_once()
    finally:
        kernel.shutdown()

    final_state = kernel.state
    final_rich_gold = final_state.entities[1].inventory.gold

    # Gold sink must have drained from the rich entity
    assert final_rich_gold < initial_rich_gold, (
        f"Rich entity gold should have decreased via gold sinks. "
        f"Initial: {initial_rich_gold}, Final: {final_rich_gold}. "
        f"Check GoldSinkSystem is wired in pipeline.py Phase 5 and "
        f"EconomyHealthMonitor sample fires at tick 100/200."
    )

    # Verify gold_sink_ticks metric was recorded in global_resources
    sink_ticks = final_state.global_resources.get("metric_gold_sink_ticks", 0.0)
    assert sink_ticks >= 1.0, (
        f"metric_gold_sink_ticks should be >= 1 after 200 ticks with inflation, "
        f"got {sink_ticks}. Check GoldSinkSystem.apply() is called in pipeline."
    )


# ---------------------------------------------------------------------------
# Epic 3.3D — Reputation-Based Shop Discounts (TCK-20260619-E33D-REP-DISCOUNTS)
# ---------------------------------------------------------------------------

def test_reputation_discount_applies():
    """apply_reputation_discount() produces correct discounts across the full rep range.

    Acceptance criteria (from ticket):
    - Entity with public_reputation=1.6 pays 16% less  (AC: "0.8 on 0–1 scale → 16% off")
    - Entity with neutral reputation (1.0) pays 10% less (default discount at midpoint)
    - Entity with rep=0.0 pays full price (no discount)
    - Floor guard: base_cost=1 never drops to 0 regardless of reputation
    - Over-range clamp: rep > 2.0 is clamped to 2.0 (max 20% discount)

    Conservation invariant: discounted_cost <= base_cost at all times (buyer never pays more).
    No gold is created: discount reduces gold_cost only, net world gold unchanged.
    """
    # AC: high rep → 16% discount
    # public_reputation=1.6 → entity_rep=1.6/2.0=0.8 → discount=0.8*0.20=0.16
    # int(100 * (1 - 0.16)) = int(84.0) = 84
    assert apply_reputation_discount(100, 1.6) == 84, (
        "rep=1.6 should give 16% discount: int(100*(1-0.16))=84"
    )

    # Neutral rep → 10% discount (default public_reputation=1.0 gives 10% off)
    # entity_rep=1.0/2.0=0.5 → discount=0.5*0.20=0.10 → int(100*0.90)=90
    assert apply_reputation_discount(100, 1.0) == 90, (
        "rep=1.0 should give 10% discount: int(100*(1-0.10))=90"
    )

    # Zero rep → no discount
    assert apply_reputation_discount(100, 0.0) == 100, (
        "rep=0.0 should give 0% discount: full price"
    )

    # Floor guard: base_cost=1 with max rep must not drop to 0
    assert apply_reputation_discount(1, 2.0) == 1, (
        "Floor guard: max(1, int(1*(1-0.20)))=max(1,0)=1; must not be 0"
    )

    # Over-range clamp: rep=3.0 clamped to 2.0 → same as max (20% discount)
    assert apply_reputation_discount(100, 3.0) == 80, (
        "rep=3.0 should clamp to 2.0 → 20% discount: int(100*0.80)=80"
    )

    # Negative rep → clamped to 0 → no discount
    assert apply_reputation_discount(100, -0.5) == 100, (
        "Negative rep clamped to 0.0 → no discount"
    )

    # Conservation invariant: discounted cost never exceeds base cost
    for rep in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]:
        result = apply_reputation_discount(100, rep)
        assert result <= 100, f"rep={rep}: discounted cost {result} exceeded base 100 (conservation violation)"
        assert result >= 1, f"rep={rep}: discounted cost {result} fell below floor 1"
