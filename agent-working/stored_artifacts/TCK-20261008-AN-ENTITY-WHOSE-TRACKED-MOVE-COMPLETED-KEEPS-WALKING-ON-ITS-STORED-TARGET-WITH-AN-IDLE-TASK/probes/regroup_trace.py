"""Held-REGROUP death trace (read-only). usage: regroup_trace.py <root> <world> <ticks> <seed>"""
import collections, json, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.combat import CombatResolutionSystem as CRS
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
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
DEC = collections.defaultdict(list)     # eid -> [(tick, reason, action)]
_ev = T.evaluate_entity_intent
def ev(st, entity, *a, **kw):
    r = _ev(st, entity, *a, **kw)
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    if r is not None and r.task is not None: DEC[entity.id].append((st.tick, pl.get("reason"), pl.get("action")))
    return r
T.evaluate_entity_intent = staticmethod(ev)
HITS = collections.defaultdict(list)    # victim -> [dict]
POS = collections.defaultdict(dict)     # eid -> tick -> pos
_rma = CRS.resolve_multi_attack
def rma(attackers, target, c, is_opportunity_attack=False, **kw):
    r = _rma(attackers, target, c, is_opportunity_attack=is_opportunity_attack, **kw)
    if getattr(r, "hp_delta", 0) and r.hp_delta < 0:
        tick = k.state.tick
        d = [x for x in DEC[target.id] if x[0] <= tick]
        HITS[target.id].append(dict(tick=tick, oa=bool(is_opportunity_attack), attackers=[a.id for a in attackers],
            apos=[tuple(a.navigation.position) for a in attackers], vpos=tuple(target.navigation.position),
            task=target.task.work_kind, reason=(target.task.payload or {}).get("reason"), mode=str(target.navigation.movement_mode).split(".")[-1],
            last_dec=d[-1] if d else None, hp_delta=r.hp_delta))
    return r
CRS.resolve_multi_attack = staticmethod(rma)
DEAD = {}
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for e in st.entities.values():
            POS[e.id][st.tick] = tuple(e.navigation.position)
            if e.id not in DEAD and not (e.combat.alive and e.lifecycle.active):
                c = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                DEAD[e.id] = (st.tick, str(getattr(c, 'value', c)), e.identity.faction.name if hasattr(e.identity.faction,'name') else str(e.identity.faction))
finally:
    k.shutdown()
out = []
for eid, (dt, cause, fac) in DEAD.items():
    hits = HITS.get(eid, [])
    last = hits[-1] if hits else None
    decs = [x for x in DEC[eid] if x[0] <= dt]
    reg = [x for x in decs if x[1] == "REGROUP"]
    rec = dict(eid=eid, death_tick=dt, cause=cause, faction=fac, n_hits=len(hits), last_hit=last)
    if last:
        # steps taken while the killing attacker was within 6 tiles, from the first such tick back-to-forward
        att = last["attackers"][0]
        near = [t for t in range(max(1, dt - 40), dt + 1) if t in POS[eid] and t in POS[att]
                and abs(POS[eid][t][0]-POS[att][t][0]) + abs(POS[eid][t][1]-POS[att][t][1]) <= 6]
        rec["near6_first_tick"] = near[0] if near else None
        steps = sum(1 for t in range(near[0]+1, dt+1) if POS[eid].get(t) != POS[eid].get(t-1)) if near else None
        rec["steps_while_attacker_within6"] = steps
        rec["hits_in_last40"] = sum(1 for h in hits if h["tick"] >= dt - 40)
        rec["oa_hits_in_last40"] = sum(1 for h in hits if h["tick"] >= dt - 40 and h["oa"])
    rec["last_regroup_dec_tick"] = reg[-1][0] if reg else None
    rec["last_dec"] = decs[-1] if decs else None
    out.append(rec)
print("RGTRACE", json.dumps(dict(world=WORLD, seed=SEED, deaths=out), default=str))
