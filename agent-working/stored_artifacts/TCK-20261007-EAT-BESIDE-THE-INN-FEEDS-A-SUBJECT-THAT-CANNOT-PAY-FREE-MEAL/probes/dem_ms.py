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

from src.engine.biological_needs import need_rates
try:
    from src.core.items import food_hunger_recovery
except ImportError:
    food_hunger_recovery=lambda i:0.0
SAMP=[]; berries_prev=0; berries_gain=0; charges_used=0; prev=None; steps=[]; lastpos={}
def isfood(n):
    return food_hunger_recovery(n.yields_item) > 0
def inns(st): return [b.position for b in st.buildings.values() if b.kind=="inn"]
try:
    for _ in range(TICKS):
        k.tick_once(); st=k.state
        fn=[n for n in st.resource_nodes.values() if isfood(n)]
        cur={n.id:n.remaining_charges for n in fn}
        if prev is not None:
            for i,c in cur.items():
                if c<prev.get(i,c): charges_used+=prev[i]-c
        prev=cur
        tot=sum(s_.quantity for e in st.entities.values() for s_ in e.inventory.items if s_.item_id=="wild_berries")
        berries_gain+=max(0,tot-berries_prev) if tot>berries_prev else 0; berries_prev=tot
        for e in st.entities.values():
            if e.combat.alive and e.lifecycle.active and e.navigation.target is not None and e.id in lastpos:
                p=e.navigation.position; q=lastpos[e.id]; d=abs(p[0]-q[0])+abs(p[1]-q[1])
                if d>0: steps.append(d)
            lastpos[e.id]=e.navigation.position
        if st.tick%100==0:
            alive=[e for e in st.entities.values() if e.combat.alive and e.lifecycle.active]
            hb=[(e,need_rates(e)[0]) for e in alive]; hb=[(e,r) for e,r in hb if r>0]
            broke=[(e,r) for e,r in hb if e.inventory.gold<5]
            ip=inns(st)
            def dn(e,pts): return min((abs(p[0]-e.navigation.position[0])+abs(p[1]-e.navigation.position[1]) for p in pts),default=None)
            SAMP.append(dict(t=st.tick,alive=len(alive),hungering=len(hb),broke=len(broke),broke_rate_sum=sum(r for _,r in broke),
               broke_hunger_mean=(sum(e.biological.hunger for e,_ in broke)/len(broke) if broke else None),
               d_food=[dn(e,[n.position for n in fn]) for e,_ in broke], d_inn=[dn(e,ip) for e,_ in broke]))
finally:
    k.shutdown()
print("DM", json.dumps(dict(world=WORLD,seed=SEED,label=LABEL,samples=SAMP,charges_used=charges_used,berries_gain=berries_gain,
   step_mean=(sum(steps)/len(steps) if steps else None),nfood=len(prev or {}),food_pos=[n.position for n in st.resource_nodes.values() if isfood(n)])))
