"""Trace probe (local only). Run from a commit archive dir: python probe.py <out.jsonl>. Logs entity 18/3 scorer inputs, retreat_pull calls and group changes."""
import json, sys, dataclasses
sys.path.insert(0, ".")
OUT = open(sys.argv[1], "w")
def log(**r): OUT.write(json.dumps(r, default=str) + "\n")
WATCH = {18, 3}
cur = {"tick": None, "eid": None}
from src.ai.goals import base as gbase
import src.ai.goals.scorers as sc
import src.ai.goals  # registers scorers
orig_all = gbase.GoalRegistry.get_all_scores.__func__
def get_all(cls, entity, state):
    cur["tick"], cur["eid"] = state.tick, entity.id
    res = orig_all(cls, entity, state)
    if entity.id in WATCH and state.tick <= 135:
        nav = entity.navigation
        log(k="scores", tick=state.tick, e=entity.id, pos=nav.position, hp=entity.combat.hp, maxhp=entity.combat.max_hp,
            nav={f.name: getattr(nav, f.name) for f in dataclasses.fields(nav) if "target" in f.name or "dest" in f.name or "path" in f.name or "goal" in f.name},
            scores=[(str(s.kind), round(s.utility, 4), s.target_id) for s in res])
    return res
gbase.GoalRegistry.get_all_scores = classmethod(get_all)
if hasattr(sc, "retreat_pull"):
    orig_rp = sc.retreat_pull
    def rp(raw, hp_ratio):
        out = orig_rp(raw, hp_ratio)
        if cur["eid"] in WATCH and cur["tick"] <= 135 or out != raw:
            log(k="retreat_pull", tick=cur["tick"], e=cur["eid"], raw=raw, hp_ratio=hp_ratio, out=out)
        return out
    sc.retreat_pull = rp
from src.systems.world_systems.groups import GroupSystem
orig_ug = GroupSystem.update_groups
prev = {}
def ug(state, current_update=None):
    res = orig_ug(state, current_update)
    snap = {g: (r.leader_id, tuple(sorted(r.member_ids)), r.dissolution_tick) for g, r in state.groups.items()}
    if 78 <= state.tick <= 86 and 10006 in state.groups:
        g6 = state.groups[10006]
        log(k="g6_pos", tick=state.tick, radius=g6.cohesion_radius, members=sorted(g6.member_ids),
            pos={m: state.entities[m].navigation.position for m in g6.member_ids if m in state.entities},
            alive={m: state.entities[m].combat.alive for m in g6.member_ids if m in state.entities}, leader=g6.leader_id)
    if 40 <= state.tick <= 52 and 18 in state.entities:
        e18 = state.entities[18]; st = e18.strategic
        log(k="e18_tick", tick=state.tick, pos=e18.navigation.position, target=e18.navigation.target,
            project=st.current_project_id, proj_kind=(st.projects[st.current_project_id].kind if st.current_project_id in st.projects else None))
    if 60 <= state.tick <= 86 and 10006 in state.groups and 18 in state.entities and 30 in state.entities:
        g6 = state.groups[10006]; l = state.entities[18]; m = state.entities[30]
        pr = l.strategic.projects.get(l.strategic.current_project_id) if l.strategic.current_project_id else None
        bond = m.social.bonds.get(18)
        trust = (bond.sentiment + 1.0) / 2.0 if bond else m.social.trust_history.get(18, 0.5)
        ax, ay = g6.anchor
        dsq = {mm: (state.entities[mm].navigation.position[0]-ax)**2 + (state.entities[mm].navigation.position[1]-ay)**2 for mm in g6.member_ids if mm in state.entities}
        log(k="g6_anchor", tick=state.tick, anchor=g6.anchor, leader=g6.leader_id, leader_project_id=l.strategic.current_project_id,
            proj_kind=(pr.kind if pr else None), leader_projects=sorted(l.strategic.projects), trust30_in_18=trust, dist_sq_to_anchor=dsq,
            pos18=l.navigation.position, pos30=m.navigation.position, last_updated=g6.last_updated_tick)
    if 53 <= state.tick <= 70 and 18 in state.entities:
        e = state.entities[18]; st = e.strategic
        objs = getattr(st, "objectives", None)
        log(k="e18_proj", tick=state.tick, cur=st.current_project_id, projects={pid: (pr.kind, getattr(pr, "status", None)) for pid, pr in st.projects.items()},
            target=e.navigation.target, work=e.task.work_kind, hp=e.combat.hp,
            directives=[(d.id, d.kind, str(d.target)) for d in (getattr(st, "directives", None) or {}).values()] if isinstance(getattr(st, "directives", None), dict) else str(getattr(st, "directives", None))[:200])
    adds = getattr(res, "groups_add_or_update", None)
    if adds is not None:
        for r in adds:
            rr = r if hasattr(r, "id") else None
            if rr is not None:
                log(k="group_upd", tick=state.tick, gid=rr.id, leader=rr.leader_id, members=sorted(rr.member_ids), dissolved=rr.dissolution_tick, n_state_groups=len(state.groups), is_new=rr.id not in state.groups)
    return res
GroupSystem.update_groups = staticmethod(ug)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile("urban_political_selfmodel_probe"))
run_dir, _e, run_id = _run_engine("urban_political", 42, 200, extra_flags=flags, audit_mode=True)
log(k="done", run_id=run_id, run_dir=run_dir)
OUT.close()
print("PROBE_DONE", run_id)
