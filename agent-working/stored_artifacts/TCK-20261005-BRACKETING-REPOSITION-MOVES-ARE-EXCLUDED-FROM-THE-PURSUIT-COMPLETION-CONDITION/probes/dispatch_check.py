"""Is tracked_move_complete ever called for a given entity, and what does it return? usage: dispatch_check.py <root> <world> <entity_id> <ticks>

Wraps MovementCandidateSelector.tracked_move_complete and the two scheduler/dispatcher entry points' view of the entity; reports, per
100-tick window, how many times the completion check ran for the entity and its return values, plus how many ticks the scheduler
produced an ENTITY_MOVE work item for it. Settings: audit_mode=True, max_tick_budget_ms=1e9, seed 42.
"""
import collections
import sys

ROOT, WORLD, EID, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.candidate_selector import MovementCandidateSelector as M  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.scheduler import DeterministicScheduler  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
NOW = [0]
CHECK = collections.defaultdict(collections.Counter)  # window -> {True/False: n}
SCHED = collections.Counter()  # window -> ENTITY_MOVE work items for the entity
_tmc = M.tracked_move_complete


def tmc(entity, entities):
    r = _tmc(entity, entities)
    if entity.id == EID:
        CHECK[NOW[0] // 100][r] += 1
    return r


M.tracked_move_complete = staticmethod(tmc)
_sw = DeterministicScheduler.select_work


def sw(self, state, *a, **k):
    out = _sw(self, state, *a, **k)
    try:
        for item in out[0]:  # select_work returns (work_items, dropped_count)
            if getattr(item, "owner_id", None) == EID and getattr(item, "work_kind", None) == "ENTITY_MOVE":
                SCHED[NOW[0] // 100] += 1
    except Exception:
        pass
    return out


DeterministicScheduler.select_work = sw
from src.engine.lod import LODService  # noqa: E402

LOD = collections.defaultdict(collections.Counter)  # window -> {True/False: n} for the entity
_lod = LODService.should_execute


def lod(tick, ent, focus_points):
    r = _lod(tick, ent, focus_points)
    if ent.id == EID:
        LOD[tick // 100][r] += 1
    return r


LODService.should_execute = staticmethod(lod)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        NOW[0] = k._state.tick
        k.tick_once()
        e = k._state.entities.get(EID)
        if e is not None and NOW[0] in (300, 310, 320, 325, 330, 400, 1000, 1299):
            print("MOVER t", NOW[0], "active", e.lifecycle.active, "alive", e.combat.alive, "hp", e.combat.hp, "task", e.task.work_kind)
finally:
    k.shutdown()
for w in sorted(set(CHECK) | set(SCHED) | set(LOD)):
    print("WINDOW", w * 100, "completion_checks", dict(CHECK[w]), "entity_move_work_items", SCHED[w], "lod_should_execute", dict(LOD[w]))
