"""
tests/integration/campaigns/test_mid_episode_grief_trigger.py
────────────────────────────────────────────────────────────────────────────────
Integration tests for the mid-episode grief-urgency trigger
(TCK-20260824-GRIEF-NEMESIS-REACHABILITY, AC3, Steps 3/4/5/5b).

Forces a deterministic ally death mid-tick by injecting a WorkerResult with
EntityUpdate(active=False) at a chosen tick, via a wrapped executor — the same
production Kernel.tick_once() loop / _phase_resolution / _phase_advancement /
_phase_observability pipeline every other tick-time mutation goes through, exercised
directly (no mocking of Kernel internals themselves).
"""
from __future__ import annotations

from dataclasses import replace as dc_replace

import pytest

from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate
from src.core.work import WorkClass
from src.core.worker_protocol import ResultStatus, WorkerResult
from src.domains.campaigns.grief_urgency import GriefUrgencyImporter
from src.platform.rng import DeterministicRNG
from src.systems.world_systems.generator import EntityGenerator


@pytest.fixture(autouse=True, scope="module")
def _warmup_catalog():
    from src.engine.behavior_consumers import _auto_init
    _auto_init()


def _profile(name: str = "test-mid-episode-grief") -> RuntimeProfile:
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=1000,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=200.0,
    )


def _build_griever_and_ally(seed: int = 1):
    gen = EntityGenerator(seed)
    griever = gen.spawn_hero((10.0, 10.0))
    ally = gen.spawn_goblin((12.0, 12.0))
    griever = dc_replace(
        griever, social=dc_replace(griever.social, trust_history={ally.id: 0.9})
    )
    return griever, ally


def _wrap_executor_to_force_death(kernel, dead_entity_id: int, at_call: int) -> None:
    """Force dead_entity_id's lifecycle.active -> False on the at_call'th
    kernel._executor.execute() invocation (1-indexed, i.e. the at_call'th tick_once()).
    """
    real_execute = kernel._executor.execute
    call_count = {"n": 0}

    def _wrapped(work_items, state_view, rng, profile):
        call_count["n"] += 1
        results = list(real_execute(work_items, state_view, rng, profile))
        if call_count["n"] == at_call:
            results = [r for r in results if r.entity_id != dead_entity_id]
            results.append(WorkerResult(
                source_packet_id="local:forced_death",
                work_id="forced_death",
                entity_id=dead_entity_id,
                work_class=WorkClass.CRITICAL,
                update=EntityUpdate(entity_id=dead_entity_id, active=False),
                status=ResultStatus.SUCCESS,
            ))
        return results

    kernel._executor.execute = _wrapped


# ── AC3: mid-episode death applied one tick after detection, via ApplyPath ────


def test_mid_episode_entity_death_triggers_grief_concern_via_apply_path():
    from src.engine.kernel import Kernel

    griever, ally = _build_griever_and_ally(seed=11)
    state = AuthoritativeState(tick=0, seed=11, entities={griever.id: griever, ally.id: ally})
    rng = DeterministicRNG(11)
    kernel = Kernel(_profile(), state, rng, flags={"no_replay": True})
    try:
        _wrap_executor_to_force_death(kernel, ally.id, at_call=1)

        concern_id = f"grief_ally_{ally.id}"

        # Tick 1: death detected mid-tick, queued — NOT yet applied this tick.
        kernel.tick_once()
        assert concern_id not in kernel.state.entities[griever.id].strategic.concerns
        assert kernel._pending_grief_triggers == [
            (griever.id, ally.id, round(min(1.0, 0.9 * 0.8), 6))
        ]

        # Tick 2: _phase_resolution drains the queue and applies via StrategicPatch/ApplyPath.
        kernel.tick_once()
        concerns = kernel.state.entities[griever.id].strategic.concerns
        assert concern_id in concerns
        assert concerns[concern_id].urgency == pytest.approx(round(min(1.0, 0.9 * 0.8), 6))
        assert kernel._pending_grief_triggers == []

        # Architecture guard: the update flowed through the authoritative dirty-set
        # tracked ApplyPath, not a direct EntityState mutation — CLAUDE.md requires
        # verifying "authoritative application path was used".
        dirty_set = getattr(kernel._status, "dirty_set", None)
        assert dirty_set is not None
        assert griever.id in dirty_set.strategic_entities
    finally:
        kernel.shutdown()


def test_mid_episode_death_does_not_duplicate_episode_boundary_grief():
    """The mid-episode concern uses concern_id = f"grief_ally_{dead_ally_id}" — identical
    to the episode-boundary formula (grief_urgency.py) — so a later episode-boundary
    _advance_grief_urgencies() call for the same death is idempotent (overwrites by id via
    StrategicPatch's merge_dict()) rather than double-injecting a second, conflicting entry.
    """
    from src.engine.kernel import Kernel
    from src.domains.campaigns.state import GriefUrgencyModifier

    griever, ally = _build_griever_and_ally(seed=12)
    state = AuthoritativeState(tick=0, seed=12, entities={griever.id: griever, ally.id: ally})
    rng = DeterministicRNG(12)
    kernel = Kernel(_profile(), state, rng, flags={"no_replay": True})
    try:
        _wrap_executor_to_force_death(kernel, ally.id, at_call=1)
        kernel.tick_once()
        kernel.tick_once()  # mid-episode concern now applied

        concern_id = f"grief_ally_{ally.id}"
        mid_episode_concern = kernel.state.entities[griever.id].strategic.concerns[concern_id]

        # Simulate the episode-boundary path re-injecting for the same death (as
        # _build_initial_state() would at the start of the NEXT episode) — must overwrite,
        # not duplicate, the same concern_id.
        modifier = GriefUrgencyModifier(
            entity_id=griever.id, dead_ally_id=ally.id, episode=0, urgency=0.5,
        )
        re_injected = GriefUrgencyImporter.apply(kernel.state.entities[griever.id], modifier)

        assert len(re_injected.strategic.concerns) == len(
            kernel.state.entities[griever.id].strategic.concerns
        )
        assert re_injected.strategic.concerns[concern_id].urgency == pytest.approx(0.5)
        assert re_injected.strategic.concerns[concern_id].id == mid_episode_concern.id
    finally:
        kernel.shutdown()


# ── AC3 edge case: death on the episode's LAST tick (Step 5b) ─────────────────


def test_death_on_final_tick_still_applies_grief_concern_same_episode(monkeypatch):
    """A death detected on the episode's FINAL tick has no tick N+1 within that Kernel
    run to drain into via the normal _phase_resolution route — Step 5b's
    Kernel.drain_pending_triggers_at_teardown() (wired via
    ScenarioRuntimeService.flush_pending_grief_triggers()) closes that gap, applying the
    concern within the same episode's final_state instead of waiting for a next episode.
    """
    import src.engine.kernel as kernel_mod
    from src.engine.scenario_runtime import ScenarioRuntimeService

    griever, ally = _build_griever_and_ally(seed=13)
    initial_state = AuthoritativeState(
        tick=0, seed=13, entities={griever.id: griever, ally.id: ally}
    )

    tick_limit = 3
    real_kernel_cls = kernel_mod.Kernel

    class _DeathInjectingKernel(real_kernel_cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Force the death on the LAST tick of the run (tick_limit'th tick_once() call).
            _wrap_executor_to_force_death(self, ally.id, at_call=tick_limit)

    monkeypatch.setattr(kernel_mod, "Kernel", _DeathInjectingKernel)

    from src.scenarios.schema import SimulationScenarioDefinition
    spec = SimulationScenarioDefinition(
        id="final_tick_death_ep",
        world_composition="frontier_living_world",
        perspective="hero_guild_perspective",
        victory_conditions=[{"kind": "tick_limit", "value": tick_limit}],
    )

    svc = ScenarioRuntimeService(spec, initial_state=initial_state)
    try:
        svc.start()
        assert svc.tick == tick_limit  # confirms no tick N+1 ran within this Kernel

        concern_id = f"grief_ally_{ally.id}"
        # Before the flush: the death was detected on the final tick but not yet applied.
        assert concern_id not in svc.final_state.entities[griever.id].strategic.concerns
        assert svc._kernel._pending_grief_triggers != []

        svc.flush_pending_grief_triggers()

        final = svc.final_state
        concerns = final.entities[griever.id].strategic.concerns
        assert concern_id in concerns, (
            "Step 5b must apply the final-tick grief trigger within this same episode's "
            "final_state, not defer it to a next episode"
        )
        assert concerns[concern_id].urgency == pytest.approx(round(min(1.0, 0.9 * 0.8), 6))
        assert svc._kernel._pending_grief_triggers == []
        # Same-episode, not a disguised extra tick: tick/world_time must be unchanged.
        assert svc.tick == tick_limit
        assert final.tick == tick_limit
    finally:
        svc.abort()
