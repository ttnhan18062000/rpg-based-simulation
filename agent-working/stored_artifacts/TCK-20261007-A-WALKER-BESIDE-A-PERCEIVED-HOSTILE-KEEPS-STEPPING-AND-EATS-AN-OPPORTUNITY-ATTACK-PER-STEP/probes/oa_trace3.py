"""Opportunity-attack trace (read-only). usage: oa_trace.py <root> <world> <ticks> <seed> <label>
(a) after each held-move interrupt: the brain's decision and the entity's task/move over the next 5 ticks (fixed arm only);
(b) every opportunity-attack swing: how the victim was moving, its goal, and whether an adjacent hostile was known to strike."""
import collections, json, sys
ROOT, WORLD, TICKS, SEED, LABEL = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
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
from src.engine.movement import MovementSystem as MS
LASTMOVE = {}
_rm = MS.resolve_move
def rm(st, entity, target_pos, mode=None, *a, **kw):
    LASTMOVE[(entity.id, st.tick)] = dict(fresh=(tuple(target_pos) != (tuple(entity.navigation.target) if entity.navigation.target else None)),
                                         mode=str(mode).split(".")[-1], had_target=entity.navigation.target is not None)
    return _rm(st, entity, target_pos, mode, *a, **kw) if mode is not None else _rm(st, entity, target_pos, *a, **kw)
MS.resolve_move = staticmethod(rm)
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
C = collections.Counter(); DEC = {}; INT = []   # INT: (tick, entity id)
def label(d):
    if d is None: return "no_decision"
    return f"{d['action'] or 'move'}|{d['reason'] or '-'}|{(d['mode'] or '-').split('.')[-1]}"
_ev = T.evaluate_entity_intent
def ev(st, entity, *a, **kw):
    r = _ev(st, entity, *a, **kw)
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    nav = r.navigation if r is not None else None
    DEC[(entity.id, st.tick)] = dict(action=pl.get("action"), reason=pl.get("reason"), mode=str(getattr(nav, "movement_mode_set", None)))
    return r
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
def pkind(e):
    s = e.strategic; p = s.projects.get(s.current_project_id) if s.current_project_id else None
    return str(getattr(p.kind, "value", p.kind)) if p else None
_rma = CRS.resolve_multi_attack
def rma(attackers, target, c, is_opportunity_attack=False, **kw):
    r = _rma(attackers, target, c, is_opportunity_attack=is_opportunity_attack, **kw)
    if is_opportunity_attack and getattr(r, "hp_delta", 0) and r.hp_delta < 0:
        tick = getattr(c, "tick", k.state.tick)
        C["oa_hits"] += 1
        d = DEC.get((target.id, tick))
        if d is not None: how = "decided_this_tick"
        elif target.task.work_kind == "ENTITY_MOVE": how = "held_move"
        else: how = "neither_decided_nor_held"
        C[f"hit.how.{how}"] += 1
        C[f"hit.how.{how}.goal.{pkind(target)}"] += 1
        if how == "neither_decided_nor_held":
            lm = LASTMOVE.get((target.id, tick))
            C[f"neither.move_source.{'fresh_target_this_tick' if (lm and lm['fresh']) else ('leftover_navigation_target' if lm else 'no_resolve_move_record')}"] += 1
            C[f"neither.payload_action.{target.task.payload.get('action')}|{target.task.payload.get('reason')}"] += 1
            C[f"neither.task.{target.task.work_kind}|payload_empty={not target.task.payload}|mode={str(target.navigation.movement_mode).split('.')[-1]}|has_nav_target={target.navigation.target is not None}"] += 1
        if how == "decided_this_tick": C[f"hit.decided.{label(d)}"] += 1
        elif how == "held_move": C[f"hit.held.{target.task.payload.get('reason')}|{str(target.navigation.movement_mode).split('.')[-1]}"] += 1
        # adjacent attackers known to strike: within one tile and their own task is an ATTACK at the victim
        adj = [a for a in attackers if abs(a.navigation.position[0]-target.navigation.position[0]) + abs(a.navigation.position[1]-target.navigation.position[1]) <= 1]
        striking = [a for a in adj if a.task.payload.get("action") == "ATTACK" and a.task.payload.get("target_id") == target.id]
        C["hit.attackers_adjacent" if adj else "hit.attackers_not_adjacent"] += 1
        C["hit.attacker_has_attack_task_on_victim" if striking else "hit.attacker_has_no_attack_task_on_victim"] += 1
    return r
CRS.resolve_multi_attack = staticmethod(rma)
HIST = collections.defaultdict(dict)
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for e in st.entities.values():
            HIST[e.id][st.tick] = (tuple(e.navigation.position), e.task.work_kind, str(e.navigation.movement_mode).split(".")[-1], pkind(e))
finally:
    k.shutdown()
for (t0, eid) in INT:
    C["interrupts"] += 1
    base = HIST[eid].get(t0)
    for dt in range(1, 6):
        d = DEC.get((eid, t0 + dt)); nxt = HIST[eid].get(t0 + dt)
        C[f"after_interrupt.decision.{label(d)}"] += 1
        if nxt is not None:
            C[f"after_interrupt.task.{nxt[1]}|{nxt[2]}"] += 1
            C[f"after_interrupt.goal.{nxt[3]}"] += 1
            if base is not None and nxt[0] != base[0]: C["after_interrupt.entity_moved_tiles"] += 1
            else: C["after_interrupt.entity_stayed"] += 1
print("OATRACE", json.dumps(dict(world=WORLD, seed=SEED, label=LABEL, counts=dict(sorted(C.items())))))
