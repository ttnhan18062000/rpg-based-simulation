"""Readiness-rejection blocker probe (read-only). usage: rb_probe.py <root> <world> <ticks> <seed> <label>"""
import collections, json, sys
ROOT, WORLD, TICKS, SEED, LABEL = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.legality import LegalityServiceV2 as L
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
C = collections.Counter()
_vr = L.verify_readiness
def vr(entity):
    r = _vr(entity)
    if not r[0]: C["readiness_rejections"] += 1
    return r
L.verify_readiness = staticmethod(vr)
BID = "blocker_nav_INSUFFICIENT_READINESS"
open_ep = {}   # eid -> start tick
RB = {}        # eid -> (tick, for_readiness, pos)
life = []
def pk(e):
    s = e.strategic; p = s.projects.get(s.current_project_id) if s.current_project_id else None
    return str(getattr(p.kind, "value", p.kind)).lower() if p else None
prevk = {}
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for e in st.entities.values():
            b = e.strategic.blockers.get(BID)
            live = b is not None and not b.resolved
            if b is not None: C["blocker_entity_ticks"] += 1
            if live and e.id not in open_ep: open_ep[e.id] = st.tick; C["blocker_episodes"] += 1
            if not live and e.id in open_ep: life.append(st.tick - open_ep.pop(e.id))
            kind = pk(e)
            if kind == "resolve_blocker" and prevk.get(e.id) != "resolve_blocker":
                C["resolve_blocker_starts"] += 1
                act = [x for x in e.strategic.blockers.values() if not x.resolved and x.suppression_until_tick <= st.tick]
                if act and act[0].id == BID:
                    C["resolve_blocker_starts_for_readiness"] += 1
                    RB[e.id] = (st.tick, tuple(e.navigation.position))
            prevk[e.id] = kind
            if e.id in RB and st.tick - RB[e.id][0] == 5:
                C["rb_readiness.moved_5t" if tuple(e.navigation.position) != RB[e.id][1] else "rb_readiness.stayed_5t"] += 1
                C["rb_readiness.alive_5t" if e.combat.alive else "rb_readiness.dead_5t"] += 1
                del RB[e.id]
finally:
    k.shutdown()
for e in k.state.entities.values():
    b = e.strategic.blockers.get(BID)
    if b is not None and not b.resolved and e.id in open_ep: life.append(TICKS - open_ep[e.id])
C["open_blocker_lifetime_sum"] = sum(life); C["open_blocker_lifetime_max"] = max(life) if life else 0
C["unresolved_at_end"] = sum(1 for e in k.state.entities.values() if (b := e.strategic.blockers.get(BID)) is not None and not b.resolved)
print("RBTRACE", json.dumps(dict(world=WORLD, seed=SEED, label=LABEL, counts=dict(sorted(C.items())))))
