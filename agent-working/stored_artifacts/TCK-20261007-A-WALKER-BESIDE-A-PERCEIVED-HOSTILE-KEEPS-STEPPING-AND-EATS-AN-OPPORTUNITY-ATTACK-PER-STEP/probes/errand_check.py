"""Does the action-holder rule block errand steps? usage: errand_check.py <root> <world> <ticks> <seed> <label>
Counts, per payload action, (1) movement-phase calls for an ENTITY_ACT entity holding a payload (resolve_move calls) and (2) in the fixed arm, targets the new rule refused."""
import collections, json, sys
ROOT, WORLD, TICKS, SEED, LABEL = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.candidate_selector import MovementCandidateSelector as MCS
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.movement import MovementSystem as MS
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
C = collections.Counter()
_rm = MS.resolve_move
def rm(st, entity, target_pos, mode=None, *a, **kw):
    if entity.task.work_kind == "ENTITY_ACT" and entity.task.payload:
        C[f"resolve_move.under_action.{entity.task.payload.get('action')}"] += 1
    else:
        C["resolve_move.other"] += 1
    return _rm(st, entity, target_pos, mode, *a, **kw) if mode is not None else _rm(st, entity, target_pos, *a, **kw)
MS.resolve_move = staticmethod(rm)
if hasattr(MCS, "movement_target"):
    _mt = MCS.movement_target
    def mt(entity, ent_upd, entities):
        r = _mt(entity, ent_upd, entities)
        if r is None and entity.navigation.target is not None and tuple(entity.navigation.target) != tuple(entity.navigation.position):
            C[f"refused_move.action={entity.task.payload.get('action')}|mode={str(entity.navigation.movement_mode).split('.')[-1]}"] += 1
        return r
    MCS.movement_target = staticmethod(mt)
try:
    for _ in range(TICKS): k.tick_once()
finally:
    k.shutdown()
print("ERRAND", json.dumps(dict(world=WORLD, seed=SEED, label=LABEL, counts=dict(sorted(C.items())))))
