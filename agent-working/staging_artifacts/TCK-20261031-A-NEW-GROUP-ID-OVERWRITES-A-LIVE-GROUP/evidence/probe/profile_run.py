"""Profiled run for the tick-cost question (scratch, read-only: wrappers only). Usage: PROBE_OUT=<jsonl> PROF_OUT=<prefix> python profile_run.py <world> <seed> <ticks>   (cwd = a commit tree, PYTHONPATH = that tree)
Everything probe_groups2 records, plus:
  cProfile of the whole run (cumulative and own time per function), dumped to <prefix>.prof, with top-40 by cumulative time and, for the named store sites, calls / cum / own / per-call:
    src/replay/fingerprint.py, src/engine/checkpoint.py, src/engine/executor.py, src/core/dirty.py, src/engine/apply_plan.py, src/engine/apply.py,
    src/systems/world_systems/groups.py, src/engine/pipeline_phases/groups.py, src/domains/cooperation/phase.py
  store-touch counters (calls and sum of len(state.groups) at the call): StateFingerprinter._group_identity, CanonicalStateHasher.to_canonical_data,
    ApplyPlanBuilder.build_plan, and how many build_plan calls copy the store (groups_add / groups_add_or_update / groups_remove non-empty) with the records copied
  events emitted (sum of len(EventExtractor.extract result)), alive entities every 250 ticks, every formation (tick, id, sorted members), the distinct ghost entity ids, the entity ids present in the initial state and the first tick each later-born id was seen
  The profile overhead is the same kind on both trees; compare calls and per-call cost, not absolute seconds."""
import cProfile, json, os, pstats, sys
sys.path.insert(0, ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_groups2 as P
P.install()
from src.systems.world_systems.groups import GroupSystem
from src.engine.apply import ApplyPath
from src.engine.apply_plan import ApplyPlanBuilder
from src.replay.fingerprint import StateFingerprinter
from src.engine.checkpoint import CanonicalStateHasher
from src.observability.event_extractor import EventExtractor
X = dict(pool=[], dis=[], initial_ids=None, born={}, forms=[], events=0, alive={}, touch={}, copies=0, copied_records=0)
def touch(name, n):
    t = X["touch"].setdefault(name, [0, 0]); t[0] += 1; t[1] += n
ou = GroupSystem.update_groups
from src.core.strategic import ContractStatus
def _eff(cu, e_id):
    return cu.entity_updates.get(e_id) if cu is not None else None
def _alive(state, cu, e_id):
    u = _eff(cu, e_id)
    if u is not None and u.combat and u.combat.alive_set is False: return False
    e = state.entities.get(e_id); return e.combat.alive if e else False
def _active(state, cu, e_id):
    u = _eff(cu, e_id)
    if u is not None and u.active is False: return False
    e = state.entities.get(e_id); return e.lifecycle.active if e else False
def _pos(state, cu, e_id):
    u = _eff(cu, e_id)
    if u is not None and u.new_position: return u.new_position
    e = state.entities.get(e_id); return e.navigation.position if e else (0.0, 0.0)
def _reasons(state, cu, grp):
    """Mirror of groups.py l.95-170 on the pre-state: which branch ends this group. Read-only."""
    ldr = state.entities.get(grp.leader_id)
    if ldr is None or not _alive(state, cu, grp.leader_id) or not _active(state, cu, grp.leader_id): return ["l110_leader_dead_inactive_or_missing"]
    out = []; kept = 1
    for m in sorted(grp.member_ids):
        if m == grp.leader_id: continue
        if not _alive(state, cu, m) or not _active(state, cu, m): out.append("member_dead_or_inactive"); continue
        mp = _pos(state, cu, m); dx = mp[0] - grp.anchor[0]; dy = mp[1] - grp.anchor[1]
        dist = dx * dx + dy * dy > (grp.cohesion_radius * 2) ** 2
        cinv = False
        if grp.contract_id and ldr:
            c = None
            if cu is not None and grp.leader_id in cu.entity_updates:
                lu = cu.entity_updates[grp.leader_id]
                if lu.strategic: c = next((x for x in lu.strategic.contracts_add_or_update if x.id == grp.contract_id), None)
            if not c: c = ldr.strategic.contracts.get(grp.contract_id)
            if not c or c.status != ContractStatus.ACTIVE: cinv = True
            elif c.expiry_tick != -1 and state.tick > c.expiry_tick: cinv = True
        if dist and cinv: out.append("member_distance_and_contract")
        elif dist: out.append("member_distance")
        elif cinv: out.append("member_contract_invalid")
        else: kept += 1
    return out if kept < 2 and out else (["l170_fewer_than_2_members_no_cause_found"] if kept < 2 else [])
def ug(state, *a, **k):
    cu = a[0] if a else k.get("current_update")
    pool = grouped = ghost = 0
    for e in state.entities.values():
        if not e.combat.alive: continue
        g = e.identity.group_id
        if g is None or g < 0: pool += 1
        else:
            grouped += 1
            gr = state.groups.get(g)
            if gr is None or e.id not in gr.member_ids: ghost += 1
    X["pool"].append([state.tick, pool, grouped, ghost])
    r = ou(state, *a, **k)
    for g in P.CUR["form"]: X["forms"].append([state.tick, g.id, sorted(g.member_ids)])
    for row in list(r.groups_add_or_update):
        old = state.groups.get(row.id)
        if row.dissolution_tick is not None and old is not None and old.dissolution_tick is None and row.dissolution_tick == state.tick:
            X["dis"].append([state.tick, row.id, sorted(old.member_ids), old.last_updated_tick, sorted(set(_reasons(state, cu, old))) or ["unclassified"]])
    return r
GroupSystem.update_groups = staticmethod(ug)
oa = ApplyPath.apply_generation
def ag(prior, update, *a, **k):
    if X["initial_ids"] is None: X["initial_ids"] = sorted(prior.entities)
    new = oa(prior, update, *a, **k)
    init = set(X["initial_ids"])
    for i in new.entities:
        if i not in init and i not in X["born"]: X["born"][i] = new.tick
    if new.tick % 250 == 0: X["alive"][str(new.tick)] = sum(1 for e in new.entities.values() if e.combat.alive)
    X["alive"]["last"] = [new.tick, sum(1 for e in new.entities.values() if e.combat.alive)] if new.tick % 250 == 0 else X["alive"].get("last")
    return new
ApplyPath.apply_generation = staticmethod(ag)
ob = ApplyPlanBuilder.build_plan
def bp(prior, update, *a, **k):
    touch("build_plan", len(prior.groups))
    if update.groups_remove or update.groups_add_or_update or getattr(update, "groups_add", ()):
        X["copies"] += 1; X["copied_records"] += len(prior.groups)
    return ob(prior, update, *a, **k)
ApplyPlanBuilder.build_plan = staticmethod(bp)
og = StateFingerprinter._group_identity
def gi(state):
    touch("fingerprint._group_identity", len(state.groups)); return og(state)
StateFingerprinter._group_identity = staticmethod(gi)
oc = CanonicalStateHasher.to_canonical_data
def cd(state):
    touch("checkpoint.to_canonical_data", len(state.groups)); return oc(state)
CanonicalStateHasher.to_canonical_data = staticmethod(cd)
oe = EventExtractor.extract
def ex(prior, current, update, mode=None, *a, **k):
    r = oe(prior, current, update, mode, *a, **k) if mode is not None else oe(prior, current, update)
    try: X["events"] += len(r)
    except TypeError: pass
    return r
EventExtractor.extract = staticmethod(ex)
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile(world))
pr = cProfile.Profile(); pr.enable()
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=True)
pr.disable()
prefix = os.environ["PROF_OUT"]; pr.dump_stats(prefix + ".prof")
ps = pstats.Stats(pr)
SITES = ("replay/fingerprint.py", "engine/checkpoint.py", "engine/executor.py", "core/dirty.py", "engine/apply_plan.py", "engine/apply.py",
         "world_systems/groups.py", "pipeline_phases/groups.py", "cooperation/phase.py")
def rec(k, v):
    cc, nc, tt, ct = v[0], v[1], v[2], v[3]
    return {"file": k[0], "line": k[1], "func": k[2], "calls": nc, "own_s": round(tt, 4), "cum_s": round(ct, 4), "cum_per_call_us": round(ct / max(nc, 1) * 1e6, 2)}
rows = [rec(k, v) for k, v in ps.stats.items()]
top = sorted(rows, key=lambda r: -r["cum_s"])[:40]
phases = sorted([r for r in rows if "phase" in r["func"].lower() or r["func"] in ("tick_once", "execute", "resolve", "apply_generation", "build_plan")], key=lambda r: -r["cum_s"])[:40]
sites = sorted([r for r in rows if any(s in r["file"].replace("\\", "/") for s in SITES)], key=lambda r: -r["cum_s"])[:80]
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
out = {"k": "profile", "world": world, "seed": seed, "ticks": ticks, "state_hash": m["state_hash"], "elapsed": elapsed, "top_cum": top, "phases": phases, "sites": sites,
       "touch": X["touch"], "copies": X["copies"], "copied_records": X["copied_records"], "events": X["events"], "alive": X["alive"],
       "initial_ids": X["initial_ids"], "born": {str(k): v for k, v in X["born"].items()}, "pool": X["pool"], "dissolutions": X["dis"], "formations_n": len(X["forms"]), "forms": X["forms"], "ghost_ids": sorted(P.S["ghost_any"]), "ghost_persist_ids": sorted(P.S["ghost_persist"]), "probe": P.summary()}
with open(os.environ["PROBE_OUT"], "w") as fh: fh.write(json.dumps(out, default=str, separators=(",", ":")) + "\n")
