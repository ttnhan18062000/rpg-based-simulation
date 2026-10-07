"""usage: ctxdeaths.py <world> <ticks> ; with CompileContext (real entry path). deaths by cause + eat/sleep + alive series"""
import sys, collections
from dataclasses import replace
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
w=sys.argv[1]; ticks=int(sys.argv[2])
spec,ctx=WorldRepository("data/worlds").load_world_with_context(w)
state,_=WorldCompiler.compile(spec,seed=42,context=ctx)
prof=RuntimeProfile(name="p",hardware_class=HardwareClass.CLASS_B,max_ram_mb=2048,max_cpu_percent=100.0,max_worker_count=1,max_queue_depth=2000,max_replay_buffer_kb=0,max_observability_budget_percent=0.0,max_tick_budget_ms=1e9)
k=Kernel(profile=prof,state=state,rng=DeterministicRNG(42),flags={"no_frame_pacing":True,"audit_mode":True})
prev={}; dead=set(); cause=collections.Counter(); hist=collections.Counter(); eat=collections.Counter(); sleep=collections.Counter(); series=[]
for t in range(1,ticks+1):
    k.tick_once()
    alive=0
    for eid,e in k.state.entities.items():
        b=e.biological; al=e.combat.alive; alive+=al
        p=prev.get(eid)
        if p and p[2] and al:
            if b.hunger<p[0]-1e-9: eat[t//100]+=1
            if b.sleep_debt<p[1]-1e-9: sleep[t//100]+=1
        if p and p[2] and not al and eid not in dead:
            dead.add(eid); L=e.lifecycle
            cause[(str(getattr(L,"passive_death_cause",None)),str(getattr(L,"death_reason",None)))]+=1; hist[t//100]+=1
        prev[eid]=(b.hunger,b.sleep_debt,al)
    if t%100==0: series.append((t,alive,round(sum(e.biological.hunger for e in k.state.entities.values() if e.combat.alive)/max(alive,1),1)))
k.shutdown()
print(w,"series(t,alive,mean_hunger)",series); print("deaths hist",sorted(hist.items())); print("cause",cause.most_common()); print("eat",sorted(eat.items())); print("sleep",sorted(sleep.items()))
