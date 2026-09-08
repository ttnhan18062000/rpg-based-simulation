"""DirtySet-incremental render vs. full re-render pixel-identity.

TCK-20260821-WORLD-RENDER-CORE AC: "DirtySet-incremental render produces
pixel-identical output to a full re-render of the same state." Ticks a real,
compiled Kernel forward, applying IncrementalRenderer.update() per tick using
dirty_entity_ids_for_render (which mirrors src/core/dirty.py's own
get_relevant_entity_ids fallback convention), then compares the resulting frame
against a full, non-incremental render() of the same final state.
"""
from __future__ import annotations

import dataclasses
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


def test_incremental_render_repaints_entity_that_dies_in_place(tmp_path):
    """TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP regression guard.

    Kills one entity in place (position unchanged, combat.alive flips False,
    lifecycle.active stays True -- e.g. a corpse) and asserts the incremental
    renderer's next update() call repaints it ENTITY_COLOR_DEAD, matching a
    full non-incremental render() of the same post-death state.
    """
    kernel = _build_kernel()
    try:
        renderer = IncrementalRenderer(kernel._state, scale=_SCALE)
        all_entity_ids = set(kernel._state.entities.keys())

        for _ in range(5):
            kernel.tick_once()
            dirty_ids = dirty_entity_ids_for_render(kernel._status, all_entity_ids)
            renderer.update(kernel._state, dirty_ids)

        eid = next(
            e_id for e_id, ent in kernel._state.entities.items()
            if getattr(ent.lifecycle, "active", True) and ent.combat.alive
        )
        entity = kernel._state.entities[eid]
        prior_position = entity.navigation.position

        dead_combat = dataclasses.replace(entity.combat, alive=False)
        dead_entity = dataclasses.replace(entity, combat=dead_combat)
        died_entities = dict(kernel._state.entities)
        died_entities[eid] = dead_entity
        died_state = dataclasses.replace(kernel._state, entities=died_entities)

        assert dead_entity.navigation.position == prior_position, (
            "test setup must kill the entity in place -- position must not change"
        )
        assert getattr(dead_entity.lifecycle, "active", True), (
            "test setup must leave lifecycle.active True -- this is the exact "
            "in-place-death scenario the gap only reproduces under"
        )

        renderer.update(died_state, {eid})

        incremental_path = str(tmp_path / "incremental_death.png")
        renderer.save(incremental_path)

        full_path = str(tmp_path / "full_death.png")
        render(died_state, full_path, scale=_SCALE)
    finally:
        kernel.shutdown()

    incremental_hash = hashlib.sha256(Path(incremental_path).read_bytes()).hexdigest()
    full_hash = hashlib.sha256(Path(full_path).read_bytes()).hexdigest()

    assert incremental_hash == full_hash, (
        "IncrementalRenderer did not repaint an entity that died in place to "
        "ENTITY_COLOR_DEAD, diverging from a full non-incremental re-render of "
        "the same post-death state"
    )


def test_incremental_render_restores_background_when_entity_deactivates_off_dirty_set(tmp_path):
    """TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP regression guard.

    An entity that deactivates (lifecycle.active True -> False) purely via passive
    decay carries no EntityUpdate that tick, so dirty_entity_ids_for_render() never
    returns it -- the published dirty_set is finalized before that apply-time-only
    mutation runs (src/engine/pipeline.py, src/engine/apply.py). Simulates that exact
    gap directly: the entity is flipped to fully inactive in the state passed to
    update(), but its id is deliberately withheld from dirty_entity_ids (empty set),
    matching what the real pipeline actually hands the renderer for such a tick.
    Asserts the renderer still restores the background cell rather than leaving a
    stale alive/dead-colored pixel.
    """
    kernel = _build_kernel()
    try:
        renderer = IncrementalRenderer(kernel._state, scale=_SCALE)
        all_entity_ids = set(kernel._state.entities.keys())

        for _ in range(5):
            kernel.tick_once()
            dirty_ids = dirty_entity_ids_for_render(kernel._status, all_entity_ids)
            renderer.update(kernel._state, dirty_ids)

        eid = next(
            e_id for e_id, ent in kernel._state.entities.items()
            if getattr(ent.lifecycle, "active", True) and ent.combat.alive
        )
        entity = kernel._state.entities[eid]
        assert eid in renderer.last_entity_pos, (
            "test setup must pick an entity the renderer has already drawn, "
            "otherwise there is no stale pixel for this gap to leave behind"
        )

        dead_lifecycle = dataclasses.replace(entity.lifecycle, active=False)
        dead_entity = dataclasses.replace(entity, lifecycle=dead_lifecycle)
        died_entities = dict(kernel._state.entities)
        died_entities[eid] = dead_entity
        died_state = dataclasses.replace(kernel._state, entities=died_entities)

        # The core reproduction: eid is deliberately absent from dirty_entity_ids,
        # matching the real gap -- a passive-decay-only deactivation never appears
        # in the published dirty_set.
        renderer.update(died_state, set())

        assert eid not in renderer.last_entity_pos, (
            "renderer must stop tracking an entity once it is confirmed inactive, "
            "even when its id never appeared in dirty_entity_ids"
        )

        incremental_path = str(tmp_path / "incremental_deactivate.png")
        renderer.save(incremental_path)

        full_path = str(tmp_path / "full_deactivate.png")
        render(died_state, full_path, scale=_SCALE)
    finally:
        kernel.shutdown()

    incremental_hash = hashlib.sha256(Path(incremental_path).read_bytes()).hexdigest()
    full_hash = hashlib.sha256(Path(full_path).read_bytes()).hexdigest()

    assert incremental_hash == full_hash, (
        "IncrementalRenderer left a stale pixel for an entity that deactivated "
        "without ever appearing in dirty_entity_ids, diverging from a full "
        "non-incremental re-render of the same post-deactivation state"
    )
