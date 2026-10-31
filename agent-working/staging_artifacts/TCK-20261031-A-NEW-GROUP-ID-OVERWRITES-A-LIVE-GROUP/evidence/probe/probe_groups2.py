"""Group-id overwrite and ghost-member probe (scratch, read-only; no source edits).
Usage: PROBE_OUT=<jsonl> python probe_groups.py <world> <seed> <ticks>   (cwd = a commit tree, PYTHONPATH = that tree)
Hooks (wrappers only, results unchanged):
  GroupRecord.__init__ called directly from src.systems.world_systems.groups (formations) or src.engine.military_conflict (squads) -> records them (dataclasses.replace callers are not counted).
  GroupSystem.update_groups -> after it returns, each formation record is checked BEFORE the same-tick merge (pipeline_phases/groups.py:48-53) against the prior store and earlier formations this call.
  ApplyPath.apply_generation -> after it returns, (1) formation/squad records checked against the prior store, (2) formation records that are not what the store holds, (3) ghost members.
Added in v2 (also: store size at t500/t1000, cooperation-phase and whole-tick ms, deterministic work counts work_phase = |store ∪ update ids| per GroupPhase.resolve call, work_coop = |store| per CooperationPhase.execute call, work_relevant = size of get_relevant_group_ids results): loose/strict split by the overwritten record status (live vs dissolved), end-of-run len(groups) and dissolved count, wall ms spent in GroupPhase.resolve (the group phase incl. update_groups) and in GroupSystem.update_groups.
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
S = dict(loose_live=0, loose_dissolved=0, strict_live=0, strict_dissolved=0, end_groups=0, end_dissolved=0, phase_ms=0.0, phase_calls=0, coop_ms=0.0, coop_calls=0, tick_ms=0.0, tick_calls=0, ckpt={}, work_phase=0, work_coop=0, work_relevant=0, upd_ms=0.0, upd_calls=0, pre_loose=0, pre_strict=0, pre_same_leader=0, vs_squad=0, squad_taken=0, post_lost=0, formations=0, squads=0,
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
        import time as _t; _t0 = _t.perf_counter()
        res = ou(state, *a, **k)
        S["upd_ms"] += (_t.perf_counter() - _t0) * 1000; S["upd_calls"] += 1
        seen = dict(state.groups)
        for r in CUR["form"]:
            S["formations"] += 1
            ex = seen.get(r.id)
            if ex is not None:
                if ex.leader_id != r.leader_id:
                    S["pre_loose"] += 1
                    if not (set(ex.member_ids) & set(r.member_ids)): S["pre_strict"] += 1
                    dis = ex.dissolution_tick is not None
                    S["loose_dissolved" if dis else "loose_live"] += 1
                    if not (set(ex.member_ids) & set(r.member_ids)): S["strict_dissolved" if dis else "strict_live"] += 1
                    S["overwritten_members"].update(ex.member_ids)
                    if len(S["events"]) < 40: S["events"].append([state.tick, r.id, ex.leader_id, r.leader_id, sorted(ex.member_ids), sorted(r.member_ids)])
                else: S["pre_same_leader"] += 1
            if any(s.id == r.id for s in CUR["squad"]): S["vs_squad"] += 1
            seen[r.id] = r
        return res
    GroupSystem.update_groups = staticmethod(ug)
    from src.engine.pipeline_phases.groups import GroupPhase
    import src.core.dirty as _dirty
    _ogr = _dirty.get_relevant_group_ids
    def _gr(*a, **k):
        r = _ogr(*a, **k); S["work_relevant"] += len(r); return r
    _dirty.get_relevant_group_ids = _gr
    orz = GroupPhase.resolve
    def rz(state, update):
        import time as _t; _t0 = _t.perf_counter()
        S["work_phase"] += len(set(state.groups) | {g.id for g in update.groups_add_or_update} | {g.id for g in getattr(update, "groups_add", ())})
        r = orz(state, update)
        S["phase_ms"] += (_t.perf_counter() - _t0) * 1000; S["phase_calls"] += 1
        return r
    GroupPhase.resolve = staticmethod(rz)
    from src.domains.cooperation.phase import CooperationPhase
    oco = CooperationPhase.execute
    def co(*a, **k):
        S["work_coop"] += len(a[0].groups) if a else len(k["state"].groups)
        import time as _t; _t0 = _t.perf_counter()
        r = oco(*a, **k)
        S["coop_ms"] += (_t.perf_counter() - _t0) * 1000; S["coop_calls"] += 1
        return r
    CooperationPhase.execute = staticmethod(co) if isinstance(CooperationPhase.__dict__.get("execute"), staticmethod) else co
    try:
        from src.engine.kernel import Kernel
        otk = Kernel.tick_once
        def tk(self, *a, **k):
            import time as _t; _t0 = _t.perf_counter()
            r = otk(self, *a, **k)
            S["tick_ms"] += (_t.perf_counter() - _t0) * 1000; S["tick_calls"] += 1
            return r
        Kernel.tick_once = tk
    except Exception: pass
    oa = ApplyPath.apply_generation
    def ag(prior, update, *a, **k):
        for s in CUR["squad"]:
            S["squads"] += 1
            if s.id in prior.groups: S["squad_taken"] += 1
        forms = list(CUR["form"]); CUR["form"] = []
        new = oa(prior, update, *a, **k)
        if prior.tick + 1 in (500, 1000): S["ckpt"][str(prior.tick + 1)] = [len(new.groups), sum(1 for g in new.groups.values() if g.dissolution_tick is not None)]
        S["end_groups"] = len(new.groups); S["end_dissolved"] = sum(1 for g in new.groups.values() if g.dissolution_tick is not None)
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
    return {k: (len(v) if isinstance(v, set) else v) for k, v in S.items() if k not in ("prev_ghost", "events", "ckpt")} | {"events": S["events"], "ckpt": S["ckpt"]}
if __name__ == "__main__":
    world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    install()
    from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
    flags = _load_profile_feature_flags(_resolve_profile(world))
    run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=True)
    m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
    log(k="fin", world=world, seed=seed, ticks=ticks, state_hash=m["state_hash"], elapsed=elapsed, **summary())
    if OUT: OUT.close()
