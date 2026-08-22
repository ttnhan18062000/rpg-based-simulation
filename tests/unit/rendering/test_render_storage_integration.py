"""render_output_path() + render() writing under data/runs/{run_id}/renders/.

TCK-20260821-WORLD-RENDER-CORE. Never writes into the real data/runs/ — uses a
tmp_path-scoped fake base_dir, same mocking spirit as
tests/unit/observability/test_retention_manager.py.
"""
from __future__ import annotations

import os

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.rendering.render import render, render_output_path


def _build_state() -> AuthoritativeState:
    terrain = {(x, y): "PLAIN" for x in range(3) for y in range(3)}
    entities = {
        1: (
            V2EntityBuilder(1)
            .kind("TEST")
            .location(1.0, 1.0)
            .combat(readiness=100.0)
            .build()
        )
    }
    return AuthoritativeState(tick=0, seed=42, entities=entities, terrain=terrain)


def test_render_writes_under_data_runs_run_id_renders_directory(tmp_path):
    base_dir = str(tmp_path)
    run_id = "run-abc-123"

    out_path = render_output_path(base_dir, run_id, "tick_0000.png")
    assert out_path == os.path.join(base_dir, run_id, "renders", "tick_0000.png")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    state = _build_state()
    render(state, out_path)

    assert os.path.exists(out_path)
    assert os.path.basename(os.path.dirname(out_path)) == "renders"
    assert os.path.basename(os.path.dirname(os.path.dirname(out_path))) == run_id
