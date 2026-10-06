import sys, json, collections
from tests.helpers.scenario import compile_world, DEFAULT_SEED, DEFAULT_FLAGS
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.engine.spatial_query import SpatialQueryService
world=sys.argv[1]; ticks=int(sys.argv[2]); out=sys.argv[3]
st=compile_world(world, DEFAULT_SEED)
k=Kernel(profile=PROD_SMALL,state=st,rng=DeterministicRNG(DEFAULT_SEED),flags=dict(DEFAULT_FLAGS))
watch=list(st.regions)  # every region of the world, so a world with different region names cannot KeyError
bounds={r:g.bounds for r,g in st.regions.items()}
series={r:[] for r in watch}; allmax=collections.defaultdict(float); first50={}
alive_prev={e.id:e.combat.alive for e in st.entities.values()}
deaths=collections.Counter(); tick_deaths=[]
def reg_of(x,y):
    hits=[r for r,(a,b,c,d) in bounds.items() if a<=x<=c and b<=y<=d]
    return hits
f=open(out,"w")
for t in range(ticks):
    k.tick_once(); s=k._state
    for r in watch: series[r].append(round(s.regions[r].trauma_score,4))
    for r,g in s.regions.items():
        allmax[r]=max(allmax[r],g.trauma_score)
        if g.trauma_score>50 and r not in first50: first50[r]=t
    for e in s.entities.values():
        was=alive_prev.get(e.id,True)
        if was and not e.combat.alive:
            p=e.navigation.position; hs=reg_of(p[0],p[1])
            cr=SpatialQueryService.get_region_at(s,(p[0],p[1])); tick_deaths.append((t,e.id,hs,cr.id if cr else None,[float(p[0]),float(p[1])],str(e.kind),str(getattr(e.lifecycle,'death_reason',None)),str(getattr(e.lifecycle,'passive_death_cause',None)),getattr(e.lifecycle,'age_ticks',None),getattr(e.lifecycle,'max_age_ticks',None),float(e.combat.hp)))
        alive_prev[e.id]=e.combat.alive
    if (t+1)%500==0:
        f.write(json.dumps({"tick":t+1,"trauma":{r:series[r][-1] for r in watch},"first50":first50,"max":dict(allmax),"deaths":len(tick_deaths)})+"\n"); f.flush()
json.dump({"series":series,"deaths":tick_deaths},open(out+".full.json","w"))
k.shutdown()
f.write(json.dumps({"final":True,"ticks":ticks,"first50":first50,"max":dict(allmax)})+"\n")
f.close()
