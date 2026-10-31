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
X = dict(growth={}, policy=dict(changes=[], ticks={}, last=None), mirror=dict(ticks=0, predicted=0, actual=0, pred_not_actual=[], actual_not_pred=[]), dis_other=[], coop=dict(calls=0, statuses={}, dissolved=0), pool=[], dis=[], initial_ids=None, born={}, forms=[], events=0, alive={}, touch={}, copies=0, copied_records=0)
def touch(name, n):
    t = X["touch"].setdefault(name, [0, 0]); t[0] += 1; t[1] += n
ou = GroupSystem.update_groups
from src.core.strategic import ContractStatus
from profile_helpers import _eff, _alive, _active, _pos, _reasons
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
    import src.core.dirty as _d
    _w = P.S["work_relevant"]; rel = _d.get_relevant_group_ids(state, cu); P.S["work_relevant"] = _w
    pred = {gid for gid in rel if gid in state.groups and state.groups[gid].dissolution_tick is None and _reasons(state, cu, state.groups[gid])}
    r = ou(state, *a, **k)
    for g in P.CUR["form"]:
        X["forms"].append([state.tick, g.id, sorted(g.member_ids)])
        ld = state.entities.get(g.leader_id); c = ld.strategic.contracts.get(g.contract_id) if (ld is not None and g.contract_id) else None
        X.setdefault("form_contract", []).append([state.tick, g.id, g.contract_id, None if c is None else str(getattr(c.status, "value", c.status)), None if c is None else c.expiry_tick, None if c is None else (c.expiry_tick != -1 and state.tick > c.expiry_tick)])
    act = {row.id for row in r.groups_add_or_update if row.dissolution_tick is not None and state.groups.get(row.id) is not None and state.groups[row.id].dissolution_tick is None and row.dissolution_tick == state.tick}
    mi = X["mirror"]; mi["ticks"] += 1; mi["predicted"] += len(pred); mi["actual"] += len(act)
    for gid in sorted(pred - act):
        if len(mi["pred_not_actual"]) < 20: mi["pred_not_actual"].append([state.tick, gid])
    for gid in sorted(act - pred):
        if len(mi["actual_not_pred"]) < 20: mi["actual_not_pred"].append([state.tick, gid])
    mi["n_pred_not_actual"] = mi.get("n_pred_not_actual", 0) + len(pred - act); mi["n_actual_not_pred"] = mi.get("n_actual_not_pred", 0) + len(act - pred)
    X.setdefault("ug_dis_ids", {})[state.tick] = act
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
    if new.tick in GROWTH_TICKS: X["growth"][str(new.tick)] = _growth(new)
    if new.tick % 250 == 0: X["alive"][str(new.tick)] = sum(1 for e in new.entities.values() if e.combat.alive)
    X["alive"]["last"] = [new.tick, sum(1 for e in new.entities.values() if e.combat.alive)] if new.tick % 250 == 0 else X["alive"].get("last")
    return new
ApplyPath.apply_generation = staticmethod(ag)
from profile_helpers import _growth, GROWTH_TICKS
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
from src.engine.pipeline_phases.groups import GroupPhase
from src.domains.cooperation.phase import CooperationPhase
orr = GroupPhase.resolve
def rr(state, update):
    res = orr(state, update)
    ids = X.get("ug_dis_ids", {}).get(state.tick, set())
    for row in res.groups_add_or_update:
        old = state.groups.get(row.id)
        if row.dissolution_tick is not None and old is not None and old.dissolution_tick is None and row.dissolution_tick == state.tick and row.id not in ids:
            X["dis_other"].append([state.tick, row.id, sorted(old.member_ids), "GroupPhase.resolve (defection pass: check_defection left <=1 member)"])
    return res
GroupPhase.resolve = staticmethod(rr)
from src.domains.cooperation.services import PartyCohesionService as _PCS
_oev = _PCS.evaluate
def _ev(g_id, st, *a, **k):
    rep = _oev(g_id, st, *a, **k)
    X["coop"]["statuses"][rep.status] = X["coop"]["statuses"].get(rep.status, 0) + 1
    return rep
_PCS.evaluate = staticmethod(_ev)
_oco = CooperationPhase.execute
def _co(state, update, *a, **k):
    res = _oco(state, update, *a, **k)
    X["coop"]["calls"] += 1
    for row in res.groups_add_or_update:
        old = state.groups.get(row.id)
        if row.dissolution_tick is not None and old is not None and old.dissolution_tick is None: X["coop"]["dissolved"] += 1
    return res
CooperationPhase.execute = staticmethod(_co)
from src.engine.kernel import Kernel as _K
_otk2 = _K.tick_once
def _tk2(self, *a, **k):
    r = _otk2(self, *a, **k)
    pol = getattr(self, "_current_policy", None)
    cur = [getattr(pol, "replay_richness", None), getattr(pol, "replay_allowed", None), getattr(pol, "name", None) or str(getattr(self, "_current_mode", None))]
    t = X["policy"]["ticks"]; key = "/".join(str(x) for x in cur); t[key] = t.get(key, 0) + 1
    if X["policy"]["last"] != cur:
        X["policy"]["changes"].append([getattr(self._state, "tick", None), X["policy"]["last"], cur]); X["policy"]["last"] = cur
    return r
_K.tick_once = _tk2
world, seed, ticks = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile(world))
NOPROF = bool(os.environ.get("NOPROF"))
pr = cProfile.Profile()
if not NOPROF: pr.enable()
run_dir, elapsed, run_id = _run_engine(world, seed, ticks, extra_flags=flags, audit_mode=(os.environ.get("AUDIT", "1") != "0"))
if not NOPROF: pr.disable()
prefix = os.environ.get("PROF_OUT", "")
if not NOPROF: pr.dump_stats(prefix + ".prof")
ps = pstats.Stats(pr) if not NOPROF else None
SITES = ("replay/fingerprint.py", "engine/checkpoint.py", "engine/executor.py", "core/dirty.py", "engine/apply_plan.py", "engine/apply.py",
         "world_systems/groups.py", "pipeline_phases/groups.py", "cooperation/phase.py")
def rec(k, v):
    cc, nc, tt, ct = v[0], v[1], v[2], v[3]
    return {"file": k[0], "line": k[1], "func": k[2], "calls": nc, "own_s": round(tt, 4), "cum_s": round(ct, 4), "cum_per_call_us": round(ct / max(nc, 1) * 1e6, 2)}
rows = [rec(k, v) for k, v in ps.stats.items()] if ps else []
top = sorted(rows, key=lambda r: -r["cum_s"])[:40]
phases = sorted([r for r in rows if "phase" in r["func"].lower() or r["func"] in ("tick_once", "execute", "resolve", "apply_generation", "build_plan")], key=lambda r: -r["cum_s"])[:40]
sites = sorted([r for r in rows if any(s in r["file"].replace("\\", "/") for s in SITES)], key=lambda r: -r["cum_s"])[:80]
m = json.load(open(os.path.join(run_dir, "run_manifest.json")))
out = {"k": "profile", "world": world, "seed": seed, "ticks": ticks, "state_hash": m["state_hash"], "elapsed": elapsed, "top_cum": top, "phases": phases, "sites": sites,
       "touch": X["touch"], "copies": X["copies"], "copied_records": X["copied_records"], "events": X["events"], "alive": X["alive"],
       "initial_ids": X["initial_ids"], "born": {str(k): v for k, v in X["born"].items()}, "growth": X["growth"], "form_contract": X.get("form_contract", []), "policy": X["policy"], "audit_mode": os.environ.get("AUDIT", "1") != "0", "mirror": X["mirror"], "dis_other": X["dis_other"], "coop": X["coop"], "pool": X["pool"], "dissolutions": X["dis"], "formations_n": len(X["forms"]), "forms": X["forms"], "ghost_ids": sorted(P.S["ghost_any"]), "ghost_persist_ids": sorted(P.S["ghost_persist"]), "probe": P.summary()}
with open(os.environ["PROBE_OUT"], "w") as fh: fh.write(json.dumps(out, default=str, separators=(",", ":")) + "\n")
