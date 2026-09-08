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

Does NOT assert observed movement toward the target over further ticks. Investigated directly
and confirmed this is not a defect in this ticket's own fix: by the tick a raid becomes eligible
in a real multi-tick run, the adaptive governor's compute-budget watchdog has (in every
reproduction, instrumented or not) already entered RuntimeMode.DEGRADED with
PhaseBudgets.scan_policy=ScanPolicy.EXACT_DIRTY, and MovementCandidateSelector.select()'s own
code deliberately skips all non-urgent movement candidates under that policy ("under heavy
degraded mode, skip non-urgent moves entirely") -- a freshly spawned WANDER-mode raider with no
per-tick EntityUpdate has no urgency flag, and (per peer review) no path to ever BECOME urgent
without first being selected, so it is a genuine starvation loop, not mere throttling. This is a
newly-observed, more visible consequence of the already-known, deliberately-deferred Kernel
wall-clock mid-tick throttle determinism issue (same mechanism tests/integration/world/
test_long_run_stability.py already documents and CI-skips for) -- filed as its own ticket rather
than fixed here, per standing process: TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-
STARVATION. Confirmed (via direct phase-graph tracing) this is NOT the dirty-set passive-decay
gap TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION covers -- movement_routing's own
should_run_phase() check returns True unconditionally here (dirty_set is None at that point in
refine()'s sequence), so that gate never applies to this path.
"""
from __future__ import annotations

import dataclasses

from src.config.profiles import HardwareClass, RuntimeProfile
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

_SEED = 42
_WORLD_ID = "camp_maturity_calibration_pilot"
_CITY_POS = (25, 25)
_CAMP_ID = "calibration_goblin_camp"


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
    return Kernel(profile=profile, state=state, rng=rng, world_id=_WORLD_ID)


def test_camp_triggered_raid_spawns_real_raiders_anchored_and_targeted_correctly():
    kernel = _build_kernel()
    try:
        assert kernel._state.camps[_CAMP_ID].maturity == 79.9

        # Raid trigger needs maturity>=80 (fast, seeded near threshold) AND
        # tick - last_raid_tick >= 500 (camp.last_raid_tick starts at 0). Pre-seed last_raid_tick
        # far in the past so the cooldown gate is already satisfied at tick 0 -- this still
        # exercises the real Kernel loop, real pipeline, and real raid-composition logic; it only
        # avoids burning ~500 real ticks of unrelated simulation wall-clock time to reach a
        # precondition this test can construct directly, matching this repo's existing pattern of
        # constructing test preconditions via dataclasses.replace() rather than always simulating
        # up to them.
        camp = kernel._state.camps[_CAMP_ID]
        kernel._state = dataclasses.replace(
            kernel._state,
            camps={**kernel._state.camps, _CAMP_ID: dataclasses.replace(camp, last_raid_tick=-10_000)},
        )

        # world_dynamics (which calls CampService.process_camps) only runs on
        # tick % cadence.world_dynamics == 0 (default 50). The maturity-threshold check inside
        # process_camps() reads camp.maturity as of the START of that call (before that same
        # call's own growth delta is applied) -- so the tick-50 call still sees maturity=79.95
        # (just under threshold) and only applies the delta that crosses to 80.0; the raid check
        # itself only passes on the NEXT window (tick 100), which reads the now-80.0 value.
        for _ in range(105):
            kernel.tick_once()

        raiders_at_trigger = [
            e for e in kernel._state.entities.values() if e.kind == "goblin_raider"
        ]
        assert raiders_at_trigger, (
            "camp-triggered raid did not spawn any goblin_raider entities -- the discard bug "
            "this ticket fixes"
        )

        # Raiders must not spawn at the hardcoded world origin -- confirms real camp anchoring.
        for e in raiders_at_trigger:
            assert e.navigation.position != (0, 0)
            assert e.navigation.target == _CITY_POS, (
                f"raider {e.id} targets {e.navigation.target}, expected the real settlement "
                f"{_CITY_POS}, not a fabricated or hardcoded destination"
            )
    finally:
        kernel.shutdown()
