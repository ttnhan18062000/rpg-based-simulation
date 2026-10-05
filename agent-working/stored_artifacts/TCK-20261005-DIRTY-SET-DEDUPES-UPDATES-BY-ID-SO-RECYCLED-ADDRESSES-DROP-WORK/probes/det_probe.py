"""Re-measure run-to-run divergence with CanonicalStateHasher as the instrument.
usage: det_probe.py <label> <world> <seed> <ticks>
Every run: audit_mode=True, max_tick_budget_ms=1e9, LocalSequentialExecutor. Records, per tick, the canonical
state hash, per-entity canonical hashes, and the governor mode; at the end total_dropped_work.
"""
import hashlib
import json
import sys

ROOT = "/mnt/data/Working/rpg-based-simulation/.claude/worktrees/lane-a-tactical-path-batch"
OUT = "/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad"
sys.path.insert(0, ROOT)
label, world, seed, ticks = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])

from src.config.profiles import PROD_SMALL
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(world)
state, _ = WorldCompiler.compile(spec, seed, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state,
           rng=DeterministicRNG(seed),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True},
           executor=LocalSequentialExecutor())
tick_hash, modes, ent_hash = [], [], []
try:
    for _ in range(ticks):
        k.tick_once()
        st = k._state
        tick_hash.append(CanonicalStateHasher.get_hash(st))
        modes.append(str(k._status.current_mode))
        ent_hash.append({
            str(e.id): hashlib.sha1(json.dumps(e.to_canonical_dict(), sort_keys=True, default=str).encode()).hexdigest()[:10]
            for e in st.entities.values()
        })
finally:
    k.shutdown()
out = {
    "label": label, "world": world, "seed": seed, "ticks": ticks,
    "total_dropped_work": k._status.total_dropped_work,
    "final_hash": tick_hash[-1], "tick_hash": tick_hash, "modes": modes, "ent_hash": ent_hash,
}
json.dump(out, open(f"{OUT}/det_{label}.json", "w"))
print(label, "final", tick_hash[-1][:16], "dropped", out["total_dropped_work"], "modes", sorted(set(modes)))
