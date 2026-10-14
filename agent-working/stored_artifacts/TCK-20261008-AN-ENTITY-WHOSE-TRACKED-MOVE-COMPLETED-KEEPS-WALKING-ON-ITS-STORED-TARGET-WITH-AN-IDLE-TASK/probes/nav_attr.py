"""Navigation-target write attribution around tracked_move_completion_update (read-only).
usage: nav_attr.py <root> <world> <ticks> <seed>"""
import collections, json, sys, traceback
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core import updates as U
from src.core.governance import RuntimeMode
from src.engine.candidate_selector import MovementCandidateSelector as MCS
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
class Pin(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
WRITES = collections.defaultdict(list)   # eid -> [(tick, kind, value, frames)]
COMPL = []                                # (tick, eid)
SKIP = {"__init__", "replace", "_replace", "merge", "merge_many", "<lambda>", "<genexpr>", "run_phase", "refine"}
orig = U.EntityUpdate.__init__
def init(self, *a, **kw):
    orig(self, *a, **kw)
    nav = kw.get("navigation")
    if nav is None: return
    ts, tc = getattr(nav, "target_set", None), getattr(nav, "target_clear", False)
    if ts is None and not tc: return
    frames = [f"{f.filename.split('/src/')[-1]}:{f.lineno}:{f.name}" for f in traceback.extract_stack()[-9:-1]]
    WRITES[kw.get("entity_id", a[0] if a else None)].append((k.state.tick, "set" if ts is not None else "clear", ts, frames))
U.EntityUpdate.__init__ = init
_c = MCS.tracked_move_completion_update
def comp(entity):
    COMPL.append((k.state.tick, entity.id)); return _c(entity)
MCS.tracked_move_completion_update = staticmethod(comp)
HIST = collections.defaultdict(dict)
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for e in st.entities.values():
            HIST[e.id][st.tick] = (e.task.work_kind, bool(e.task.payload), str(e.navigation.movement_mode).split(".")[-1], e.navigation.target)
finally:
    k.shutdown()
res = []
for (t, eid) in COMPL[:25]:
    rec = dict(completion_tick=t, eid=eid, after={tt: HIST[eid].get(tt) for tt in range(t - 1, t + 5)}, writes=[])
    for (wt, kind, val, frames) in WRITES.get(eid, []):
        if t - 1 <= wt <= t + 4: rec["writes"].append((wt, kind, val, frames))
    res.append(rec)
print("NAVATTR", json.dumps(dict(world=WORLD, seed=SEED, n_completions=len(COMPL), records=res), default=str))
