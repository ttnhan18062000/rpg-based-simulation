"""refire_probe.py <root> <world> <seed> <ticks> <out>. Read-only: logs every learn("abandoned") (tick, group, member, leader), every PartyCohesionService.evaluate status,
every change of a trust_history value, and every trust_history.get() that reads a present negative value (caller file:line)."""
import sys, os, json, collections
root, world, seed, ticks, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
os.chdir(root); sys.path.insert(0, root)
from tools.test_architecture.rpg_gate_run import build_kernel
CUR = {"t": 0, "k": None}
LEARN = []; COH = []; TRUST = []; READS = collections.Counter(); READ_ALL = collections.Counter()
from src.domains.cooperation.services import CooperationLearningService as L, PartyCohesionService as P
oL = L.learn
def learn(entity, outcome, state):
    r = oL(entity, outcome, state)
    LEARN.append([state.tick, entity.id, outcome.partner_id, outcome.outcome_type, r.trust_delta])
    return r
L.learn = staticmethod(learn)
oP = P.evaluate
def ev(g_id, state):
    r = oP(g_id, state)
    g = state.groups.get(g_id)
    COH.append([state.tick, g_id, str(r.status), g.leader_id if g else None, len(g.member_ids) if g else None])
    return r
P.evaluate = staticmethod(ev)
class LDict(dict):
    def get(self, key, default=None):
        v = dict.get(self, key, default)
        if key in self:
            f = sys._getframe(1); loc = f"{os.path.relpath(f.f_code.co_filename, root)}:{f.f_lineno}"
            READ_ALL[loc] += 1
            if v <= -0.5: READS[loc] += 1
        return v
from src.systems.social_systems.relationships import RelationshipService as R
from dataclasses import replace
oPU = R.process_update
def pu(social, update):
    r = oPU(social, update)
    return replace(r, trust_history=LDict(r.trust_history)) if update.trust_delta or isinstance(social.trust_history, LDict) else r
R.process_update = staticmethod(pu)
run_id = f"rf_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, run_id); last = {}; dis = {}
for t in range(ticks):
    k.tick_once()
    st = k.state
    for e in st.entities.values():
        for tgt, v in e.social.trust_history.items():
            if last.get((e.id, tgt)) != v:
                last[(e.id, tgt)] = v; TRUST.append([st.tick, e.id, tgt, round(v, 4), int(e.lifecycle.active)])
    for gid, g in st.groups.items():
        if g.dissolution_tick is not None and gid not in dis: dis[gid] = g.dissolution_tick
st = k.state
bondsat = {f"{e.id}->{tg}": (e.social.bonds[tg].sentiment if tg in e.social.bonds else None) for e in st.entities.values() for tg in e.social.trust_history}
alive = {e.id: int(e.lifecycle.active) for e in st.entities.values()}
groups = {gid: {"leader": g.leader_id, "members": list(g.member_ids), "dissolved": g.dissolution_tick} for gid, g in st.groups.items()}
k.shutdown()
import shutil; shutil.rmtree(os.path.join("data", "runs", run_id), ignore_errors=True)
json.dump({"world": world, "seed": seed, "ticks": ticks, "learn": LEARN, "cohesion": COH, "trust_changes": TRUST, "negative_reads": dict(READS), "all_reads": dict(READ_ALL),
           "bond_sentiment_for_trust_pairs_final": bondsat, "alive_final": alive, "groups_final": groups, "dissolution": dis}, open(out, "w"))
