"""Death trace. usage: death_trace.py <root> <world> <ticks> [seed]
For every entity that dies: cause, project kind and flags at the death tick and over the previous 20 ticks."""
import collections, json, sys
ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3]); SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 42
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical_threat import present_threat_terms
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
HIST = collections.defaultdict(lambda: collections.deque(maxlen=21))
DEAD = {}; PROJ_TICKS = collections.Counter(); ALIVE = {}
def snap(st, e):
    strat = e.strategic
    pk = None
    if strat.current_project_id:
        p = strat.projects.get(strat.current_project_id); pk = str(getattr(p.kind, "value", p.kind)) if p else None
    near = [o for o in st.entities.values() if o.id != e.id and o.combat.alive and o.lifecycle.active
            and o.identity.faction != e.identity.faction and abs(o.navigation.position[0]-e.navigation.position[0]) + abs(o.navigation.position[1]-e.navigation.position[1]) <= 10]
    threat = [t.value for t in present_threat_terms(e, near)] if near else []
    return dict(t=st.tick, proj=pk, pos=tuple(e.navigation.position), tgt=(tuple(e.navigation.target) if e.navigation.target else None),
                hp=round(e.combat.hp, 1), hu=round(e.biological.hunger, 1), sd=round(e.biological.sleep_debt, 1),
                hostile10=len(near), threat=threat, need_hot=(e.biological.hunger / 95.0 >= 0.6 or e.biological.sleep_debt / 98.0 >= 0.6))
try:
    for _ in range(TICKS):
        k.tick_once()
        st = k.state
        for e in st.entities.values():
            if e.id in DEAD: continue
            if e.combat.alive and e.lifecycle.active:
                s = snap(st, e); HIST[e.id].append(s); PROJ_TICKS[s["proj"]] += 1
                if st.tick in (1000, 1100): ALIVE.setdefault(st.tick, []).append(e.id)
            else:
                cause = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                DEAD[e.id] = dict(id=e.id, kind=e.kind, tick=st.tick, cause=str(getattr(cause, "value", cause)), last=list(HIST[e.id])[-1] if HIST[e.id] else None,
                                  proj_hist=collections.Counter(h["proj"] for h in HIST[e.id]), threat_ticks=sum(1 for h in HIST[e.id] if h["threat"]),
                                  hostile_ticks=sum(1 for h in HIST[e.id] if h["hostile10"]), need_hot_ticks=sum(1 for h in HIST[e.id] if h["need_hot"]))
finally:
    k.shutdown()
bycause = collections.Counter(d["cause"] for d in DEAD.values())
print("TOTAL", WORLD, json.dumps(dict(deaths=len(DEAD), by_cause=dict(bycause), alive_t1000=len(ALIVE.get(1000, [])), alive_t1100=len(ALIVE.get(1100, [])))))
print("PROJ_ENTITY_TICKS", json.dumps({str(a): b for a, b in PROJ_TICKS.most_common()}))
agg = collections.Counter()
for d in DEAD.values():
    l = d["last"] or {}
    key = d["cause"]
    agg[f"{key}|proj={l.get('proj')}"] += 1
    agg[f"{key}|threat_at_death={bool(l.get('threat'))}"] += 1
    agg[f"{key}|hostile10_at_death={bool(l.get('hostile10'))}"] += 1
    agg[f"{key}|need_hot_at_death={l.get('need_hot')}"] += 1
    agg[f"{key}|need_hot_any_last20={d['need_hot_ticks'] > 0}"] += 1
print("DEATH_AGG", json.dumps(dict(sorted(agg.items()))))
for d in sorted(DEAD.values(), key=lambda x: x["tick"]):
    l = d["last"] or {}
    print("DEATH", json.dumps(dict(id=d["id"], kind=d["kind"], t=d["tick"], cause=d["cause"], proj=l.get("proj"), tgt=l.get("tgt"), pos=l.get("pos"), hp=l.get("hp"), hu=l.get("hu"), sd=l.get("sd"),
        threat=l.get("threat"), hostile10=l.get("hostile10"), hot=l.get("need_hot"), proj_last20=dict(d["proj_hist"]), threat_ticks20=d["threat_ticks"], hostile_ticks20=d["hostile_ticks"], hot_ticks20=d["need_hot_ticks"])))
