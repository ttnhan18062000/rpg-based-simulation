"""trust_probe.py <root> <world> <seed> <ticks> <out>. Read-only instrumentation of every trust writer (wraps, never changes behaviour)."""
import sys, os, json, collections
root, world, seed, ticks, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
os.chdir(root); sys.path.insert(0, root)
from tools.test_architecture.rpg_gate_run import build_kernel
C = collections.Counter(); X = collections.defaultdict(lambda: collections.Counter())
def wrap_static(cls, name, key, post=None):
    orig = getattr(cls, name)
    def f(*a, **k):
        r = orig(*a, **k); C[key + ".calls"] += 1
        if post: post(a, k, r)
        return r
    setattr(cls, name, staticmethod(f))
from src.domains.cooperation.services import CooperationLearningService as L, PartyCohesionService as P
def post_learn(a,k,r): X["learn.outcome_type"][a[1].outcome_type]+=1; C["learn.nonzero_trust"] += (r.trust_delta!=0)
wrap_static(L,"learn","CooperationLearningService.learn",post_learn)
def post_coh(a,k,r):
    X["cohesion.status"][str(r.status)]+=1
wrap_static(P,"evaluate","PartyCohesionService.evaluate",post_coh)
from src.systems.social_systems.appraisal import SocialAppraisalSystem as S
wrap_static(S,"process_betrayal","SocialAppraisalSystem.process_betrayal")
wrap_static(S,"recalibrate_trust","SocialAppraisalSystem.recalibrate_trust")
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem as SI
wrap_static(SI,"process_outcome","StrategicIntelligenceSystem.process_outcome")
from src.systems.social_systems.relationships import RelationshipService as R
o_pu = R.process_update
def pu(social, update):
    r = o_pu(social, update); C["RelationshipService.process_update.calls"] += 1
    if update.trust_delta:
        C["process_update.with_trust_delta"] += 1
        for eid, d in update.trust_delta.items():
            X["process_update.delta_sign"]["neg" if d<0 else "pos" if d>0 else "zero"] += 1
            C["process_update.entries_after"] += (eid in r.trust_history)
    return r
R.process_update = staticmethod(pu)
from src.engine import patches
o_sp = patches.SocialPatch.apply
def sp(self, entity, changes):
    C["SocialPatch.apply.calls"] += 1
    if self.social is not None and self.social.trust_delta: C["SocialPatch.apply.with_trust_delta"] += 1
    return o_sp(self, entity, changes)
patches.SocialPatch.apply = sp
from src.domains.cooperation.phase import CooperationPhase as CP
o_ex = CP.execute
def ex(*a, **k):
    r = o_ex(*a, **k); C["CooperationPhase.execute.calls"] += 1
    for eid, u in (r.entity_updates or {}).items():
        pr = getattr(u, "property_updates", None) or {}
        if pr.get("last_cooperation_decision") is not None: X["cooperation.decision"][str(pr["last_cooperation_decision"])] += 1
        s = getattr(u, "social", None)
        if s is not None and s.trust_delta: C["CooperationPhase.result_entity_updates_with_trust_delta"] += 1
    return r
CP.execute = staticmethod(o_ex and ex) if isinstance(CP.__dict__.get("execute"), staticmethod) else ex
run_id=f"tp_{world}_{seed}_{os.getpid()}"
k = build_kernel(world, seed, run_id); G=[]
for t in range(ticks):
    k.tick_once()
    if t % 250 == 0: G.append([k.state.tick, len(k.state.groups), sum(1 for g in k.state.groups.values() if g.dissolution_tick is None)])
st = k.state
nt = [(e.id, dict(e.social.trust_history)) for e in st.entities.values() if e.social.trust_history]
bonds = sum(len(e.social.bonds) for e in st.entities.values())
k.shutdown()
import shutil; shutil.rmtree(os.path.join("data","runs",run_id),ignore_errors=True)
json.dump({"world":world,"seed":seed,"ticks":ticks,"counters":dict(C),"breakdown":{a:dict(b) for a,b in X.items()},"groups_sampled[tick,total,active]":G,"final_entities_with_trust":len(nt),"final_trust_entries":nt[:20],"final_total_bonds":bonds,"entities":len(st.entities),"groups_final":len(st.groups)},open(out,"w"),indent=1,default=str)
