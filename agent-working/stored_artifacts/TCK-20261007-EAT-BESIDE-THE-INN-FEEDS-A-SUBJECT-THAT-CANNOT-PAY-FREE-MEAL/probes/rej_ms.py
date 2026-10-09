"""Decision-27 / free-meal pinned measurement. usage: forage_ms.py <root> <world> <ticks> <seed> [label]
Pinned NORMAL governor + audit_mode + budget off + LocalSequentialExecutor. Counters degrade gracefully on the base arm (no opening steps)."""
import collections, hashlib, json, os, statistics, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); LABEL = sys.argv[5] if len(sys.argv) > 5 else ""
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
class Pin(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
EATF = collections.Counter(); 
from src.core.conservation import ResourceTransactionResolver as RTR
REJ=collections.Counter(); OK=collections.Counter(); first={}
_r=RTR.resolve.__func__ if hasattr(RTR.resolve,"__func__") else RTR.resolve
def res(state, entity, intent, *a, **kw):
    out=_r(state, entity, intent, *a, **kw)
    key=(intent.source_kind, getattr(intent,"transfer_kind",None))
    if intent.source_kind in("TOWN_SERVICE","SERVICE_FEE","TAX","REPAIR_FEE","INFORMATION_PURCHASE"):
        if out.accepted: OK[key]+=1
        else: REJ[key+(str(out.reason), "broke" if entity.inventory.gold<5 else "can_pay")]+=1; first.setdefault(entity.id,state.tick)
    return out
RTR.resolve=staticmethod(res)
for _ in range(TICKS): k.tick_once()
k.shutdown()
print("RJ",json.dumps(dict(seed=SEED,rejected={"|".join(map(str,k_)):v for k_,v in REJ.items()},accepted={"|".join(map(str,k_)):v for k_,v in OK.items()},entities_rejected=len(first))))
