"""Scope 1/2 probe. usage: dirty_probe.py <root> <mode plain|strong> <trials> <ticks>
Runs <trials> identical seed-42 frontier_living_world runs in this ONE process (audit_mode, 1e9 budget,
sequential executor), prints the canonical-hash trace group of each trial, the count of id()-collision skips in
DirtySetBuilder.mark_from_update, and (strong mode) keeps a strong reference to every entity-update object so no
address can be reused. Positive-control: the trial hash traces themselves are compared across trials.
"""
import hashlib
import sys

ROOT, MODE, TRIALS, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)

from src.config.profiles import PROD_SMALL
from src.core.dirty import DirtySetBuilder
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

KEEP = []        # strong references (strong mode only)
SKIPS = [0]      # id()-collision skips: same id, different update object content
_orig = DirtySetBuilder.mark_from_update


def _mfu(self, state, update):
    shadow = self.__dict__.setdefault("_shadow", {})
    for e_id, e_upd in update.entity_updates.items():
        uid = id(e_upd)
        sig = hashlib.md5(repr((e_id, e_upd)).encode()).hexdigest()
        if hasattr(self, '_processed_upd_ids') and uid in self._processed_upd_ids:
            if shadow.get(uid) != sig:
                SKIPS[0] += 1
        else:
            shadow[uid] = sig
        if MODE == "strong":
            KEEP.append(e_upd)
    return _orig(self, state, update)


DirtySetBuilder.mark_from_update = _mfu

repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context("frontier_living_world")
traces = []
for t in range(TRIALS):
    SKIPS[0] = 0
    state, _ = WorldCompiler.compile(spec, 42, context=ctx)
    k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state,
               rng=DeterministicRNG(42),
               flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True},
               executor=LocalSequentialExecutor())
    hs = []
    try:
        for _ in range(TICKS):
            k.tick_once()
            hs.append(CanonicalStateHasher.get_hash(k._state)[:10])
    finally:
        k.shutdown()
    traces.append(tuple(hs))
    print("trial", t, hs[-1], "skips", SKIPS[0], "dropped", k._status.total_dropped_work, flush=True)
    if MODE == "strong":
        KEEP.clear()
groups = {}
for i, tr in enumerate(traces):
    groups.setdefault(tr, []).append(i)
print("RESULT", MODE, ROOT.split("/")[-1], "trials", TRIALS, "ticks", TICKS, "distinct_traces", len(groups),
      {k[-1]: len(v) for k, v in groups.items()})
