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
X = dict(initial_ids=None, born={}, forms=[], events=0, alive={}, touch={}, copies=0, copied_records=0)
def touch(name, n):
    t = X["touch"].setdefault(name, [0, 0]); t[0] += 1; t[1] += n
ou = GroupSystem.update_groups
def ug(state, *a, **k):
    r = ou(state, *a, **k)
    for g in P.CUR["form"]: X["forms"].append([state.tick, g.id, sorted(g.member_ids)])
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
sites = sorted([r for r in rows if any(s in r["file"].replace("\\", "/") for s in SITES)], key=lambda r: -r["cum_s"])[:80]
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
out = {"k": "profile", "world": world, "seed": seed, "ticks": ticks, "state_hash": m["state_hash"], "elapsed": elapsed, "top_cum": top, "sites": sites,
       "touch": X["touch"], "copies": X["copies"], "copied_records": X["copied_records"], "events": X["events"], "alive": X["alive"],
       "initial_ids": X["initial_ids"], "born": {str(k): v for k, v in X["born"].items()}, "formations_n": len(X["forms"]), "forms": X["forms"], "ghost_ids": sorted(P.S["ghost_any"]), "ghost_persist_ids": sorted(P.S["ghost_persist"]), "probe": P.summary()}
with open(os.environ["PROBE_OUT"], "w") as fh: fh.write(json.dumps(out, default=str, separators=(",", ":")) + "\n")
