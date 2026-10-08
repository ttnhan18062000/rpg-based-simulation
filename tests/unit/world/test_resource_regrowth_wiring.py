"""TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE (Bible 03 §3.1, TOWN-137):
the regeneration the Resource Ecology Service computes reaches the world through the real tick path, not only the service."""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.core.state import AuthoritativeState, RegionState, ResourceNodeState
from src.core.updates import StateUpdate
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.platform.rng import DeterministicRNG
from src.world.ecology import ResourceEcologyService

NODE_ID = 7
INTERVAL = ResourceEcologyService.ECOLOGY_INTERVAL


class _PinnedNormalGovernor(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        return None


def _state(tick: int, charges: int, regen: int = 1, cooldown: int = 0) -> AuthoritativeState:
    node = ResourceNodeState(
        id=NODE_ID, kind="herb_patch", position=(5.0, 5.0), yields_item="herb", remaining_charges=charges, max_charges=5,
        required_ticks=1, regen_rate_per_tick=regen, cooldown_remaining=cooldown)
    region = RegionState(id="r", name="R", bounds=(0, 0, 10, 10))
    return AuthoritativeState(tick=tick, seed=42, resource_nodes={NODE_ID: node}, regions={"r": region})


def test_the_refined_update_carries_the_regen_and_the_recovered_event():
    refined = AuthoritativeApplyPipeline.refine(_state(INTERVAL, charges=0), StateUpdate())
    assert refined.node_updates[NODE_ID].charges_delta == 1
    assert [e.subject for e in refined.world_events_add if e.category == WorldEventCategory.RESOURCE_RECOVERED] == [str(NODE_ID)]


def test_a_node_that_is_not_depleted_regrows_without_a_recovered_event():
    refined = AuthoritativeApplyPipeline.refine(_state(INTERVAL, charges=2), StateUpdate())
    assert refined.node_updates[NODE_ID].charges_delta == 1
    assert not [e for e in refined.world_events_add if e.category == WorldEventCategory.RESOURCE_RECOVERED]


def test_no_regen_off_the_ecology_interval_for_a_static_node_or_a_node_on_cooldown():
    assert NODE_ID not in AuthoritativeApplyPipeline.refine(_state(INTERVAL + 50, charges=0), StateUpdate()).node_updates
    assert NODE_ID not in AuthoritativeApplyPipeline.refine(_state(INTERVAL, charges=0, regen=0), StateUpdate()).node_updates
    on_cooldown = AuthoritativeApplyPipeline.refine(_state(INTERVAL, charges=0, cooldown=3), StateUpdate()).node_updates[NODE_ID]
    assert on_cooldown.charges_delta == 0  # the cooldown counts down; no charge returns until it ends


def test_a_depleted_node_gains_charges_over_the_ecology_interval_through_the_real_tick_path():
    kernel = Kernel(
        profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=_state(INTERVAL - 2, charges=0), rng=DeterministicRNG(42),
        governor=_PinnedNormalGovernor(), flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    try:
        for _ in range(4):
            kernel.tick_once()
        assert kernel.state.tick > INTERVAL
        assert kernel.state.resource_nodes[NODE_ID].remaining_charges == 1
    finally:
        kernel.shutdown()
