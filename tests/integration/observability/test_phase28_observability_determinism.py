"""The observability mode never changes the authoritative state (TCK-20261021-OBSERVABILITY-DETERMINISM-TEST-NEVER-HASHES).

The same world and seed run through the pinned gate kernel (``build_kernel``: pinned governor, sequential executor, audit mode) under OFF and under FULL; the final
authoritative state hash must be identical. Two more tests prove the comparison has teeth: a FULL run whose observability phase writes one authoritative field (an entity's hp) gets a different hash, and so does one whose
state tick is advanced after each tick.

What the hash covers (``CanonicalStateHasher.to_canonical_data``): the authoritative partition only (tick, seed, world_time and the other scalars, entities, regions, places, scars, nodes,
buildings, corpses, ground items, chests, groups, storage, camps, global resources, tiles, rng checkpoint and the bridge fields). Observability-only data (the event recorder's buffers and files,
SimQ scores, run ledgers) is outside it by design, so it can differ between OFF and FULL without failing this test.
The test used to flip ``ObservabilityConfig`` and assert ``get_mode()`` only; it never ran a kernel and never hashed.
"""
from __future__ import annotations

import functools
import os
import shutil
from dataclasses import replace

from src.engine.checkpoint import CanonicalStateHasher
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.engine.kernel import Kernel
from tools.test_architecture.rpg_gate_run import build_kernel

_REAL_OBSERVABILITY_PHASE = Kernel._phase_observability  # captured at import, before any case injects a fault
WORLD, SEED, TICKS = "frontier_living_world", 42, 100


def _observability_phase_that_writes_hp(real_phase):
    """The kernel's observability phase with one injected fault: after it runs (it returns at once under OFF), it also bumps the hp of the lowest-id entity in the authoritative state.
    The fault sits at the observability boundary of the test only; no production code has such a switch."""
    def phase(self, prior_state, update):
        real_phase(self, prior_state, update)
        if ObservabilityConfig.get_mode() is ObservabilityMode.OFF:
            return
        eid = min(self._state.entities)
        entity = self._state.entities[eid]
        bumped = replace(entity, combat=replace(entity.combat, hp=entity.combat.hp + 1))
        self._state = replace(self._state, entities={**self._state.entities, eid: bumped})
    return phase


def _execute(mode: ObservabilityMode, tag: str = "", writes_authoritative_state: bool = False) -> tuple[str, bool]:
    """``(final canonical state hash, whether the run wrote simulation_events.jsonl)`` for ``TICKS`` ticks of WORLD/SEED under ``mode``.

    ``writes_authoritative_state`` models an observability path that mutates the authoritative state (it advances the state's tick after every tick); only the coarse self-test sets it.
    """
    run_id = f"obsdet-{mode.value.lower()}-{os.getpid()}{tag}"
    original = ObservabilityConfig.get_mode()
    ObservabilityConfig.set_override_mode(mode)
    kernel = build_kernel(WORLD, SEED, run_id)
    try:
        for _ in range(TICKS):
            kernel.tick_once()
            if writes_authoritative_state:
                kernel._state = replace(kernel._state, tick=kernel._state.tick + 1)
        final = CanonicalStateHasher.get_hash(kernel._state)
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(original)
        wrote_events = os.path.exists(os.path.join("data", "runs", run_id, "simulation_events.jsonl"))
        shutil.rmtree(os.path.join("data", "runs", run_id), ignore_errors=True)
    return final, wrote_events


@functools.lru_cache(maxsize=None)
def _clean_run(mode: ObservabilityMode) -> tuple[str, bool]:
    """The unfaulted run per mode, computed once per process; the faulted cases never touch this cache."""
    return _execute(mode)


def test_observability_off_and_full_have_same_authoritative_hash():
    off_hash, off_wrote = _clean_run(ObservabilityMode.OFF)
    full_hash, full_wrote = _clean_run(ObservabilityMode.FULL)
    assert full_wrote and not off_wrote, "the two modes must really differ in what they record, or the comparison proves nothing"
    assert full_hash == off_hash


def test_the_comparison_catches_an_observability_phase_that_writes_an_entitys_hp(monkeypatch):
    off_hash, _ = _clean_run(ObservabilityMode.OFF)
    full_hash, _ = _clean_run(ObservabilityMode.FULL)
    # scoped by the fixture: undone at the end of this test, so no other case (or xdist worker test) sees the fault
    monkeypatch.setattr(Kernel, "_phase_observability", _observability_phase_that_writes_hp(Kernel._phase_observability))
    faulty_hash, _ = _execute(ObservabilityMode.FULL, tag="-hp")
    assert faulty_hash != full_hash and faulty_hash != off_hash


def test_the_comparison_catches_a_state_tick_advanced_after_each_tick():
    """Kept as a separate, coarser self-test: it does not go through any observability code."""
    off_hash, _ = _clean_run(ObservabilityMode.OFF)
    mutated_hash, _ = _execute(ObservabilityMode.FULL, tag="-tick", writes_authoritative_state=True)
    assert mutated_hash != off_hash


def test_no_injected_fault_outlives_its_case():
    """Run after the faulted case in file order: the fixture must have restored the real phase."""
    assert Kernel._phase_observability is _REAL_OBSERVABILITY_PHASE
