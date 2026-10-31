"""Scratch: per-tick group store trace for one world. Usage: trace3738.py <world> <seed> <ticks> <out.jsonl> <ids,comma>"""
import sys, json
sys.path.insert(0, ".")
import src.core.state as st
from src.systems.world_systems.groups import GroupSystem
from src.engine.apply import ApplyPath
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tools.calibrate_simq import _load_world_state
world, seed, ticks, out, ids = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], [int(x) for x in sys.argv[5].split(",")]
fh = open(out, "w")
cur = []
oi = st.GroupRecord.__init__
def ini(self, *a, **k):
    oi(self, *a, **k)
    if sys._getframe(1).f_globals.get("__name__") == "src.systems.world_systems.groups": cur.append(self)
st.GroupRecord.__init__ = ini
ou = GroupSystem.update_groups
forms = []
def ug(state, *a, **k):
    cur.clear(); r = ou(state, *a, **k)
    for g in cur:
        ex = state.groups.get(g.id)
        forms.append([state.tick, g.id, sorted(g.member_ids), "none" if ex is None else ("dissolved" if ex.dissolution_tick is not None else "live")])
    return r
GroupSystem.update_groups = staticmethod(ug)
oa = ApplyPath.apply_generation
def ag(prior, update, *a, **k):
    new = oa(prior, update, *a, **k)
    rec = {"t": prior.tick, "n": len(new.groups), "dis": sum(1 for g in new.groups.values() if g.dissolution_tick is not None), "forms": list(forms)}
    forms.clear()
    for i in ids:
        e = new.entities.get(i)
        rec["e%d" % i] = None if e is None else [e.identity.group_id, e.combat.alive, e.lifecycle.active]
    rec["rec"] = {str(g.id): [sorted(g.member_ids), g.leader_id, g.dissolution_tick] for g in new.groups.values() if set(ids) & set(g.member_ids)} if prior.tick >= 125 else {}
    fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    return new
ApplyPath.apply_generation = staticmethod(ag)
state, _ = _load_world_state(world, seed)
k = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(state.seed), flags={"no_frame_pacing": True, "audit_mode": True, "no_replay": True})
try:
    for _ in range(ticks): k.tick_once()
finally:
    k.shutdown(); fh.close()
