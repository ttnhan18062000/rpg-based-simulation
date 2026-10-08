"""OA instrumentation (read-only). usage: oa_instr.py <root> <world> <ticks> <seed>
(a) what MovementSystem.resolve_move does for an entity holding an ATTACK task whose live target is adjacent;
(b) per held-move interrupt: for the next five ticks, what the scheduler scheduled for the entity, whether execute_brain ran and whether it called the tactical pass."""
import collections, json, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.combat import CombatResolutionSystem as CRS
from src.engine.domain.cognition import CognitionDomain
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.movement import MovementSystem as MS
from src.engine.scheduler import DeterministicScheduler
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
C = collections.Counter(); INT = []; SCHED = {}; SNAP = {}; BRAIN = {}; EVAL = set()
_sel = DeterministicScheduler.select_work
def sel(self, st, policy=None):
    items, dropped = _sel(self, st, policy)
    for it in items:
        if isinstance(it.owner_id, int): SCHED[(st.tick, it.owner_id)] = it.work_kind
    for e in st.entities.values():
        SNAP[(st.tick, e.id)] = (e.task.work_kind, bool(e.task.payload), round(e.combat.readiness, 1), e.lifecycle.active)
    return items, dropped
DeterministicScheduler.select_work = sel
_eb = CognitionDomain.execute_brain
def eb(st, entity, force=False):
    r = _eb(st, entity, force)
    BRAIN[(st.tick, entity.id)] = True
    return r
CognitionDomain.execute_brain = staticmethod(eb)
_ev = T.evaluate_entity_intent
def ev(st, entity, *a, **kw):
    EVAL.add((st.tick, entity.id)); return _ev(st, entity, *a, **kw)
T.evaluate_entity_intent = staticmethod(ev)
try:
    import src.engine.executor as EX
    _h = EX.held_move_interrupted_by_threat
    def h(entity, neighbors):
        r = _h(entity, neighbors)
        if r: INT.append((k.state.tick, entity.id))
        return r
    EX.held_move_interrupted_by_threat = h
except AttributeError:
    pass
CUR = {"oa": 0}
_rma = CRS.resolve_multi_attack
def rma(attackers, target, c, is_opportunity_attack=False, **kw):
    if is_opportunity_attack: CUR["oa"] += 1
    return _rma(attackers, target, c, is_opportunity_attack=is_opportunity_attack, **kw)
CRS.resolve_multi_attack = staticmethod(rma)
def man(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
_rm = MS.resolve_move
def rm(st, entity, target_pos, mode=None, *a, **kw):
    before = CUR["oa"]
    out = _rm(st, entity, target_pos, mode, *a, **kw) if mode is not None else _rm(st, entity, target_pos, *a, **kw)
    tid = entity.task.payload.get("target_id")
    if entity.task.payload.get("action") == "ATTACK" and tid in st.entities:
        tgt = st.entities[tid]
        adj = man(tgt.navigation.position, entity.navigation.position) <= 1
        upd = out.get(entity.id)
        moved = upd is not None and upd.new_position is not None and tuple(upd.new_position) != tuple(entity.navigation.position)
        fr = getattr(upd.navigation, "failure_reason", None) if upd is not None and upd.navigation is not None else None
        key = f"attack_task.target_adjacent={adj}|moved={moved}|oa_swing={CUR['oa'] > before}|failure={fr}"
        C[key] += 1
        C["attack_task.resolve_move_calls"] += 1
    return out
MS.resolve_move = staticmethod(rm)
try:
    for _ in range(TICKS): k.tick_once()
finally:
    k.shutdown()
for (t0, eid) in INT:
    C["interrupts"] += 1
    for dt in range(1, 6):
        t = t0 + dt
        sk = SCHED.get((t, eid), "not_scheduled")
        snap = SNAP.get((t, eid))
        brain = (t, eid) in BRAIN; ev_ = (t, eid) in EVAL
        why = ""
        if sk == "not_scheduled" and snap is not None:
            why = f"|task={snap[0]}|payload_nonempty={snap[1]}|readiness_ge_100={snap[2] >= 100.0}|active={snap[3]}"
        C[f"after_interrupt.scheduled={sk}|brain_executed={brain}|tactical_called={ev_}{why}"] += 1
print("OAINSTR", json.dumps(dict(world=WORLD, seed=SEED, counts=dict(sorted(C.items())))))
