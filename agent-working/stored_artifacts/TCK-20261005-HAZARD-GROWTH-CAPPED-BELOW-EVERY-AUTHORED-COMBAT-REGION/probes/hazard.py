"""hazard.py <world> <ticks> <out.jsonl>: per 500 ticks, every region's hazard and trauma, alive population, and the death-cause mix so far.
Writes each checkpoint as it goes (output exists before any post-processing). Run from a worktree root: PYTHONPATH=. python hazard.py ..."""
import sys, json, collections
from tests.helpers.scenario import compile_world, DEFAULT_SEED, DEFAULT_FLAGS
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
world, ticks, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
st = compile_world(world, DEFAULT_SEED)
k = Kernel(profile=PROD_SMALL, state=st, rng=DeterministicRNG(DEFAULT_SEED), flags=dict(DEFAULT_FLAGS))
authored = {r: g.hazard_level for r, g in st.regions.items()}
alive_prev = {e.id: e.combat.alive for e in st.entities.values()}
causes = collections.Counter(); first_growth = {}
f = open(out, "w")
f.write(json.dumps({"authored_hazard": authored}) + "\n")
for t in range(ticks):
    k.tick_once(); s = k._state
    for e in s.entities.values():
        if alive_prev.get(e.id, True) and not e.combat.alive:
            causes[str(getattr(e.lifecycle, "death_reason", None))] += 1
        alive_prev[e.id] = e.combat.alive
    for r, g in s.regions.items():
        if g.hazard_level > authored[r] + 1e-9 and r not in first_growth: first_growth[r] = t
    if (t + 1) % 500 == 0:
        f.write(json.dumps({"tick": t + 1, "hazard": {r: round(g.hazard_level, 3) for r, g in s.regions.items()},
                            "trauma": {r: round(g.trauma_score, 2) for r, g in s.regions.items()},
                            "alive": sum(1 for e in s.entities.values() if e.combat.alive),
                            "deaths": sum(causes.values()), "causes": dict(causes), "first_growth": first_growth}) + "\n"); f.flush()
k.shutdown()
f.write(json.dumps({"final": True, "ticks": ticks, "first_growth": first_growth}) + "\n"); f.close()
