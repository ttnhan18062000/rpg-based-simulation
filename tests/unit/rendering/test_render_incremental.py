"""DirtySet-incremental render vs. full re-render pixel-identity.

TCK-20260821-WORLD-RENDER-CORE AC: "DirtySet-incremental render produces
pixel-identical output to a full re-render of the same state." Ticks a real,
compiled Kernel forward, applying IncrementalRenderer.update() per tick using
dirty_entity_ids_for_render (which mirrors src/core/dirty.py's own
get_relevant_entity_ids fallback convention), then compares the resulting frame
against a full, non-incremental render() of the same final state.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from src.config.profiles import HardwareClass, RuntimeProfile
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.rendering.incremental import IncrementalRenderer, dirty_entity_ids_for_render
from src.rendering.render import render
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

_SCALE = 2
_N_TICKS = 15
_SEED = 42
_WORLD_ID = "sandbox_world"


def _build_kernel() -> Kernel:
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(_WORLD_ID)
    state, _report = WorldCompiler.compile(spec, seed=_SEED)

    profile = RuntimeProfile(
        name="RENDER_INCREMENTAL_TEST",
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


def test_dirty_set_incremental_render_pixel_identical_to_full_rerender(tmp_path):
    kernel = _build_kernel()
    try:
        renderer = IncrementalRenderer(kernel._state, scale=_SCALE)
        all_entity_ids = set(kernel._state.entities.keys())

        saw_nonempty_dirty_set = False
        for _ in range(_N_TICKS):
            kernel.tick_once()
            dirty_ids = dirty_entity_ids_for_render(kernel._status, all_entity_ids)
            if dirty_ids:
                saw_nonempty_dirty_set = True
            renderer.update(kernel._state, dirty_ids)

        # Sanity check that this scenario actually exercises the DirtySet-filtered
        # path (not merely a trivial all-static run) — sandbox_world at seed 42 has
        # entities that move over these ticks.
        assert saw_nonempty_dirty_set, (
            "scenario produced no dirty entities across all ticks — this test would "
            "not actually exercise the DirtySet-incremental update path"
        )

        incremental_path = str(tmp_path / "incremental_final.png")
        renderer.save(incremental_path)

        full_path = str(tmp_path / "full_final.png")
        render(kernel._state, full_path, scale=_SCALE)
    finally:
        kernel.shutdown()

    incremental_hash = hashlib.sha256(Path(incremental_path).read_bytes()).hexdigest()
    full_hash = hashlib.sha256(Path(full_path).read_bytes()).hexdigest()

    assert incremental_hash == full_hash, (
        "DirtySet-incremental render diverged from a full non-incremental re-render "
        "of the same final state"
    )
