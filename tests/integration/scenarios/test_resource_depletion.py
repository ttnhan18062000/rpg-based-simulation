"""
tests/integration/scenarios/test_resource_depletion.py
───────────────────────────────────────────────────────────────────────────────
Epic 2.1D — Scarcity Signal Verification

Two integration tests confirming the full depletion+recovery pipeline fires
end-to-end:

1. test_depletion_and_recovery_in_1000_tick_run
   Drives harvest (pipeline) then ecology (ecology service) in a controlled
   sequence over the 1000-tick window. Confirms both RESOURCE_DEPLETED and
   RESOURCE_RECOVERED appear across the accumulated event log.

2. test_regional_scarcity_rises_after_depletion
   Injects RESOURCE_DEPLETED events directly into state.recent_world_events
   and calls WorldEmergencePhase.execute() to assert that RegionalPressureModel
   and ScarcityModel both produce non-zero outputs.

Ticket: TCK-20260619-E21D-SCARCITY-VERIFY
"""
from __future__ import annotations

import pytest

from src.core.state import AuthoritativeState, ResourceNodeState, RegionState, ItemStack, InventoryComponent
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.domains.world_emergence.phase import WorldEmergencePhase
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.world.ecology import ResourceEcologyService
from src.core.builder import V2EntityBuilder


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_node(
    node_id: int = 1,
    remaining_charges: int = 2,
    max_charges: int = 2,
    regen_rate_per_tick: int = 1,
) -> ResourceNodeState:
    return ResourceNodeState(
        id=node_id,
        kind="WOOD",
        position=(0.0, 0.0),
        yields_item="wood",
        remaining_charges=remaining_charges,
        max_charges=max_charges,
        required_ticks=1,
        regen_rate_per_tick=regen_rate_per_tick,
    )


def _make_harvest_intent(node_id: int, txn_id: str = "txn-1") -> ResourceTransferIntent:
    return ResourceTransferIntent(
        transaction_id=txn_id,
        source_id=node_id,
        source_kind="NODE",
        items_add=[ItemStack("wood", 1)],
        transfer_kind="HARVEST",
    )


class _FakeGenerator:
    """Minimal stub for EntityGenerator — ecology seeding path uses rng.get_float."""
    class _RNG:
        def get_float(self, *args, **kwargs):
            return 0.9  # > 0.5 → no new nodes seeded

    rng = _RNG()


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.slow
@pytest.mark.integration
def test_depletion_and_recovery_in_1000_tick_run():
    """
    Assert RESOURCE_DEPLETED and RESOURCE_RECOVERED both appear in a 1000-tick run.

    Strategy: step through two logical phases without the kernel:

    Phase A — Depletion:
        Harvest a node with max_charges=2 twice via AuthoritativeApplyPipeline.refine().
        The second harvest that drains charges to 0 must emit RESOURCE_DEPLETED.

    Phase B — Recovery (ecology ticks at 200, 400, ..., 1000):
        Call ResourceEcologyService.process_ecology() on the depleted node at each
        200-tick boundary. The first call (tick=200) must emit RESOURCE_RECOVERED.

    Both event categories must appear in accumulated_events by tick 1000.
    """
    # ── Phase A: Depletion via harvest ──────────────────────────────────────
    entity = V2EntityBuilder(1).location(0.0, 0.0).combat(readiness=100.0).build()
    node = _make_node(node_id=1, remaining_charges=2, max_charges=2, regen_rate_per_tick=1)
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={1: node},
        regions={},
    )

    accumulated_events: list[WorldEvent] = []

    # Harvest #1 — charges: 2 → 1, no DEPLETED yet
    update_1 = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=[_make_harvest_intent(1, "txn-a")])
        }
    )
    refined_1 = AuthoritativeApplyPipeline.refine(state, update_1)
    accumulated_events.extend(refined_1.world_events_add)

    # Apply state so node has 1 charge remaining for next harvest
    from src.engine.apply import ApplyPath
    state = ApplyPath.apply_partial(state, refined_1)

    # Harvest #2 — charges: 1 → 0, DEPLETED must be emitted
    update_2 = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=[_make_harvest_intent(1, "txn-b")])
        }
    )
    refined_2 = AuthoritativeApplyPipeline.refine(state, update_2)
    accumulated_events.extend(refined_2.world_events_add)

    # Verify depletion event appeared before proceeding
    depleted_events = [
        e for e in accumulated_events if e.category == WorldEventCategory.RESOURCE_DEPLETED
    ]
    assert len(depleted_events) >= 1, (
        "RESOURCE_DEPLETED not emitted after draining node to 0 charges"
    )

    # Apply state so node has 0 charges for ecology
    state = ApplyPath.apply_partial(state, refined_2)

    # ── Phase B: Recovery via ecology (ticks 200, 400, ..., 1000) ───────────
    # Node is now at 0 charges — first ecology tick must recover it
    for tick in range(200, 1001, ResourceEcologyService.ECOLOGY_INTERVAL):
        ecology_state = AuthoritativeState(
            tick=tick,
            seed=state.seed,
            entities=dict(state.entities),
            resource_nodes=dict(state.resource_nodes),
            regions={},
        )
        ecology_update = ResourceEcologyService.process_ecology(ecology_state, _FakeGenerator())
        accumulated_events.extend(ecology_update.world_events_add)
        # Apply ecology update so node charges advance across intervals
        state = ApplyPath.apply_partial(ecology_state, ecology_update)

    recovered_events = [
        e for e in accumulated_events if e.category == WorldEventCategory.RESOURCE_RECOVERED
    ]
    assert len(recovered_events) >= 1, (
        f"RESOURCE_RECOVERED not emitted across ticks 200–1000. "
        f"Accumulated events: {[e.category for e in accumulated_events]}"
    )


def test_regional_scarcity_rises_after_depletion():
    """
    Assert RegionalPressureModel scarcity increases after depletion window.

    Injects 3 × RESOURCE_DEPLETED events into state.recent_world_events for
    region "test_region" and drives WorldEmergencePhase.execute() directly.

    Confirms:
    - At least one ResourceScarcitySignal with scarcity_level > 0 for "wood"
    - At least one RegionalPressure(pressure_kind="resource") with intensity > 0
    """
    region = RegionState(id="test_region", name="Test Region", bounds=(0, 0, 100, 100))

    depletion_events = [
        WorldEvent(
            category=WorldEventCategory.RESOURCE_DEPLETED,
            tick=5,
            region_id="test_region",
            subject="wood",
            severity=1.0,
        ),
        WorldEvent(
            category=WorldEventCategory.RESOURCE_DEPLETED,
            tick=6,
            region_id="test_region",
            subject="wood",
            severity=1.0,
        ),
        WorldEvent(
            category=WorldEventCategory.RESOURCE_DEPLETED,
            tick=7,
            region_id="test_region",
            subject="wood",
            severity=1.0,
        ),
    ]

    state = AuthoritativeState(
        tick=10,
        seed=0,
        regions={"test_region": region},
        recent_world_events=depletion_events,
    )

    _update, result = WorldEmergencePhase.execute(state, StateUpdate(), state.recent_world_events)

    # ScarcityModel must produce a signal for "wood" in "test_region"
    assert len(result.scarcity) >= 1, (
        "Expected ≥1 ResourceScarcitySignal after 3 RESOURCE_DEPLETED events, got none"
    )
    wood_signals = [s for s in result.scarcity if s.resource_type == "wood"]
    assert len(wood_signals) >= 1, (
        f"Expected scarcity signal for resource_type='wood', got: {result.scarcity}"
    )
    assert wood_signals[0].scarcity_level > 0.0, (
        f"Expected scarcity_level > 0 for wood, got {wood_signals[0].scarcity_level}"
    )

    # RegionalPressureModel must produce a resource pressure for "test_region"
    resource_pressures = [
        p for p in result.pressures
        if p.pressure_kind == "resource" and p.region_id == "test_region"
    ]
    assert len(resource_pressures) >= 1, (
        f"Expected resource RegionalPressure for 'test_region', got: {result.pressures}"
    )
    assert resource_pressures[0].intensity > 0.0, (
        f"Expected intensity > 0 for resource pressure, got {resource_pressures[0].intensity}"
    )
