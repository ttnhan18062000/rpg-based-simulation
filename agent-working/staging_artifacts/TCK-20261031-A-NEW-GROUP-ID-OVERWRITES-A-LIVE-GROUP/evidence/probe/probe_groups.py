"""Group-id overwrite and ghost-member probe (scratch, read-only; no source edits).
Usage: PROBE_OUT=<jsonl> python probe_groups.py <world> <seed> <ticks>   (cwd = a commit tree, PYTHONPATH = that tree)
Hooks (wrappers only, results unchanged):
  GroupRecord.__init__ called directly from src.systems.world_systems.groups (formations) or src.engine.military_conflict (squads) -> records them (dataclasses.replace callers are not counted).
  GroupSystem.update_groups -> after it returns, each formation record is checked BEFORE the same-tick merge (pipeline_phases/groups.py:48-53) against the prior store and earlier formations this call.
  ApplyPath.apply_generation -> after it returns, (1) formation/squad records checked against the prior store, (2) formation records that are not what the store holds, (3) ghost members.
Counts:
  pre_loose   formation row whose id is taken (prior store or earlier formation this call) by a record with a DIFFERENT leader   (a lower bound only for the overwrites that share a leader)
  pre_strict  as pre_loose and the member sets are disjoint
  pre_same_leader  id taken by a record with the SAME leader (not counted above)
  vs_squad    formation id equal to a squad row created earlier this tick; squad_taken: squad id already in the prior store
  post_lost   formation rows whose record is not what the store holds for that id after apply (and differs from it)
  ghost       living entity with group_id >= 0 whose group is missing or does not list it, at end of tick; ghost_persist: seen at two consecutive ticks
  ghost_preceded: ghost entity that was a member of a record overwritten by a pre_loose event"""
import json, os, sys
sys.path.insert(0, ".")
OUT = open(os.environ["PROBE_OUT"], "w") if os.environ.get("PROBE_OUT") else None
def log(**r):
    if OUT: OUT.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
S = dict(pre_loose=0, pre_strict=0, pre_same_leader=0, vs_squad=0, squad_taken=0, post_lost=0, formations=0, squads=0,
         ghost_any=set(), ghost_persist=set(), ghost_preceded=set(), overwritten_members=set(), prev_ghost=set(), ghost_end=0, events=[])
CUR = {"form": [], "squad": [], "tick": None}
def install():
    from src.systems.world_systems.groups import GroupSystem
    from src.engine.apply import ApplyPath
    from src.core.state import GroupRecord as GR
    oi = GR.__init__
    def ini(self, *a, **k):
        oi(self, *a, **k)
        mod = sys._getframe(1).f_globals.get("__name__")
        if mod == "src.systems.world_systems.groups": CUR["form"].append(self)
        elif mod == "src.engine.military_conflict": CUR["squad"].append(self)
    GR.__init__ = ini
    ou = GroupSystem.update_groups
    def ug(state, *a, **k):
        if CUR["tick"] != state.tick: CUR.update(tick=state.tick); CUR["squad"] = []
        CUR["form"] = []
        res = ou(state, *a, **k)
        seen = dict(state.groups)
        for r in CUR["form"]:
            S["formations"] += 1
            ex = seen.get(r.id)
            if ex is not None:
                if ex.leader_id != r.leader_id:
                    S["pre_loose"] += 1
                    if not (set(ex.member_ids) & set(r.member_ids)): S["pre_strict"] += 1
                    S["overwritten_members"].update(ex.member_ids)
                    if len(S["events"]) < 40: S["events"].append([state.tick, r.id, ex.leader_id, r.leader_id, sorted(ex.member_ids), sorted(r.member_ids)])
                else: S["pre_same_leader"] += 1
            if any(s.id == r.id for s in CUR["squad"]): S["vs_squad"] += 1
            seen[r.id] = r
        return res
    GroupSystem.update_groups = staticmethod(ug)
    oa = ApplyPath.apply_generation
    def ag(prior, update, *a, **k):
        for s in CUR["squad"]:
            S["squads"] += 1
            if s.id in prior.groups: S["squad_taken"] += 1
        forms = list(CUR["form"]); CUR["form"] = []
        new = oa(prior, update, *a, **k)
        for r in forms:
            h = new.groups.get(r.id)
            if h is not r and (h is None or h.leader_id != r.leader_id): S["post_lost"] += 1
        ghosts = set()
        if new.groups:
            for e in new.entities.values():
                g = e.identity.group_id
                if g is not None and g >= 0 and e.combat.alive:
                    gr = new.groups.get(g)
                    if gr is None or e.id not in gr.member_ids: ghosts.add(e.id)
        S["ghost_any"] |= ghosts; S["ghost_persist"] |= (ghosts & S["prev_ghost"]); S["prev_ghost"] = ghosts; S["ghost_end"] = len(ghosts)
        S["ghost_preceded"] |= (S["ghost_persist"] & S["overwritten_members"])
        CUR["squad"] = CUR["squad"] if CUR["tick"] == prior.tick else []
        return new
    ApplyPath.apply_generation = staticmethod(ag)
def summary():
    return {k: (len(v) if isinstance(v, set) else v) for k, v in S.items() if k not in ("prev_ghost", "events")} | {"events": S["events"]}
if __name__ == "__main__":
    world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    install()
    from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
    flags = _load_profile_feature_flags(_resolve_profile(world))
    run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=True)
    m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
    log(k="fin", world=world, seed=seed, ticks=ticks, state_hash=m["state_hash"], elapsed=elapsed, **summary())
    if OUT: OUT.close()
