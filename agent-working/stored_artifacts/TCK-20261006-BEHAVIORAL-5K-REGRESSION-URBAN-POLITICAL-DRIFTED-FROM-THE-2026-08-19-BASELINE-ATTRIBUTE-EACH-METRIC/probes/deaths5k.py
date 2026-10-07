"""usage: deaths5k.py <out.json> [ticks]; cwd = worktree. Per-tick: deaths by cause + hist, eat/sleep events (hunger/sleep_debt decrease)."""
import sys, json, collections
from dataclasses import replace
out=sys.argv[1]; ticks=int(sys.argv[2]) if len(sys.argv)>2 else 2000
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
spec=WorldRepository("data/worlds").load_world("urban_political")
state,_=WorldCompiler.compile(spec,seed=42)
fl=dict(state.feature_flags); fl["ENABLE_ADVENTURE_ROUTING"]=1.0
state=replace(state,feature_flags=fl)
prof=RuntimeProfile(name="p",hardware_class=HardwareClass.CLASS_B,max_ram_mb=2048,max_cpu_percent=100.0,max_worker_count=1,max_queue_depth=2000,max_replay_buffer_kb=0,max_observability_budget_percent=0.0,max_tick_budget_ms=1e9)
k=Kernel(profile=prof,state=state,rng=DeterministicRNG(42),flags={"no_frame_pacing":True,"audit_mode":True})
prev={}; dead=set(); deaths=[]; eat=collections.Counter(); sleep=collections.Counter()
try:
    for t in range(1,ticks+1):
        k.tick_once()
        for eid,e in k.state.entities.items():
            b=e.biological; al=e.combat.alive
            p=prev.get(eid)
            if p and p[2] and al:
                if b.hunger<p[0]-1e-9: eat[t//100]+=1
                if b.sleep_debt<p[1]-1e-9: sleep[t//100]+=1
            if p and p[2] and not al and eid not in dead:
                dead.add(eid); L=e.lifecycle
                deaths.append({"t":t,"id":str(eid),"hunger":b.hunger,"sleep":b.sleep_debt,"passive":str(getattr(L,"passive_death_cause",None)),"reason":str(getattr(L,"death_reason",None)),"name":getattr(e,"name",None) or str(getattr(e,"entity_type",""))})
            prev[eid]=(b.hunger,b.sleep_debt,al)
finally:
    k.shutdown()
hist=collections.Counter(d["t"]//100 for d in deaths)
cause=collections.Counter((d["passive"],d["reason"]) for d in deaths)
json.dump({"deaths":deaths,"hist":sorted(hist.items()),"cause":[(list(a),n) for a,n in cause.items()],"eat":sorted(eat.items()),"sleep":sorted(sleep.items()),"n_entities_final":len(k.state.entities)},open(out,"w"))
print("hist",sorted(hist.items())); print("cause",cause.most_common()); print("eat",sorted(eat.items())); print("sleep",sorted(sleep.items()))
