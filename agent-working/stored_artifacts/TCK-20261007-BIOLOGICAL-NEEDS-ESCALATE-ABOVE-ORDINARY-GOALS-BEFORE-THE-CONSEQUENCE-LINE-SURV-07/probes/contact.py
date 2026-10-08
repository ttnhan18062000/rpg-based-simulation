"""Read-only tactical-contact trace. usage: contact.py <root> <world> <ticks> <seed> <id,id,...>
For the named entities, the last 30 ticks before death: hp, project, who is adjacent / targeting, whether perceived, the tactical decision."""
import collections, json, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); IDS = {int(x) for x in sys.argv[5].split(",")}
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.behavior_consumers import get_entity_signals, get_perception_gate, get_pressure_resolver
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.engine.tactical_threat import present_threat_terms, safety_retreat_warranted, CAUTIOUS_SAFETY_PRESSURE
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
DEC = collections.defaultdict(dict)
_ev = T.evaluate_entity_intent
def ev(st, entity, *a, **kw):
    r = _ev(st, entity, *a, **kw)
    if entity.id in IDS:
        pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
        nav = r.navigation if r is not None else None
        DEC[entity.id][st.tick] = dict(action=pl.get("action"), reason=pl.get("reason"), mode=str(getattr(nav, "movement_mode_set", None)),
                                      tgt=pl.get("target_id"), clear=bool(getattr(nav, "target_clear", False)) if nav else False)
    return r
T.evaluate_entity_intent = staticmethod(ev)
HIST = collections.defaultdict(list); DEAD = {}
gate = get_perception_gate()
def man(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for eid in IDS:
            e = st.entities.get(eid)
            if e is None or eid in DEAD: continue
            if not (e.combat.alive and e.lifecycle.active):
                DEAD[eid] = st.tick; continue
            s = e.strategic; p = s.projects.get(s.current_project_id) if s.current_project_id else None
            near = []
            for o in st.entities.values():
                if o.id == eid or not (o.combat.alive and o.lifecycle.active): continue
                d = man(o.navigation.position, e.navigation.position)
                if d > 3 and o.task.payload.get("target_id") != eid: continue
                try: perceived = bool(gate.can_perceive(e, get_entity_signals(o), {"distance": float(d)}).perceived)
                except Exception as ex: perceived = None
                near.append(dict(id=o.id, kind=o.kind, d=d, targets_me=o.task.payload.get("target_id") == eid, act=o.task.payload.get("action"), perceived=perceived, hp=round(o.combat.hp, 1)))
            try: sp = get_pressure_resolver().resolve_pressures(e).safety_pressure
            except Exception: sp = None
            HIST[eid].append(dict(t=st.tick, pos=e.navigation.position, hp=round(e.combat.hp, 1), maxhp=e.combat.max_hp, readiness=round(e.combat.readiness, 1),
                                  proj=str(getattr(p.kind, "value", p.kind)) if p else None, mode=str(e.navigation.movement_mode), safety=sp, near=near,
                                  dec=DEC[eid].get(st.tick), threat=[t.value for t in present_threat_terms(e, [])] if False else None))
finally:
    k.shutdown()
for eid in sorted(IDS):
    h = HIST[eid][-30:]
    print("CONTACT-ENTITY", eid, "died", DEAD.get(eid), "kind", st.entities.get(eid).kind if st.entities.get(eid) else "?")
    for r in h:
        print("  ", json.dumps(r, default=str))
