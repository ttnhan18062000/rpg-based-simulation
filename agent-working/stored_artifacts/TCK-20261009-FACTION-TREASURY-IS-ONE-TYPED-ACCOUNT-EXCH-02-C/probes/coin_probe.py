import sys,collections
ROOT,WORLD,TICKS,SEED=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
sys.path.insert(0,ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from tests.helpers.kernel_pinning import PinnedNormalGovernor
spec,ctx=WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state,_=WorldCompiler.compile(spec,SEED,context=ctx)
k=Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms":1e9}),state=state,rng=DeterministicRNG(SEED),governor=PinnedNormalGovernor(),flags={"no_frame_pacing":True,"no_replay":True,"audit_mode":True},executor=LocalSequentialExecutor())
def parts(s):
    e=sum(x.inventory.gold for x in s.entities.values()); b=sum(x.inventory.gold for x in s.buildings.values())
    t=sum(v for kk,v in s.global_resources.items() if kk.startswith("faction_") and kk.endswith("_gold"))
    c=sum(getattr(x,"gold",0) for x in s.corpses.values())
    return e,b,t+0,c
seen=set(k.state.entities); created=0.0
e0,b0,t0,c0=parts(k.state); prev=(e0,b0,t0,c0); last=e0+b0+t0+c0
rows=[]
for tk in range(TICKS):
    k.tick_once(); s=k.state
    for i,x in s.entities.items():
        if i not in seen: seen.add(i); created+=x.inventory.gold
    e,b,t,c=parts(s); tot=e+b+t+c
    if tot!=last:
        rows.append((tk+1,round(e-prev[0],1),round(b-prev[1],1),round(t-prev[2],1),round(c-prev[3],1),round(tot-last,1)))
    prev=(e,b,t,c); last=tot
print("start",e0,b0,t0,c0,"created",created,"end",*parts(k.state),"drift",round(sum(parts(k.state))-(e0+b0+t0+c0+created),1))
print("ticks with total change:",len(rows),"first 12:",[r for r in rows if r[5]!=0][:25])
k.shutdown()
