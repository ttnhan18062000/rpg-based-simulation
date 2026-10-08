"""Who removes HP from the named entities. usage: hpsrc.py <root> <world> <ticks> <seed> <ids>"""
import collections, json, sys, traceback
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); IDS = {int(x) for x in sys.argv[5].split(",")}
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.core.updates import EntityUpdate
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
LOG = collections.defaultdict(list); _i = EntityUpdate.__init__
def init(self, *a, **kw):
    _i(self, *a, **kw)
    c = self.combat
    if self.entity_id in IDS and c is not None and getattr(c, "hp_delta", 0) < 0:
        site = "?"
        for fs in reversed(traceback.extract_stack(limit=14)[:-1]):
            if "/src/" in fs.filename and not fs.filename.endswith("core/updates.py"):
                site = f"{fs.filename.split('/src/')[-1]}:{fs.lineno}:{fs.name}"; break
        LOG[self.entity_id].append((k.state.tick, c.hp_delta, getattr(c, "attacker_id", None), site))
EntityUpdate.__init__ = init
try:
    for _ in range(TICKS): k.tick_once()
finally:
    k.shutdown()
for eid in sorted(IDS):
    print("HPSRC", eid, "events", len(LOG[eid]))
    agg = collections.Counter((s, a) for t, d, a, s in LOG[eid])
    for (s, a), n in agg.most_common(8): print("   ", n, "attacker", a, s)
    print("   last 8:", LOG[eid][-8:])
