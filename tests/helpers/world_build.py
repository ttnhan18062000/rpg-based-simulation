"""Compile a world the way the gate compiles it (TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT).

``WorldCompiler.compile(spec, seed)`` with no content context builds a world whose bodies have no starting purse, inventory or catalog roles. The rpg gate
(`tools/test_architecture/rpg_gate_run.build_kernel`) loads the spec WITH its context; a test that measures a world must do the same, through this one helper.
"""
from __future__ import annotations

import os
from typing import Any, Tuple


def compile_world_with_context(world_id: str, seed: int, root: str = os.path.join("data", "worlds")) -> Tuple[Any, Any]:
    """Return (state, report) for ``world_id`` compiled for ``seed`` with the world's content context."""
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, context = WorldRepository(root).load_world_with_context(world_id)
    return WorldCompiler.compile(spec, seed, context=context)
