"""Unengaged-adjacency episodes (read-only). usage: notice_eps.py <root> <world> <ticks> <seed>"""
import collections, json, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.candidate_selector import MovementCandidateSelector as MCS
from src.engine.combat import CombatResolutionSystem as CRS
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.hostility import is_engaged, perceived_hostile
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
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
C = collections.Counter(); DECS = collections.defaultdict(list); OA = collections.defaultdict(list)
_ev = T.evaluate_entity_intent
def ev(st, entity, *a, **kw):
    r = _ev(st, entity, *a, **kw); C["brain_decisions"] += 1
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    cls = (pl.get("action") or pl.get("reason") or ("move" if r is not None and r.task is not None else "none"))
    DECS[entity.id].append((st.tick, str(cls))); return r
T.evaluate_entity_intent = staticmethod(ev)
_rma = CRS.resolve_multi_attack
def rma(attackers, target, c, is_opportunity_attack=False, **kw):
    r = _rma(attackers, target, c, is_opportunity_attack=is_opportunity_attack, **kw)
    if is_opportunity_attack and getattr(r, "hp_delta", 0) and r.hp_delta < 0: OA[target.id].append(k.state.tick)
    return r
CRS.resolve_multi_attack = staticmethod(rma)
EPS = []; OPEN = {}; POS = collections.defaultdict(dict)
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state; t = st.tick
        idx = MCS.position_index(st.entities)
        adj_now = set()
        for e in st.entities.values():
            POS[e.id][t] = tuple(e.navigation.position)
            if not (e.combat.alive and e.lifecycle.active): continue
            x, y = int(e.navigation.position[0]), int(e.navigation.position[1])
            for tile in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                for oid in idx.get(tile, ()):
                    o = st.entities.get(oid)
                    if o is not None and o.id != e.id and not is_engaged(e, o) and perceived_hostile(e, o):
                        adj_now.add(e.id); break
                if e.id in adj_now: break
        for eid in adj_now:
            if eid not in OPEN: OPEN[eid] = t
        for eid in list(OPEN):
            if eid not in adj_now:
                EPS.append((eid, OPEN.pop(eid), t - 1))
finally:
    k.shutdown()
for eid, s in OPEN.items(): EPS.append((eid, s, TICKS))
lat = []; steps_before = 0; oa_before = 0; first_cls = collections.Counter(); undecided = 0; eplen = []
for eid, s, e in EPS:
    eplen.append(e - s + 1)
    ds = [d for d in DECS.get(eid, []) if d[0] >= s]
    first = ds[0] if ds else None
    end_dec = first[0] if first and first[0] <= e + 0 else None
    if first is None or first[0] > e: undecided += 1
    L = (first[0] - s) if first else None
    if first is not None and first[0] <= e:
        lat.append(L); first_cls[first[1]] += 1
        pl = POS[eid]; steps_before += sum(1 for t in range(s + 1, first[0] + 1) if pl.get(t) != pl.get(t - 1))
        oa_before += sum(1 for t in OA.get(eid, []) if s <= t <= first[0])
lat.sort()
def pct(p): return lat[min(len(lat) - 1, int(p * len(lat)))] if lat else None
out = dict(world=WORLD, seed=SEED, episodes=len(EPS), entity_ticks=sum(eplen), mean_len=(sum(eplen)/len(eplen) if eplen else 0), max_len=max(eplen) if eplen else 0,
           decided_within_episode=len(lat), ended_without_a_decision=undecided, lat_mean=(sum(lat)/len(lat) if lat else None), lat_p50=pct(0.5), lat_p90=pct(0.9), lat_max=(lat[-1] if lat else None),
           steps_before_first_decision=steps_before, oa_before_first_decision=oa_before, first_decision_class=dict(first_cls.most_common(8)), brain_decisions=C["brain_decisions"])
print("NOTICE", json.dumps(out))
