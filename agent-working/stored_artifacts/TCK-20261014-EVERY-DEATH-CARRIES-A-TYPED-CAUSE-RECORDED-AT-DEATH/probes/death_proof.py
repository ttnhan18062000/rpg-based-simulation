import json, os, sys, shutil, importlib.util
from pathlib import Path
from collections import Counter
from tools.test_architecture.rpg_gate_run import build_kernel
spec = importlib.util.spec_from_file_location("proj", "/mnt/data/Working/rpg-based-simulation/.claude/worktrees/deathcause/tests/helpers/death_field_projection.py")
proj = importlib.util.module_from_spec(spec); spec.loader.exec_module(proj)
from src.engine.checkpoint import CanonicalStateHasher
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rid = f"dp_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, rid)
for _ in range(ticks): k.tick_once()
st = k.state
alive = Counter(); dead = Counter(); cause = Counter()
for e in st.entities.values():
    if e.combat.alive: alive[e.kind] += 1
    else: dead[e.kind] += 1; cause[(e.kind, e.lifecycle.death_reason)] += 1
r = {"world": world, "seed": seed, "ticks": ticks, "full_digest": CanonicalStateHasher.get_hash(st), "projected_digest": proj.projected_digest(st),
     "movement_count": st.movement_count, "alive": dict(alive), "dead": dict(dead), "cause": {f"{a}|{b}": v for (a, b), v in sorted(cause.items(), key=str)},
     "records": sum(1 for e in st.entities.values() if getattr(e.lifecycle, "death_record", None) is not None)}
k.shutdown(); json.dump(r, open(out, "w"), sort_keys=True, indent=1)
shutil.rmtree(Path("data/runs") / rid, ignore_errors=True)
