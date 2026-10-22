"""The shared world-build helper builds the same tick-0 world as the gate's kernel builder, and that world has its purses
(TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT)."""
from __future__ import annotations

import shutil
from pathlib import Path

from tests.helpers.world_build import compile_world_with_context

WORLD, SEED = "urban_political", 42


def test_the_helper_compiles_the_same_tick_zero_world_as_the_gate_and_the_bodies_hold_coin():
    from src.engine.checkpoint import CanonicalStateHasher
    from tools.test_architecture.rpg_gate_run import build_kernel

    state, _ = compile_world_with_context(WORLD, SEED)
    assert sum(e.inventory.gold for e in state.entities.values()) > 0
    run_id = "world_build_helper_vs_gate"
    kernel = build_kernel(WORLD, SEED, run_id)
    try:
        assert CanonicalStateHasher.get_hash(state) == CanonicalStateHasher.get_hash(kernel.state)
    finally:
        kernel.shutdown()
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def test_a_context_less_compile_is_what_the_helper_exists_to_avoid():
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec = WorldRepository("data/worlds").load_world(WORLD)
    bare, _ = WorldCompiler.compile(spec, seed=SEED)
    assert sum(e.inventory.gold for e in bare.entities.values()) == 0
