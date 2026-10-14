"""Opportunity-attack hit classification (read-only). usage: arm_probe.py <root> <world> <ticks> <seed> <arm: base|engaged|any>"""
import collections, json, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ARM = sys.argv[5]
TRACE = set()
import time
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.candidate_selector import MovementCandidateSelector as MCS
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
BLOCK = {}   # (eid, tick) -> engaged flag
TCLS = {}
MEMO = {}
if ARM in ("engaged", "any"):
    from src.engine.hostility import is_engaged, perceived_hostile
    _eah = MCS.engaged_adjacent_hostile
    def eah(entity, entities, index=None):
        if ARM == "engaged":
            r = _eah(entity, entities, index)
            if r:
                BLOCK[(entity.id, k.state.tick)] = True
                pl = entity.task.payload or {}
                TCLS[(entity.id, k.state.tick)] = (entity.task.work_kind, 'queued_attack' if pl.get('action') == 'ATTACK' else ('hold_between_blows' if pl.get('reason') == 'HOLD_BETWEEN_BLOWS' else (pl.get('reason') or pl.get('action') or 'empty_payload')))
            return r
        if index is None: index = MCS.position_index(entities)
        x, y = int(entity.navigation.position[0]), int(entity.navigation.position[1])
        eng = False; hit = False
        for tile in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            for oid in index.get(tile, ()):
                o = entities.get(oid)
                if o is not None and o.id != entity.id and perceived_hostile(entity, o):
                    hit = True; eng = eng or is_engaged(entity, o)
        if hit: BLOCK[(entity.id, k.state.tick)] = eng
        return hit
    MCS.engaged_adjacent_hostile = staticmethod(eah)
from src.engine.movement import MovementSystem as MS
_rm = MS.resolve_move
RM = [0]
def rm(*a, **kw):
    RM[0] += 1; return _rm(*a, **kw)
MS.resolve_move = staticmethod(rm)
LASTHIT = {}
C = collections.Counter(); DEC = {}; LASTDEC = {}; MT = {}; HIST = collections.defaultdict(list); MODE_SET = {}
SAMPLES = []
_ev = T.evaluate_entity_intent
def ev(st, entity, *a, **kw):
    r = _ev(st, entity, *a, **kw)
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    nav = r.navigation if r is not None else None
    d = dict(tick=st.tick, kind=pl.get("action") or ("move" if r is not None and r.task is not None else "none"), reason=pl.get("reason"),
             mode=str(getattr(nav, "movement_mode_set", None)).split(".")[-1], wk=getattr(getattr(r, "task", None), "work_kind_set", None))
    DEC[(entity.id, st.tick)] = d; LASTDEC[entity.id] = d
    if r is not None and getattr(nav, "movement_mode_set", None) is not None: MODE_SET[entity.id] = (st.tick, "tactical", d["reason"] or d["kind"])
    return r
T.evaluate_entity_intent = staticmethod(ev)
if hasattr(MCS, 'movement_target'):
    _mt = MCS.movement_target
    def mt(entity, ent_upd, entities, *rest):
        r = _mt(entity, ent_upd, entities, *rest)
        nav = ent_upd.navigation if ent_upd else None
        fresh = bool(nav and nav.target_set is not None)
        fields = sorted(f for f in ("task", "strategic", "navigation", "new_position") if ent_upd is not None and getattr(ent_upd, f, None) is not None)
        MT[(entity.id, k.state.tick)] = dict(fresh=fresh, mode_set=bool(nav and nav.movement_mode_set is not None), result=r is not None,
                                             stored_target=entity.navigation.target is not None, upd_fields=fields,
                                             upd_task=(ent_upd.task.work_kind_set if ent_upd and ent_upd.task else None))
        return r
    MCS.movement_target = staticmethod(mt)
POS = collections.defaultdict(dict)
_rma = CRS.resolve_multi_attack
def rma(attackers, target, c, is_opportunity_attack=False, **kw):
    r = _rma(attackers, target, c, is_opportunity_attack=is_opportunity_attack, **kw)
    if is_opportunity_attack and getattr(r, "hp_delta", 0) and r.hp_delta < 0:
        tick = getattr(c, "tick", k.state.tick)
        d = DEC.get((target.id, tick)); m = MT.get((target.id, tick)); wk = target.task.work_kind; pl = target.task.payload or {}
        if d is not None: cls = "decided_this_tick:" + str(d["reason"] or d["kind"])
        elif wk == "ENTITY_MOVE": cls = "held_move:" + str(pl.get("reason") or "none")
        elif wk == "ENTITY_ACT": cls = "act_holder:" + str(pl.get("action"))
        else: cls = "other:" + str(wk)
        top = cls.split(":")[0]
        LASTHIT[target.id] = cls
        try:
            from src.engine.hostility import is_engaged, perceived_hostile
            from src.engine.legality import LegalityServiceV2 as L
            v0 = k.state.entities.get(target.id)
            for a in attackers:
                a0 = k.state.entities.get(a.id)
                if v0 is None or a0 is None: continue
                adj = L.is_adjacent(v0.navigation.position, a0.navigation.position)
                C[f"rem.{top}.adjacent_at_start={adj}|engaged={is_engaged(v0, a0)}|perceived_hostile={perceived_hostile(v0, a0)}"] += 1
        except Exception as ex:
            C["rem.probe_error"] += 1
        C["hits"] += 1; C["cls." + top] += 1; C["cls." + cls] += 1
        if top in ("act_holder", "other"):
            ld = LASTDEC.get(target.id)
            C[f"{top}.fresh_target_update={m['fresh'] if m else None}"] += 1
            C[f"{top}.mode_set_same_tick={m['mode_set'] if m else None}"] += 1
            C[f"{top}.stored_target_present={m['stored_target'] if m else None}"] += 1
            C[f"{top}.mode={str(target.navigation.movement_mode).split('.')[-1]}"] += 1
            C[f"{top}.upd_fields={','.join(m['upd_fields']) if m else None}|task={m['upd_task'] if m else None}"] += 1
            C[f"{top}.has_tactical_decision_this_tick={d is not None}"] += 1
            ring = list(RING[target.id]); trans = None
            for i in range(len(ring) - 1, 0, -1):
                if not (ring[i][1] == 'ENTITY_ACT' and not ring[i][2]): continue
                if not (ring[i-1][1] == 'ENTITY_ACT' and not ring[i-1][2]):
                    trans = (ring[i-1], ring[i]); break
            if trans:
                p, n = trans
                C[f"idle_transition.from={p[1]}:{p[3]}|target_after={n[5]}|mode_after={n[4]}"] += 1
                C["idle_age_bucket." + ('0-9' if tick - n[0] < 10 else '10-19' if tick - n[0] < 20 else '20+')] += 1
            else:
                C["idle_transition.none_in_ring"] += 1
            if len(SAMPLES) < 40:
                SAMPLES.append(dict(tick=tick, victim=target.id, cls=cls, mode=str(target.navigation.movement_mode), mt=m, last_dec=ld,
                                    mode_set_by=MODE_SET.get(target.id), payload=dict(pl)))
    return r
CRS.resolve_multi_attack = staticmethod(rma)
prevmode = {}
T0 = time.perf_counter()
RING = collections.defaultdict(lambda: collections.deque(maxlen=40))
DEAD = {}
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for e in st.entities.values():
            md = str(e.navigation.movement_mode).split(".")[-1]
            if prevmode.get(e.id) != md and e.id not in MODE_SET or (prevmode.get(e.id) != md and MODE_SET.get(e.id, (0,))[0] != st.tick):
                MODE_SET[e.id] = (st.tick, "non_tactical_or_other", None)
            prevmode[e.id] = md
            RING[e.id].append((st.tick, e.task.work_kind, bool(e.task.payload), (e.task.payload or {}).get('reason') or (e.task.payload or {}).get('action'), md, e.navigation.target is not None))
            if e.id in TRACE:
                HIST[e.id].append((st.tick, e.task.work_kind, (e.task.payload or {}).get("action"), (e.task.payload or {}).get("reason"), md,
                                   e.navigation.target, tuple(e.navigation.position), e.combat.alive))
            if e.id not in DEAD and not (e.combat.alive and e.lifecycle.active):
                DEAD[e.id] = st.tick
                cz = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                C['death.' + str(getattr(cz, 'value', cz))] += 1
                C['death.%s.last_hit=%s' % (str(getattr(cz, 'value', cz)), LASTHIT.get(e.id))] += 1
            if st.tick in (1000, 1100) and e.combat.alive and e.lifecycle.active: C['alive_t%d' % st.tick] += 1
finally:
    k.shutdown()
WALL = time.perf_counter() - T0
C['deaths'] = len(DEAD); C['resolve_move_calls'] = RM[0]
per = collections.defaultdict(list)
for (eid, t), eng in BLOCK.items(): per[eid].append((t, eng))
longest = 0; total = 0; total_unengaged = 0
for eid, lst in per.items():
    lst.sort(); run = 1; best = 1
    for i in range(1, len(lst)):
        run = run + 1 if lst[i][0] == lst[i-1][0] + 1 else 1; best = max(best, run)
    longest = max(longest, best); total += len(lst); total_unengaged += sum(1 for _, e in lst if not e)
C['blocked_entity_ticks'] = total; C['blocked_entity_ticks_unengaged_only'] = total_unengaged; C['longest_block_run'] = longest
C['wall_seconds_x100'] = int(WALL * 100)
byc = collections.defaultdict(list)
for (eid, t), cl in TCLS.items(): byc[cl].append((eid, t))
for cl, lst in byc.items():
    C['blocked_ticks.%s|%s' % cl] = len(lst)
    perent = collections.defaultdict(list)
    for eid, t in lst: perent[eid].append(t)
    best = 0
    for eid, ts in perent.items():
        ts.sort(); run = 1; b = 1
        for i in range(1, len(ts)):
            run = run + 1 if ts[i] == ts[i-1] + 1 else 1; b = max(b, run)
        best = max(best, b)
    C['longest_run.%s|%s' % cl] = best
out = dict(world=WORLD, seed=SEED, arm=ARM, counts=dict(sorted(C.items())), samples=[])
if TRACE:
    tr = {}
    for eid in TRACE:
        dt = DEAD.get(eid)
        decs = sorted((v["tick"], v["kind"], v["reason"], v["wk"]) for (i, t), v in DEC.items() if i == eid and (dt is None or t <= dt))
        pr = [d for d in decs if d[2] == "PANIC_RETREAT"]
        tr[eid] = dict(death=dt, decisions_last=decs[-8:], hist=[h for h in HIST[eid] if dt is not None and dt - 25 <= h[0] <= dt])
    out["trace"] = tr
print("ARMPROBE", json.dumps(out, default=str))
