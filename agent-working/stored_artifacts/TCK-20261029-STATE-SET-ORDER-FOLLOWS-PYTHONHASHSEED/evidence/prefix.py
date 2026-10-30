"""Prefix check: set up exactly as arm_child.py does for a 5000-tick run (ticks=5000), stop at t1000, record the canonical hash. Usage: prefix.py <world> <seed> <out.json>"""
import json, os, shutil, sys, time
sys.path.insert(0, ".")
world, seed, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
total = 5000
from src.engine.checkpoint import CanonicalStateHasher
from tools.test_architecture.rpg_gate_run import build_kernel
run_id = f"prefix_{world}_{seed}_{os.getpid()}"
kernel = build_kernel(world, seed, run_id)
t0 = time.time()
for t in range(total):
    if t == 1000:
        break
    kernel.tick_once()
h = CanonicalStateHasher.get_hash(kernel.state)
kernel.shutdown()
shutil.rmtree(f"data/runs/{run_id}", ignore_errors=True)
json.dump({"world": world, "seed": seed, "configured_ticks": total, "stopped_at": 1000, "hash_at_t1000": h, "hashseed": os.environ.get("PYTHONHASHSEED"), "wall_s": round(time.time() - t0, 1)}, open(out, "w"))
print("PREFIX", world, seed, h[:16])
