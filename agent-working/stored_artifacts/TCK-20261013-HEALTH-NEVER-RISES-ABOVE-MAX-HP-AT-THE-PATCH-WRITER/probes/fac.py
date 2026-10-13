import sys,os,json
tree,seed,out=sys.argv[1],int(sys.argv[2]),sys.argv[3]
os.chdir(tree); sys.path.insert(0,tree)
from collections import Counter
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world
from src.content_semantics.faction import get_faction_id_str
st=compile_world('urban_political',seed)
k=Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms":1e9}),state=st,rng=DeterministicRNG(seed),flags={"no_frame_pacing":True},executor=LocalSequentialExecutor(),governor=PinnedNormalGovernor())
for i in range(5000): k.tick_once()
s=k._state; d=Counter(); al=Counter()
for e in s.entities.values():
    f=get_faction_id_str(e); sp=(e.identity.properties or {}).get('species_id')
    if e.combat.alive: al[f"{sp}/{f}"]+=1
    else:
        c=e.lifecycle.death_reason or (e.lifecycle.passive_death_cause.value if getattr(e.lifecycle,'passive_death_cause',None) else 'UNKNOWN')
        d[f"{sp}/{f}/{c}"]+=1
json.dump({"deaths":d,"alive":al},open(out,'w')); k.shutdown()
