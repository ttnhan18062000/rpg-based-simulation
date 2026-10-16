"""Unit tests for Kernel._drain_pending_grief_triggers() and
Kernel.drain_pending_triggers_at_teardown() (TCK-20260824-GRIEF-NEMESIS-REACHABILITY,
Steps 3/5/5b; the owed triggers are read from state, decision 80).

drain_pending_triggers_at_teardown() is a one-shot resolution+apply flush for a death
detected on a Kernel run's FINAL tick, which _phase_resolution never gets a tick N+1 to
drain into — reuses the same AuthoritativeApplyPipeline.refine() + ApplyPath.
apply_generation() commit route as a normal tick, but must NOT advance tick/world_time
and must be a true no-op (no state rebuild) when no trigger is owed, and a second flush finds nothing (the `grief_drained_tick` watermark).
"""
from __future__ import annotations

import pytest

from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from dataclasses import replace

from src.core.death_cause import DeathCause, DeathRecord
from src.core.grief_triggers import pending_grief_triggers
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


def _profile(name: str = "test-grief-drain") -> RuntimeProfile:
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


def _make_kernel(entities=None, tick: int = 5, world_time: int = 500, seed: int = 1) -> Kernel:
    state = AuthoritativeState(tick=tick, seed=seed, world_time=world_time, entities=entities or {})
    rng = DeterministicRNG(seed)
    return Kernel(_profile(), state, rng, flags={"no_replay": True})


def _griever(entity_id: int = 1, ally_id: int = 99, trust: float = 0.75):
    e = V2EntityBuilder(entity_id).kind("worker").location(0.0, 0.0).combat(hp=80, max_hp=80).build()
    return replace(e, social=replace(e.social, trust_history={ally_id: trust}))


def _dead_ally(ally_id: int = 99, death_tick: int = 4):
    e = V2EntityBuilder(ally_id).kind("worker").location(1.0, 0.0).build()
    return replace(e, lifecycle=replace(e.lifecycle, active=False, death_record=DeathRecord(cause=DeathCause.COMBAT, tick=death_tick)))


def _kernel_with_owed_trigger(tick: int = 5, world_time: int = 500, ally_id: int = 99) -> Kernel:
    """A kernel whose state owes one grief trigger: the ally died on tick `tick - 1`."""
    return _make_kernel(entities={1: _griever(1, ally_id), ally_id: _dead_ally(ally_id, tick - 1)}, tick=tick, world_time=world_time)


class TestDrainPendingTriggersAtTeardownNoop:
    def test_noop_when_empty(self, monkeypatch):
        kernel = _make_kernel()
        try:
            assert pending_grief_triggers(kernel.state) == []
            prior_state = kernel.state

            from src.engine.pipeline import AuthoritativeApplyPipeline
            from src.engine.apply import ApplyPath

            refine_called = []
            apply_called = []
            monkeypatch.setattr(
                AuthoritativeApplyPipeline, "refine",
                staticmethod(lambda *a, **k: refine_called.append(True)),
            )
            monkeypatch.setattr(
                ApplyPath, "apply_generation",
                staticmethod(lambda *a, **k: apply_called.append(True)),
            )

            kernel.drain_pending_triggers_at_teardown()

            assert kernel.state is prior_state, "no-op must not rebuild state"
            assert refine_called == []
            assert apply_called == []
        finally:
            kernel.shutdown()


class TestDrainPendingTriggersAtTeardownNonEmpty:
    def test_applies_grief_concern_and_advances_the_watermark(self):
        kernel = _kernel_with_owed_trigger(ally_id=99)
        try:
            assert pending_grief_triggers(kernel.state) != []

            kernel.drain_pending_triggers_at_teardown()

            assert pending_grief_triggers(kernel.state) == []
            assert kernel.state.grief_drained_tick == 4
            concerns = kernel.state.entities[1].strategic.concerns
            assert "grief_ally_99" in concerns
            assert concerns["grief_ally_99"].urgency == pytest.approx(round(min(1.0, 0.75 * 0.8), 6))
        finally:
            kernel.shutdown()

    def test_does_not_advance_tick_or_world_time(self):
        kernel = _kernel_with_owed_trigger(tick=7, world_time=777)
        try:
            kernel.drain_pending_triggers_at_teardown()

            assert kernel.state.tick == 7
            assert kernel.state.world_time == 777
        finally:
            kernel.shutdown()

    def test_replaces_state_object_when_nonempty(self):
        """Unlike the no-op case, a real drain reassigns self._state to a new object
        (via ApplyPath.apply_generation), since StrategicPatch application replaces the
        entity and therefore the entities dict."""
        kernel = _kernel_with_owed_trigger()
        try:
            prior_state = kernel.state

            kernel.drain_pending_triggers_at_teardown()

            assert kernel.state is not prior_state
        finally:
            kernel.shutdown()

    def test_a_second_flush_finds_nothing(self):
        """The watermark makes the flush idempotent: the trigger fires exactly once."""
        kernel = _kernel_with_owed_trigger()
        try:
            kernel.drain_pending_triggers_at_teardown()
            after_first = kernel.state

            kernel.drain_pending_triggers_at_teardown()

            assert kernel.state is after_first
        finally:
            kernel.shutdown()
