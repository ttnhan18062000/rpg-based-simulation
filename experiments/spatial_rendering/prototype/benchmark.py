"""Prototype benchmark: (1) render cost at real-world scale (256x256), (2) checkpoint-pickle
cost vs. replay-tick cost — resolving the two biggest open questions with real numbers.
"""
from __future__ import annotations

import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.platform.rng import DeterministicRNG
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from render_world import render  # noqa: E402


def main() -> None:
    world_id = "wilderness_survival"
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)

    t0 = time.perf_counter()
    state, report = WorldCompiler.compile(spec, seed=42)
    compile_ms = (time.perf_counter() - t0) * 1000
    print(f"Compiled {world_id}: entities={report['entity_count']} in {compile_ms:.1f}ms, terrain_tiles={len(state.terrain)}")

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)

    t0 = time.perf_counter()
    stats = render(state, str(out_dir / f"{world_id}_scale_test.png"), scale=3)
    render_ms = (time.perf_counter() - t0) * 1000
    print(f"Render at scale=3: {render_ms:.1f}ms, output {stats['width_px']}x{stats['height_px']}px, grid {stats['grid_w']}x{stats['grid_h']}")

    # --- Checkpoint (pickle) cost vs. replay (re-tick) cost ---
    profile = RuntimeProfile(
        name="BENCH", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048, max_cpu_percent=90.0, max_worker_count=0,
        max_tick_budget_ms=200.0, max_queue_depth=100,
        max_replay_buffer_kb=4096, max_observability_budget_percent=5.0,
    )
    rng = DeterministicRNG(42)
    kernel = Kernel(profile=profile, state=state, rng=rng, world_id=world_id)

    N_TICKS = 50
    t0 = time.perf_counter()
    for _ in range(N_TICKS):
        kernel.tick_once()
    tick_total_ms = (time.perf_counter() - t0) * 1000
    print(f"\n{N_TICKS} ticks (live, no checkpointing): {tick_total_ms:.1f}ms total, {tick_total_ms/N_TICKS:.2f}ms/tick")

    t0 = time.perf_counter()
    blob = pickle.dumps(kernel._state, protocol=pickle.HIGHEST_PROTOCOL)
    pickle_ms = (time.perf_counter() - t0) * 1000
    blob_kb = len(blob) / 1024
    print(f"Single full-state pickle (checkpoint): {pickle_ms:.1f}ms, {blob_kb:.1f}KB")

    t0 = time.perf_counter()
    restored = pickle.loads(blob)
    unpickle_ms = (time.perf_counter() - t0) * 1000
    print(f"Single full-state unpickle (restore): {unpickle_ms:.1f}ms")

    # Simulate dense checkpointing: one checkpoint every tick for N_TICKS.
    t0 = time.perf_counter()
    for _ in range(N_TICKS):
        pickle.dumps(kernel._state, protocol=pickle.HIGHEST_PROTOCOL)
    dense_checkpoint_ms = (time.perf_counter() - t0) * 1000
    print(f"\nDense checkpointing simulation ({N_TICKS} checkpoints, state held constant): {dense_checkpoint_ms:.1f}ms total, "
          f"{dense_checkpoint_ms/N_TICKS:.2f}ms/checkpoint, storage = {blob_kb*N_TICKS/1024:.2f}MB for {N_TICKS} ticks")
    print(f"Replay-only cost for the same {N_TICKS} ticks: {tick_total_ms:.1f}ms total, 0 bytes stored")
    print(f"Ratio: dense checkpointing costs {dense_checkpoint_ms/tick_total_ms:.2f}x the CPU of plain replay, "
          f"PLUS {blob_kb*N_TICKS/1024:.2f}MB storage replay needs zero of")


if __name__ == "__main__":
    main()
