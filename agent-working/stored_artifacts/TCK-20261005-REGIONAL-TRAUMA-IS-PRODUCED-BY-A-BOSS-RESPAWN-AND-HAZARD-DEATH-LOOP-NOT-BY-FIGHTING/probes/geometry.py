"""geometry.py: static region geometry for every resolved corpus world, no simulation.
Per world: every overlapping region pair with its inclusive-tile overlap, and each region's owned-tile share under the rule in force
(core.region_resolution.resolve_region_among: smallest area wins, ties to declaration order). Run: PYTHONPATH=. python geometry.py > geometry.jsonl"""
import glob, json, yaml, itertools, collections
from src.core.region_resolution import resolve_region_among
out=[]
for f in sorted(glob.glob("data/worlds/*/resolved/world.resolved.yaml")):
    w=f.split("/")[2]; d=yaml.safe_load(open(f))
    regs=[(r["id"],tuple(r["bounds"])) for r in d.get("regions",[])]
    if not regs: continue
    area={i:(b[2]-b[0]+1)*(b[3]-b[1]+1) for i,b in regs}   # inclusive tiles
    pairs={}
    for (a,ba),(b,bb) in itertools.combinations(regs,2):
        w_=min(ba[2],bb[2])-max(ba[0],bb[0])+1; h_=min(ba[3],bb[3])-max(ba[1],bb[1])+1
        if w_>0 and h_>0: pairs[f"{a}|{b}"]=w_*h_
    owned=collections.Counter(); union=set()
    for i,(x0,y0,x1,y1) in [(i,b) for i,b in regs]:
        for x in range(int(x0),int(x1)+1):
            for y in range(int(y0),int(y1)+1): union.add((x,y))
    class R:  # minimal duck type for resolve_region_among
        pass
    for (x,y) in union:
        cands=[]
        for i,b in regs:
            if b[0]<=x<=b[2] and b[1]<=y<=b[3]: cands.append(i)
        if len(cands)==1: owned[cands[0]]+=1
        elif cands: owned[min(cands,key=lambda c:(area[c],[i for i,_ in regs].index(c)))]+=1
    out.append({"world":w,"regions":{i:{"bounds":list(b),"area":area[i],"owned":owned.get(i,0)} for i,b in regs},"overlap_tiles":pairs})
for o in out: print(json.dumps(o))
