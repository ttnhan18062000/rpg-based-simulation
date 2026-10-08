"""Per-entity trace of DEFEAT deaths in the hunger project. usage: hunger_defeats.py <root> <world> <ticks> [seed]"""
import collections, json, sys
ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3]); SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 42
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.engine.tactical_threat import present_threat_terms
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
TAC = collections.defaultdict(lambda: collections.deque(maxlen=25))
_ev = T.evaluate_entity_intent
def ev(st, entity, *a, **kw):
    r = _ev(st, entity, *a, **kw)
    d = None
    if r is not None:
        pl = (r.task.payload_set or {}) if r.task is not None else {}
        nav = r.navigation
        d = (st.tick, pl.get("action"), pl.get("reason"), str(getattr(nav, "movement_mode_set", None)) if nav else None, bool(getattr(nav, "target_clear", False)) if nav else False)
    TAC[entity.id].append(d if d else (st.tick, None, None, None, False))
    return r
T.evaluate_entity_intent = staticmethod(ev)
def pkind(e):
    s = e.strategic
    p = s.projects.get(s.current_project_id) if s.current_project_id else None
    return str(getattr(p.kind, "value", p.kind)) if p else None
def man(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
def path_tiles(a, b):
    x, y = int(a[0]), int(a[1]); out = []
    while (x, y) != (int(b[0]), int(b[1])) and len(out) < 400:
        if abs(b[0]-x) > abs(b[1]-y): x += 1 if b[0] > x else -1
        else: y += 1 if b[1] > y else -1
        out.append((x, y))
    return out
RUN = {}; DEAD = {}; HIST = collections.defaultdict(lambda: collections.deque(maxlen=21)); inns = None
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        if inns is None: inns = [b.position for b in st.buildings.values() if b.kind == "inn"]
        for e in st.entities.values():
            if e.id in DEAD: continue
            if e.combat.alive and e.lifecycle.active:
                pk = pkind(e)
                if pk == "hunger":
                    if e.id not in RUN:
                        inn = min(inns, key=lambda p: man(p, e.navigation.position)) if inns else None
                        pt = path_tiles(e.navigation.position, inn) if inn else []
                        foes = [o for o in st.entities.values() if o.id != e.id and o.combat.alive and o.lifecycle.active and o.identity.faction != e.identity.faction]
                        near_start = [o for o in foes if man(o.navigation.position, e.navigation.position) <= 10]
                        near_path = [o.id for o in foes if any(abs(o.navigation.position[0]-x) + abs(o.navigation.position[1]-y) <= 3 for x, y in pt[::2])]
                        RUN[e.id] = dict(t0=st.tick, pos0=tuple(e.navigation.position), inn=inn, path_len=len(pt), foes_within10_at_start=len(near_start),
                                         foes_within3_of_path_at_start=len(near_path), gold0=e.inventory.gold, hp0=e.combat.hp, hunger0=round(e.biological.hunger, 1))
                else:
                    RUN.pop(e.id, None)
                HIST[e.id].append((st.tick, pk, tuple(e.navigation.position), round(e.combat.hp, 1), e.inventory.gold))
            else:
                c = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                DEAD[e.id] = (st.tick, str(getattr(c, "value", c)), list(HIST[e.id]), dict(RUN.get(e.id, {})), list(TAC[e.id]))
finally:
    k.shutdown()
for eid, (t, cause, hist, run, tac) in sorted(DEAD.items(), key=lambda kv: kv[1][0]):
    if cause != "DEFEAT" or not hist or hist[-1][1] != "hunger": continue
    last = hist[-1]
    acts = collections.Counter((a[1], a[2], a[3]) for a in tac[-20:])
    print("HUNGER-DEFEAT", json.dumps(dict(id=eid, t_death=t, run=run, gold_at_death=last[4], hp_at_death=last[3], pos_at_death=last[2],
          ticks_in_hunger_before_death=t - run.get("t0", t), tactical_last20=[[list(k), v] for k, v in acts.most_common()],
          path_last10=[h[2] for h in hist[-10:]])))
print("DONE", WORLD, SEED, "hunger-defeats:", sum(1 for _, (t, c, h, r, ta) in DEAD.items() if c == "DEFEAT" and h and h[-1][1] == "hunger"), "of", sum(1 for _, v in DEAD.items() if v[1] == "DEFEAT"))
