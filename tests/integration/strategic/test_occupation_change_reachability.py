"""
Integration test for TCK-20260824-OCCUPATION-CHANGE-TRIGGER, plan.md Step 8 / test_plan.md test
8 (test_occupation_change_reachable_through_real_kernel_tick_once).

Proves AC1: a real Kernel.tick_once() loop, with no test-side scoring/dispatch shortcuts, takes a
CITIZEN entity all the way through OccupationChangeGoalScorer -> tier-5 materialization ->
TacticalDecisionSystem navigation -> ObjectiveIntentResolver -> ActionIntentAdapter -> the
authoritative IdentityPatch.apply path, ending with entity.identity.role changed to a real
destination role.

Uses a small hand-built world (mirrors test_hunger_satiation.py's own pattern) rather than
sandbox_world: a lone CITIZEN entity in a region with no competing SHOPKEEPER/WORKER/GUARD
headcount is a deterministic, reliably-reachable scenario, unlike sandbox_world's variable
population/terrain (which the sibling test_recipe_learned_fires_through_real_kernel_tick_once
documents as not force-reachable within a fixed budget for that reason).
"""
from __future__ import annotations

from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import AuthoritativeState, RegionState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

_TEST_PROFILE = RuntimeProfile(
    name="occupation-change-test",
    hardware_class=HardwareClass.CLASS_B,
    max_ram_mb=512,
    max_cpu_percent=100.0,
    max_worker_count=1,
    max_queue_depth=500,
    max_replay_buffer_kb=0,
    max_observability_budget_percent=0.0,
    max_tick_budget_ms=500.0,
)


def _state_with_lone_citizen(seed: int = 42) -> AuthoritativeState:
    entity = (
        V2EntityBuilder(1)
        .kind("citizen")
        .location(5.0, 5.0)
        .identity(role=EntityRole.CITIZEN)
        .combat(readiness=100.0)
        .build()
    )
    # kind="TOWN" (not the RegionState default "FOREST") is load-bearing, not decorative:
    # SpawnService.process_spawns (src/world/spawn.py:65) looks up SPAWN_POOLS[region.kind] and
    # only spawns wildlife for a region kind present in that dict ("FOREST"/"PLAINS"/"MOUNTAIN",
    # src/world/spawn_config.py:33-36) -- "TOWN" resolves to an empty pool, so no monster spawns
    # into this region during the tick loop below. Left at the default "FOREST", tick 0's spawn
    # check (SPAWN_INTERVAL=50, and tick 0 % 50 == 0) seeds a MONSTER that wanders into aggro
    # range of the citizen around tick ~19-20 (exactly when it reaches the region center) and its
    # tactical INTERCEPT response permanently preempts the CHANGE_OCCUPATION objective's
    # navigation, so the transition never completes within a bounded tick budget -- confirmed via
    # direct reproduction during TCK-20260824-OCCUPATION-CHANGE-TRIGGER's own Test phase. A citizen
    # taking an open civilian job is a town-region scenario in the first place, so "TOWN" is also
    # the semantically correct kind, not just a monster-suppression workaround.
    region = RegionState(id="town", name="Town", bounds=(0, 0, 20, 20), kind="TOWN")
    return AuthoritativeState(
        tick=0, seed=seed, world_time=0,
        entities={1: entity}, regions={"town": region},
    )


def test_occupation_change_reachable_through_real_kernel_tick_once():
    kernel = Kernel(
        _TEST_PROFILE, _state_with_lone_citizen(), DeterministicRNG(42),
        flags={"no_frame_pacing": True, "no_replay": True},
    )

    final_role = None
    try:
        for _ in range(200):
            kernel.tick_once()
            ent = kernel.state.entities.get(1)
            if ent is not None and ent.identity.role != EntityRole.CITIZEN:
                final_role = ent.identity.role
                break
    finally:
        kernel.shutdown()

    assert final_role is not None, "entity.identity.role never transitioned off CITIZEN in 200 ticks"
    assert final_role in (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)
