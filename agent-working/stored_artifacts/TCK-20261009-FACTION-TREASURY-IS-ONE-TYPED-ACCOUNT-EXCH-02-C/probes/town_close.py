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
rows=[]
for t in range(TICKS):
    k.tick_once()
    if (t+1)%250==0:
        s=k.state
        b=[(x.kind,x.functional,x.inventory.gold) for x in s.buildings.values()]
        rows.append((t+1, s.global_resources.get('faction_hero_guild_gold'), sum(1 for x in b if x[1]), len(b), sum(x[2] for x in b)))
print("ROWS (tick, hero treasury, functional, buildings, building purses)")
for r in rows: print(r)
k.shutdown()
