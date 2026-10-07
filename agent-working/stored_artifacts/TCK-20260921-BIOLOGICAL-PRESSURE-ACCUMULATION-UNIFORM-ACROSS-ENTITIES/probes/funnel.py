import sys, collections
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
from src.engine.domain.core_actions import CoreActions
from src.engine.town_resolution import TownResolutionSystem
calls=collections.Counter(); _orig=CoreActions.execute_survival
def _spy(entity, action, tick):
    calls[(tick//100,action)]+=1
    return _orig(entity, action, tick)
CoreActions.execute_survival=staticmethod(_spy)
act=collections.Counter(); proj=collections.Counter(); rej=collections.Counter(); outcome=collections.Counter()
for t in range(1,ticks+1):
    k.tick_once()
    if t%50==0:
        inns=[b.position for b in k.state.buildings.values() if b.kind=="inn"]
        rows=[]
        for e in k.state.entities.values():
            if not e.combat.alive or not e.strategic.projects: continue
            ps=[p for p in e.strategic.projects.values() if getattr(p,"kind","") in ("hunger","fatigue") and 'ACTIVE' in str(p.status)]
            if ps and inns:
                d=min(abs(i[0]-e.navigation.position[0])+abs(i[1]-e.navigation.position[1]) for i in inns)
                rows.append((e.id,ps[0].kind.value,round(d,1),e.strategic.current_objective_id is not None, (e.task.work_kind, e.task.payload, round(e.biological.hunger,1)) if hasattr(e.task,'work_kind') else None))
        if rows and t%200==0 and t>=1000: print(t,rows[:8])
    if t%100==0:
        c=collections.Counter()
        for e in k.state.entities.values():
            if not e.combat.alive: continue
            p=e.strategic.projects.get(e.strategic.current_project_id or "")
            c[str(getattr(p,"kind",None))]+=1
        print("curproj",t,dict(c))
    for e in k.state.entities.values():
        if not e.combat.alive: continue
        pl=getattr(e.task,"payload",None) or {}
        a=pl.get("action")
        if a in ("EAT","REST","SLEEP"): act[(t//100,a)]+=1; outcome[(a,pl.get("outcome"),pl.get("reason"))]+=1
        for p in e.strategic.projects.values():
            if getattr(p,"kind","") in ("hunger","fatigue"): proj[(t//100,p.kind,str(getattr(p,"status","")))]+=1
print("execute_survival calls",sorted(calls.items())); print("actions",sorted(act.items())); print("outcomes",outcome.most_common(8)); print("projects(sample)",sorted(proj.items())[:30])
print("rejections",dict(k.state.rejections) if hasattr(k.state,"rejections") else "")
k.shutdown()
