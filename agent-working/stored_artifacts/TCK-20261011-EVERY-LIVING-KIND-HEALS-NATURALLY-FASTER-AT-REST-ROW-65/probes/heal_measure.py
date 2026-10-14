import json, sys, time, os
from collections import Counter
tree, world, seed, ticks, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
os.chdir(tree); sys.path.insert(0, tree)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world
def sp(e): return (e.identity.properties or {}).get("species_id")
state = compile_world(world, seed)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(seed),
           flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
prev_t = {}; starts = Counter(); samples = 0; hp_ratio_sum = 0.0; wounded_sum = 0.0; wounded_n = 0; alive_n = 0; t0 = time.time()
for i in range(ticks):
    k.tick_once(); s = k._state
    for e in s.entities.values():
        if e.combat.alive and e.task.payload.get("action") == "ATTACK":
            t = e.task.payload.get("target_id")
            if prev_t.get(e.id) != t: starts[sp(e)] += 1
            prev_t[e.id] = t
        else: prev_t.pop(e.id, None)
    if (i + 1) % 100 == 0:
        for e in s.entities.values():
            if e.combat.alive and e.combat.max_hp > 0:
                r = e.combat.hp / e.combat.max_hp; alive_n += 1; hp_ratio_sum += r
                if r < 1.0: wounded_n += 1; wounded_sum += r
s = k._state
deaths = {}
for e in s.entities.values():
    if not e.combat.alive:
        cause = e.lifecycle.death_reason or (e.lifecycle.passive_death_cause.value if getattr(e.lifecycle, "passive_death_cause", None) else "UNKNOWN")
        deaths.setdefault(str(sp(e)), Counter())[str(cause)] += 1
alive = Counter(sp(e) for e in s.entities.values() if e.combat.alive)
json.dump({"world": world, "seed": seed, "wall_s": time.time()-t0, "alive": dict(alive), "deaths": {a: dict(c) for a, c in deaths.items()},
           "attack_starts": dict(starts), "mean_hp_ratio": hp_ratio_sum/max(1,alive_n), "wounded_samples": wounded_n, "alive_samples": alive_n,
           "mean_wounded_hp_ratio": wounded_sum/max(1,wounded_n)}, open(out, "w"))
k.shutdown()
