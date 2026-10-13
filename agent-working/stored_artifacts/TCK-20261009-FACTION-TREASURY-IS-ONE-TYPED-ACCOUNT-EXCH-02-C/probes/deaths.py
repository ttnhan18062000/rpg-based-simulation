import sys
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
dead=set(); out=[]
for t in range(TICKS):
    k.tick_once()
    for i,e in k.state.entities.items():
        if not e.combat.alive and i not in dead:
            dead.add(i); out.append((t+1,i,str(e.lifecycle.death_reason),tuple(round(x) for x in e.navigation.position)))
print("DEATHS",out)
k.shutdown()
