"""Local instrumentation (not committed): per tick, every entity's stored concerns in dict order; every capacity trim; the canonical hash every 5 ticks."""
import json, sys, os, shutil
sys.path.insert(0, ".")
world, seed, ticks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase as C
from tools.test_architecture.rpg_gate_run import build_kernel
f = open(out, "w")
cur = {"tick": 0}
oe = C.enforce
def en(state, update):
    res = oe(state, update)
    for e_id, u in res.entity_updates.items():
        su = u.strategic
        if su is None or not su.concerns_remove: continue
        old = update.entity_updates.get(e_id)
        before = set(old.strategic.concerns_remove) if old and old.strategic else set()
        dropped = [c for c in su.concerns_remove if c not in before]
        if not dropped: continue
        ent = state.entities[e_id]
        f.write(json.dumps({"k": "trim", "tick": state.tick, "e": e_id,
            "stored": [[c.id, c.urgency] for c in ent.strategic.concerns.values()],
            "add": [[c.id, c.urgency] for c in (old.strategic.concerns_add_or_update if old and old.strategic else [])],
            "dropped": dropped}) + "\n")
    return res
C.enforce = staticmethod(en)
run_id = f"inst_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, run_id)
for t in range(ticks):
    k.tick_once()
    s = k.state
    f.write(json.dumps({"k": "c", "tick": s.tick, "c": {str(e.id): [[c.id, c.urgency] for c in e.strategic.concerns.values()] for e in s.entities.values() if e.strategic.concerns}}) + "\n")
    if t % 5 == 4:
        f.write(json.dumps({"k": "h", "tick": s.tick, "h": CanonicalStateHasher.get_hash(s)}) + "\n")
f.write(json.dumps({"k": "final", "h": CanonicalStateHasher.get_hash(k.state)}) + "\n")
f.close(); k.shutdown(); shutil.rmtree(f"data/runs/{run_id}", ignore_errors=True)
