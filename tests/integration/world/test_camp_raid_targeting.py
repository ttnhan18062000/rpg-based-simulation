"""
tests/integration/world/test_camp_raid_targeting.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX

Proves the camp-triggered raid actually spawns real raiders, anchored at the camp (not the
hardcoded world origin), targeting the nearest real settlement -- not just that
navigation.target was assigned somewhere, and not the pre-fix discard bug where computed
raiders never reached entities_add at all. Uses camp_maturity_calibration_pilot (built for
TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE): a CAMP seeded at maturity=79.9 crosses the 80.0
raid threshold within a few ticks, and the world has a real CITY place ("hometown_city",
position (25,25)) far from the CAMP ("calibration_goblin_camp", position (160,160)) to target.

Historically did NOT assert observed movement toward the target over further ticks. By the tick a
raid becomes eligible in a real multi-tick run, the adaptive governor's compute-budget watchdog
has (in every reproduction, instrumented or not) already entered RuntimeMode.DEGRADED with
PhaseBudgets.scan_policy=ScanPolicy.EXACT_DIRTY, and MovementCandidateSelector.select() used to
skip all non-urgent movement candidates under that policy unconditionally -- a freshly spawned
WANDER-mode raider with no per-tick EntityUpdate has no urgency flag, and (per peer review) had no
path to ever BECOME urgent without first being selected, so it was a genuine starvation loop, not
mere throttling. This was a newly-observed, more visible consequence of the already-known,
deliberately-deferred Kernel wall-clock mid-tick throttle determinism issue (same mechanism
tests/integration/world/test_long_run_stability.py already documents and CI-skips for) -- fixed
under TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION with a reduced-cadence admission
for entities with a real, unreached target and no other urgency signal
(MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO), so raiders now eventually move
even under sustained real DEGRADED pressure -- this test now asserts that directly. Confirmed (via
direct phase-graph tracing) this is NOT the dirty-set passive-decay gap
TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION covers -- movement_routing's own
should_run_phase() check returns True unconditionally here (dirty_set is None at that point in
refine()'s sequence), so that gate never applies to this path.
"""
from __future__ import annotations

import dataclasses

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import RuntimeMode
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

_SEED = 42
_WORLD_ID = "camp_maturity_calibration_pilot"
_CITY_POS = (25, 25)
_CAMP_ID = "calibration_goblin_camp"


class _DegradedGovernor(ResourceGovernor):
    """Holds the governor's indicated mode at DEGRADED.

    This test covers the non-urgent-movement starvation that DEGRADED's EXACT_DIRTY scan policy caused
    (TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION). It used to reach DEGRADED by accident,
    through the kernel's wall-clock tick-budget throttle; that throttle now only reports
    (TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY), so under NORMAL the test would pass without
    covering that path. The mode is driven through the governor instead, and asserted below.
    """

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.DEGRADED


def _build_kernel() -> Kernel:
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(_WORLD_ID)
    state, _report = WorldCompiler.compile(spec, seed=_SEED)

    profile = RuntimeProfile(
        name="CAMP_RAID_TARGETING_TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=90.0,
        max_worker_count=0,
        max_tick_budget_ms=200.0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
    )
    rng = DeterministicRNG(_SEED)
    return Kernel(profile=profile, state=state, rng=rng, world_id=_WORLD_ID, governor=_DegradedGovernor())


def test_a_matured_camp_raids_nothing_in_a_real_run():
    """D70 (TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70): the camp raid is retired. The same real run that used to conjure
    goblin_raider entities (a camp crossing the 80.0 raid threshold with its cooldown already satisfied) now adds no entity at all, charges the
    camp no raid cost, and leaves its raid clock alone; the camp only matures.

    The DEGRADED non-urgent-movement starvation fix this file used to cover through those raiders
    (TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION) keeps its own unit coverage in
    tests/unit/domains/optimization/test_movement_candidate_selector.py.
    """
    kernel = _build_kernel()
    try:
        assert kernel._state.camps[_CAMP_ID].maturity == 79.9
        camp = kernel._state.camps[_CAMP_ID]
        kernel._state = dataclasses.replace(
            kernel._state,
            camps={**kernel._state.camps, _CAMP_ID: dataclasses.replace(camp, last_raid_tick=-10_000)},
        )
        ids_before = set(kernel._state.entities)

        for _ in range(105):
            kernel.tick_once()

        after = kernel._state.camps[_CAMP_ID]
        assert after.maturity >= 80.0, "the camp must cross the old raid threshold for this test to mean anything"
        assert after.last_raid_tick == -10_000, "no raid happened, so the raid clock is untouched"
        assert not [e for e in kernel._state.entities.values() if e.kind == "goblin_raider"]
        assert not [e for e in kernel._state.entities.values() if e.id not in ids_before and e.kind.startswith("goblin")]
    finally:
        kernel.shutdown()
