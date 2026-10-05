"""Many short identical runs to catch the tick-5 divergence and diff the diverging fields."""
import hashlib
import json
import sys

ROOT = "/mnt/data/Working/rpg-based-simulation/.claude/worktrees/lane-a-tactical-path-batch"
OUT = "/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad"
sys.path.insert(0, ROOT)
TRIALS, TICKS = int(sys.argv[1]), int(sys.argv[2])

from src.config.profiles import PROD_SMALL
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

from src.systems.strategic_systems.work_queue import StrategicWorkQueue as _W
_REC = []
_b = _W.build
def _wb(state, update, dirty, budget=50, sweep_interval=1):
    r = _b(state, update, dirty, budget, sweep_interval)
    flags = {}
    dstrat = dirty.strategic_entities if dirty else set()
    for e_id, e in state.entities.items():
        nav_fail = e.navigation.wait_count >= 5 or e.navigation.oscillation_count >= 3
        intent_fail = any(not x.accepted for x in e.identity.latest_intent_results)
        flags[e_id] = (bool(nav_fail), bool(intent_fail), any(not b.resolved for b in e.strategic.blockers.values()),
                       e.strategic.current_project_id, bool(e_id in dstrat), len(e.identity.latest_intent_results),
                       e.navigation.wait_count, e.navigation.oscillation_count)
    _REC.append({"tick": state.tick, "budget": budget, "sweep": sweep_interval, "cands": list(r),
                 "dirty_none": dirty is None, "force_full": bool(update.force_full_scan),
                 "dirty_strat": sorted(dstrat), "flags": flags})
    return r
_W.build = staticmethod(_wb)
from src.core.dirty import DirtySetBuilder as _DSB
import hashlib as _hl
_COLL = []
_orig_mfu = _DSB.mark_from_update
def _mfu(self, state, update):
    shadow = self.__dict__.setdefault("_shadow", {})
    new = []
    for e_id, e_upd in update.entity_updates.items():
        uid = id(e_upd)
        sig = (e_id, _hl.md5(repr(e_upd).encode()).hexdigest())
        if uid in self._processed_upd_ids:
            if shadow.get(uid) != sig:
                _COLL.append({"tick": state.tick, "entity": e_id, "stored_entity": (shadow.get(uid) or (None,))[0]})
        else:
            new.append((uid, sig))
    r = _orig_mfu(self, state, update)
    for uid, sig in new:
        shadow[uid] = sig
    return r
_DSB.mark_from_update = _mfu
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context("frontier_living_world")
trials = []
for t in range(TRIALS):
    state, _ = WorldCompiler.compile(spec, 42, context=ctx)
    k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state,
               rng=DeterministicRNG(42),
               flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True},
               executor=LocalSequentialExecutor())
    hashes, dicts = [], []
    _REC.clear()
    _COLL.clear()
    try:
        for _ in range(TICKS):
            k.tick_once()
            st = k._state
            hashes.append(CanonicalStateHasher.get_hash(st)[:12])
            dicts.append({str(e.id): e.to_canonical_dict() for e in st.entities.values()})
    finally:
        k.shutdown()
    trials.append({"hashes": hashes, "dicts": dicts, "rec": [dict(x) for x in _REC], "coll": list(_COLL)})
    print("trial", t, hashes[-1], "id-collisions skipped:", len(_COLL), [(c["tick"], c["entity"]) for c in _COLL[:6]], flush=True)

groups = {}
for i, tr in enumerate(trials):
    groups.setdefault(tuple(tr["hashes"]), []).append(i)
print("distinct hash traces:", len(groups), {str(list(k)[-1]): v for k, v in groups.items()})
if len(groups) > 1:
    keys = list(groups)
    ga, gb = trials[groups[keys[0]][0]]["rec"], trials[groups[keys[1]][0]]["rec"]
    for ra, rb in zip(ga, gb):
        if ra != rb:
            print("FIRST DIFFERING WORK-QUEUE RECORD, tick", ra["tick"])
            for key in ("budget", "sweep", "dirty_none", "force_full"):
                print("  ", key, ra[key], rb[key])
            print("   candidates only in A:", sorted(set(ra["cands"]) - set(rb["cands"])))
            print("   candidates only in B:", sorted(set(rb["cands"]) - set(ra["cands"])))
            print("   dirty_strat A:", ra["dirty_strat"], "B:", rb["dirty_strat"])
            for eid in sorted(set(ra["flags"]) | set(rb["flags"])):
                if ra["flags"].get(eid) != rb["flags"].get(eid):
                    print("   ENTITY FLAGS DIFFER", eid, ra["flags"].get(eid), rb["flags"].get(eid))
            print("   candidate lists A:", ra["cands"])
            print("   candidate lists B:", rb["cands"])
            break
    else:
        print("work-queue records identical between groups over", len(ga), "calls")
    ca = [(c["tick"], c["entity"]) for c in trials[groups[keys[0]][0]]["coll"] if c["entity"] == 16 and c["tick"] <= 5]
    cb = [(c["tick"], c["entity"]) for c in trials[groups[keys[1]][0]]["coll"] if c["entity"] == 16 and c["tick"] <= 5]
    print("COLLISIONS INVOLVING ENTITY 16 (tick<=5)  A:", ca, " B:", cb)
    print("TICK<=4 COLLISION COUNTS  A:", sum(1 for c in trials[groups[keys[0]][0]]["coll"] if c["tick"] <= 4),
          " B:", sum(1 for c in trials[groups[keys[1]][0]]["coll"] if c["tick"] <= 4))
    a, b = trials[groups[keys[0]][0]], trials[groups[keys[1]][0]]
    first = next(i for i, (x, y) in enumerate(zip(a["hashes"], b["hashes"])) if x != y)
    print("first divergent tick index", first)
    da, db = a["dicts"][first], b["dicts"][first]

    def walk(x, y, path, out):
        if isinstance(x, dict) and isinstance(y, dict):
            for key in sorted(set(x) | set(y)):
                walk(x.get(key, "<absent>"), y.get(key, "<absent>"), path + [str(key)], out)
        elif x != y:
            out.append(("/".join(path), x, y))

    diffs = []
    walk(da, db, [], diffs)
    for p, x, y in diffs[:40]:
        print("DIFF", p, "|", str(x)[:120], "|", str(y)[:120])
    json.dump({"first": first, "diffs": [(p, str(x)[:300], str(y)[:300]) for p, x, y in diffs]}, open(f"{OUT}/early_diff.json", "w"))
