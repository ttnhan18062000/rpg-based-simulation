"""The observability mode never changes the authoritative state (TCK-20261021-OBSERVABILITY-DETERMINISM-TEST-NEVER-HASHES).

The same world and seed run through the pinned gate kernel (``build_kernel``: pinned governor, sequential executor, audit mode) under OFF and under FULL; the final
authoritative state hash must be identical. A second test proves the comparison has teeth: a FULL run whose "observability" writes authoritative state gets a different hash.
The test used to flip ``ObservabilityConfig`` and assert ``get_mode()`` only; it never ran a kernel and never hashed.
"""
from __future__ import annotations

import functools
import os
import shutil
from dataclasses import replace

from src.engine.checkpoint import CanonicalStateHasher
from src.observability.config import ObservabilityConfig, ObservabilityMode
from tools.test_architecture.rpg_gate_run import build_kernel

WORLD, SEED, TICKS = "frontier_living_world", 42, 100


@functools.lru_cache(maxsize=None)
def _run(mode: ObservabilityMode, writes_authoritative_state: bool = False) -> tuple[str, bool]:
    """``(final canonical state hash, whether the run wrote simulation_events.jsonl)`` for ``TICKS`` ticks of WORLD/SEED under ``mode``.

    ``writes_authoritative_state`` models an observability path that mutates the authoritative state (it advances the state's tick after every tick); only the mutation check sets it.
    """
    run_id = f"obsdet-{mode.value.lower()}-{os.getpid()}{'-mut' if writes_authoritative_state else ''}"
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


def test_observability_off_and_full_have_same_authoritative_hash():
    off_hash, off_wrote = _run(ObservabilityMode.OFF)
    full_hash, full_wrote = _run(ObservabilityMode.FULL)
    assert full_wrote and not off_wrote, "the two modes must really differ in what they record, or the comparison proves nothing"
    assert full_hash == off_hash


def test_the_comparison_catches_an_observability_mode_that_writes_authoritative_state():
    off_hash, _ = _run(ObservabilityMode.OFF)
    mutated_hash, _ = _run(ObservabilityMode.FULL, writes_authoritative_state=True)
    assert mutated_hash != off_hash
