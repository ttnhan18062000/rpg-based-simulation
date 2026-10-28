import sys; sys.path.insert(0,".")
from pathlib import Path
import src.worldassembly.resolver as R
from src.worldassembly.resolve_io import resolve_composition_file
orig=R.topological_sort_modules
def authored_first(modules_map):
    # Kahn with ties broken by insertion (authored) order instead of alphabetical
    adj={m:set() for m in modules_map}; deg={m:0 for m in modules_map}
    for m,s in modules_map.items():
        for r in s.requires:
            if r in modules_map: adj[r].add(m); deg[m]+=1
    ready=[m for m in modules_map if deg[m]==0]; out=[]
    while ready:
        c=ready.pop(0); out.append(c)
        for n in modules_map:
            if n in adj[c]:
                deg[n]-=1
                if deg[n]==0: ready.append(n)
    return out
changed=[]
for y in sorted(Path("data/worlds").glob("*/world.yaml")):
    R.topological_sort_modules=orig; _,a=resolve_composition_file(y)
    R.topological_sort_modules=authored_first; _,b=resolve_composition_file(y)
    if a!=b: changed.append(y.parent.name)
print("resolved text differs when authored order wins ties:",len(changed),changed)
