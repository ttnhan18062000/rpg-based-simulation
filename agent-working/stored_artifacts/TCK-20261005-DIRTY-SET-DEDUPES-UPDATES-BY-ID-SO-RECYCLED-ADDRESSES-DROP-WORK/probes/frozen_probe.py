"""Scope 4: does executor.get_frozen ever return a STALE frozen view because id(obj) was reused?
Before each LocalSequentialExecutor.execute call, for each cached key whose cached id equals id(current attr),
compare the cached frozen view with a fresh deep_freeze of the current attr (repr equality).
usage: frozen_probe.py <root> <ticks> <world>
"""
import sys

ROOT, TICKS, WORLD = sys.argv[1], int(sys.argv[2]), sys.argv[3]
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.immutability import deep_freeze
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

KEYS = {"regions": "regions", "nodes": "resource_nodes", "buildings": "buildings", "groups": "groups",
        "corpses": "corpses", "ground_items": "ground_items", "terrain": "terrain"}
C = {"calls": 0, "id_matches": 0, "stale": 0, "per_key_stale": {}}
_orig = LocalSequentialExecutor.execute


def execute(self, work_items, state, rng, profile):
    cache = getattr(self, "_freeze_cache", {})
    C["calls"] += 1
    for key, attr in KEYS.items():
        ent = cache.get(key)
        cur = getattr(state, attr)
        if ent and ent[0] == id(cur):
            C["id_matches"] += 1
            if repr(deep_freeze(cur)) != repr(ent[1]):
                C["stale"] += 1
                C["per_key_stale"][key] = C["per_key_stale"].get(key, 0) + 1
    return _orig(self, work_items, state, rng, profile)


LocalSequentialExecutor.execute = execute
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
print("FROZEN-PROBE", WORLD, TICKS, C)
