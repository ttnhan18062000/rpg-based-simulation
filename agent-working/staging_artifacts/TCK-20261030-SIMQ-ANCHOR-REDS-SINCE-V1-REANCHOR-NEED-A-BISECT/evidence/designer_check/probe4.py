"""Designer-check probe (scratch, read-only). PROBE_OUT=<jsonl> python probe4.py <scenario_key>
Per tick, for every entity: position, hp, max_hp, alive, current project, group (st).
For entities that are retreat-active (current project id contains 'combat_retreat'), below hp ratio 0.5, or had a retreat_pull call this tick, and for entity 18 at t40-45 (positive control):
  th: acting = acting_threat_to (src/ai/goals/present_threat.py), adj = a perceived hostile orthogonally adjacent (decision 32's adjacency, LegalityServiceV2.is_adjacent),
      perceived = number of perceived hostiles, terms = AGENCY-07 present_threat_terms.
rp: every retreat_pull call that changes a score. sc: retreat score and the top three raw scores per call.
wv: entities 1 and 14 in detail t1640-1670 (task, payload action, nav target, movement mode, faction), faction pair tension/diplomatic state every 25 ticks."""
import json, os, sys, runpy
sys.path.insert(0, ".")
OUT = open(os.environ["PROBE_OUT"], "w")
def log(**r): OUT.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
cur = {"tick": None, "eid": None}; rp_now = set()
from src.ai.goals import base as gbase
import src.ai.goals.scorers as sc
import src.ai.goals
from src.ai.goals.present_threat import acting_threat_to
from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.tactical_threat import present_threat_terms
from src.engine.legality import LegalityServiceV2
orig_all = gbase.GoalRegistry.get_all_scores.__func__
def get_all(cls, entity, state):
    cur["tick"], cur["eid"] = state.tick, entity.id
    res = orig_all(cls, entity, state)
    top = sorted(res, key=lambda s: -s.utility)[:3]
    r = [s.utility for s in res if str(s.kind).endswith("COMBAT_RETREAT")]
    log(k="sc", t=state.tick, e=entity.id, r=round(r[0], 6) if r else None, top=[[str(s.kind), round(s.utility, 6)] for s in top])
    return res
gbase.GoalRegistry.get_all_scores = classmethod(get_all)
if hasattr(sc, "retreat_pull"):
    orig_rp = sc.retreat_pull
    def rp(raw, hp_ratio):
        out = orig_rp(raw, hp_ratio)
        if out != raw:
            log(k="rp", t=cur["tick"], e=cur["eid"], raw=raw, hp=hp_ratio, out=out); rp_now.add((cur["tick"], cur["eid"]))
        return out
    sc.retreat_pull = rp
from src.systems.world_systems.groups import GroupSystem
orig_ug = GroupSystem.update_groups
def ug(state, current_update=None):
    t = state.tick
    for eid in sorted(state.entities):
        e = state.entities[eid]; st = e.strategic
        pr = st.current_project_id
        hpr = e.combat.hp / max(1, e.combat.max_hp)
        log(k="st", t=t, e=eid, p=e.navigation.position, hp=e.combat.hp, mh=e.combat.max_hp, a=e.combat.alive, pr=pr, g=e.identity.group_id)
        if e.combat.alive and (("combat_retreat" in (pr or "")) or hpr < 0.5 or (t, eid) in rp_now or (eid == 18 and 40 <= t <= 45)):
            hs = perceived_hostiles(e, state)
            adj = any(LegalityServiceV2.is_adjacent(e.navigation.position, h.navigation.position) for h in hs)
            log(k="th", t=t, e=eid, acting=bool(acting_threat_to(e, state)), adj=bool(adj), perc=len(hs), terms=[str(x) for x in present_threat_terms(e, hs)] if hs else [], hpr=round(hpr, 4), pr=pr)
    if 1640 <= t <= 1670:
        for eid in (1, 14):
            e = state.entities.get(eid)
            if e is not None:
                log(k="wv", t=t, e=eid, p=e.navigation.position, hp=e.combat.hp, a=e.combat.alive, wk=e.task.work_kind, act=e.task.payload.get("action") if e.task.payload else None,
                    nt=e.navigation.target, mm=str(e.navigation.movement_mode), f=e.identity.properties.get("faction_id") if e.identity.properties else None, pr=e.strategic.current_project_id, g=e.identity.group_id)
    if t % 25 == 0 or 1640 <= t <= 1670:
        for fid, f in sorted(state.factions.items()):
            for o, v in sorted(f.pairwise_tension.items()):
                if fid < o: log(k="ten", t=t, f=fid, o=o, v=round(v, 6), d=str(f.diplomatic_relations.get(o)))
    rp_now.difference_update({x for x in rp_now if x[0] <= t})
    return orig_ug(state, current_update)
GroupSystem.update_groups = staticmethod(ug)
sys.argv = ["evaluate_simq", "--scenario", sys.argv[1]]
try: runpy.run_path("tools/evaluate_simq.py", run_name="__main__")
except SystemExit as ex: log(k="exit", code=str(ex.code))
OUT.close()
