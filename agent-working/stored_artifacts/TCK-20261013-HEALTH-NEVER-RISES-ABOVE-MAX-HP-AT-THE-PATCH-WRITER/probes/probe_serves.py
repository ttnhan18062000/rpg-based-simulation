import sys,os
tree='/mnt/data/Working/rpg-based-simulation/.claude/worktrees/rpg-heal'
os.chdir(tree); sys.path.insert(0,tree)
from collections import Counter
from tests.helpers.scenario import compile_world
from src.engine import serves as S
from src.content_semantics.faction import get_faction_id_str
for seed in (42,43,44):
    st=compile_world('urban_political',seed)
    c=Counter(); ex={}
    for b in st.buildings.values():
        if not b.functional: continue
        ctrl=S._controlling_faction(st,b)
        for e in st.entities.values():
            if not e.combat.alive or not S.keeps_coin(e): continue
            ok=S.serves(st,e,b); k=(b.kind,get_faction_id_str(e),ctrl,ok); c[k]+=1
    refused=[(k,n) for k,n in c.items() if not k[3]]
    print(seed,'trading-person x building pairs',sum(c.values()),'refused',sum(n for _,n in refused))
    for k,n in sorted(refused,key=str)[:12]: print('  ',k,n)
