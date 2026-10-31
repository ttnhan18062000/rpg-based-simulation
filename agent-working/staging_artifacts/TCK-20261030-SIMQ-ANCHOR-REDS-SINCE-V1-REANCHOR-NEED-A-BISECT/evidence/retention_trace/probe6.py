"""Retention trace + width probe (scratch, read-only; pushable). Usage: PROBE_OUT=<jsonl> python probe6.py <world> <seed> <ticks>   (cwd = a commit tree, PYTHONPATH = that tree)
Runs the engine the way tools/evaluate_simq.py -> calibrate_simq does for an anchored key: tools.calibrate_simq._run_engine(world, seed, ticks, extra_flags=<profile flags of the same name>, audit_mode=True), without the quality-report replay.
Records (all read-only):
  pj  per entity, on change of (alive, current project id): tick, entity, alive, project id
  rh  per tick, per ALIVE entity whose current project id contains 'combat_retreat': hp, max hp, acting_threat_to (src/ai/goals/present_threat.py), adj (a perceived hostile orthogonally adjacent, decision 32), perceived count
  sel per strategic goal-selection call (ScoreModifierSystem.apply_modifiers) for an entity holding a retreat project: top-3 modified scores, the best_candidate the intelligence.py:1586-1593 filter yields (utility >= 20 and a target) or None, the head committed intention (kind, status)
  sw  per evaluate_project_switch call where the current project is a retreat project: candidate, candidate score, current score, lock_until, retention margin inputs, returned switch
  dead per DEAD entity (at its first dead tick, every 250 ticks, and at the last tick): current project id and the ids/kinds/status of its ACTIVE projects
  fin the final state_hash from run_manifest.json"""
import json, os, sys, shutil
sys.path.insert(0, ".")
OUT = open(os.environ["PROBE_OUT"], "w")
def log(**r): OUT.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from src.ai.goals.present_threat import acting_threat_to
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.legality import LegalityServiceV2
from src.ai.score_modifiers import ScoreModifierSystem as SM
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem as SI
from src.systems.world_systems.groups import GroupSystem
def holds_retreat(e): return "combat_retreat" in (e.strategic.current_project_id or "")
om = SM.apply_modifiers
import src.systems.strategic_systems.intelligence as I
cur = {"t": None, "e": None}
def am(entity, state, scores):
    res = om(entity, state, scores)
    cur["t"], cur["e"] = state.tick, entity.id
    if holds_retreat(entity):
        ms = sorted(res, key=lambda x: (-x.utility, x.kind))
        best = next((g for g in ms if not (g.utility < 20.0 or (g.target_id is None and g.target_pos is None))), None)
        ci = entity.strategic.committed_intentions
        ex = next((p for p in entity.strategic.projects.values() if best and p.kind == best.kind), None)
        log(k="ex", t=state.tick, e=entity.id, best_kind=str(best.kind) if best else None, existing=[ex.id, str(ex.status)] if ex else None,
            n_active=sum(1 for p in entity.strategic.projects.values() if "ACTIVE" in str(p.status)), max_active=entity.strategic.profile.max_active_projects)
        log(k="sel", t=state.tick, e=entity.id, top=[[str(g.kind), round(g.utility, 3), g.target_id] for g in ms[:3]],
            best=[str(best.kind), round(best.utility, 3), best.target_id] if best else None,
            ci=[ci[0].goal_kind, ci[0].status] if ci else None)
    return res
SM.apply_modifiers = staticmethod(am)
oe = SI.evaluate_project_switch
def ev(entity, candidate_project, current_tick, state=None):
    res = oe(entity, candidate_project, current_tick, state=state)
    cur = entity.strategic.projects.get(entity.strategic.current_project_id)
    if cur is not None and "combat_retreat" in cur.id:
        p = entity.strategic.profile
        log(k="sw", t=current_tick, e=entity.id, cand=candidate_project.id, cand_score=candidate_project.score, cur=cur.id, cur_status=str(cur.status), cur_score=cur.score,
            lock_until=cur.lock_until_tick, resist=p.interruption_resistance, mult=p.resistance_multiplier, switched=bool(res),
            set=(res.current_project_id_set if res else None))
    return res
SI.evaluate_project_switch = staticmethod(ev)
_hc, _en, _rs = I.has_project_capacity, I.escalated_need_wins, SI.resume_project
from src.core.strategic import is_live_project
def hc(projects, max_active):
    r = _hc(projects, max_active)
    if cur["e"] is not None and any("combat_retreat" in pid for pid, p in projects.items() if "ACTIVE" in str(p.status)): log(k="cap", t=cur["t"], e=cur["e"], has_capacity=bool(r), live=sum(1 for p in projects.values() if is_live_project(p)), max=max_active)
    return r
def en(entity, kind):
    r = _en(entity, kind)
    if holds_retreat(entity): log(k="esc", t=cur["t"], e=entity.id, kind=str(kind), escalated=bool(r))
    return r
def rs(entity, pid):
    r = _rs(entity, pid)
    if holds_retreat(entity): log(k="res", t=cur["t"], e=entity.id, pid=pid, resumed=bool(r))
    return r
I.has_project_capacity, I.escalated_need_wins = hc, en
SI.resume_project = staticmethod(rs)
prev = {}
og = GroupSystem.update_groups
def ug(state, current_update=None):
    t = state.tick
    for eid in sorted(state.entities):
        e = state.entities[eid]; st = e.strategic; pr = st.current_project_id or ""
        key = (bool(e.combat.alive), pr)
        if prev.get(eid) != key:
            prev[eid] = key; log(k="pj", t=t, e=eid, a=key[0], pr=pr)
        if e.combat.alive and "combat_retreat" in pr:
            hs = perceived_hostiles(e, state)
            adj = any(LegalityServiceV2.is_adjacent(e.navigation.position, h.navigation.position) for h in hs)
            log(k="rh", t=t, e=eid, pr=pr, hp=e.combat.hp, mh=e.combat.max_hp, acting=bool(acting_threat_to(e, state)), adj=bool(adj), perc=len(hs), p=e.navigation.position, wk=e.task.work_kind, act=(e.task.payload.get("action") if e.task.payload else None))
        if not e.combat.alive:
            first = prev.get(("dead", eid)) is None
            if first or t % 250 == 249 or t == ticks - 1:
                prev[("dead", eid)] = t
                act = [[pid, str(p.kind), str(p.status)] for pid, p in st.projects.items() if "ACTIVE" in str(p.status)]
                log(k="dead", t=t, e=eid, pr=pr, active=act, first=first)
    return og(state, current_update)
GroupSystem.update_groups = staticmethod(ug)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile(world))
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=True)
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
log(k="fin", state_hash=m["state_hash"], ticks=m["ticks_completed"], run_id=run_id, elapsed=elapsed, flags=flags)
OUT.close()
shutil.rmtree(run_dir)   # this run's own scratch run directory (about 100 MB); the manifest hash is kept in the log
